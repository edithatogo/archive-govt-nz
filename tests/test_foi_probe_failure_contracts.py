"""Offline negative paths retain bounded failures instead of successful access."""

import asyncio
import hashlib
import json
import runpy
import socket
import sys
from pathlib import Path

import httpx
import pytest

from archive_govt_nz import foi_candidate_probe as probe


def candidate() -> dict:
    """Return a synthetic candidate without acquisition authority."""
    return {
        "source_id": "synthetic",
        "entity_id": "NZ",
        "source_url": "https://example.org/",
        "retained_receipt_sha256": "0" * 64,
    }


@pytest.mark.parametrize(
    ("error", "outcome"),
    [
        (TimeoutError(), "timeout"),
        (httpx.ReadTimeout("synthetic"), "timeout"),
        (socket.gaierror(), "dns_failure"),
        (httpx.ConnectError("synthetic"), "transport_or_tls_failure"),
        (ValueError(), "dns_or_header_rejected"),
    ],
)
def test_request_failures_keep_empty_body(
    monkeypatch: pytest.MonkeyPatch, error: Exception, outcome: str
) -> None:
    """No failure becomes an observed body or leaks exception diagnostics."""

    async def reject(host: str) -> str:
        assert host == "example.org"
        raise error

    monkeypatch.setattr(probe, "public_address", reject)
    record, body = asyncio.run(
        probe.safe_get("https://example.org/", 100, probe.Bounds())
    )
    assert record["outcome"] == outcome
    assert record["body_sha256"] is None
    assert record["received_bytes"] == record["body_bytes"] == 0
    assert body == b""
    assert "synthetic" not in json.dumps(record)


def test_public_dns_selection_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    """A validated mixed public answer set pins the smallest IPv4 address."""

    async def check() -> None:
        async def answers(*args: object, **kwargs: object) -> list:
            assert args
            assert kwargs
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))
                for address in ["2606:4700:4700::1111", "8.8.8.8", "1.1.1.1"]
            ]

        monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", answers)
        assert await probe.public_address("example.org") == "1.1.1.1"

    asyncio.run(check())


@pytest.mark.parametrize(
    ("status", "location", "outcome", "target"),
    [
        (302, "/next", "redirect", "https://example.org/next"),
        (302, "http://example.org/next", "unsafe_redirect", None),
        (302, "", "unsafe_redirect", None),
        (404, "", "http_error", None),
    ],
)
def test_response_status_never_reads_body(
    status: int, location: str, outcome: str, target: str | None
) -> None:
    """Redirect and error records do not retain even a supplied response body."""
    response = httpx.Response(
        status, headers={"location": location}, content=b"private"
    )
    record = {"url": "https://example.org/", "received_bytes": 0}
    result, body = asyncio.run(probe._read_response(response, record, 100))  # noqa: SLF001
    assert result["outcome"] == outcome
    assert result.get("redirect_url") == target
    assert result["received_bytes"] == 0
    assert body == b""


@pytest.mark.parametrize(
    "mode", ["html", "plain", "disallowed", "limit", "parse", "absent"]
)
def test_collection_terminal_contract(mode: str) -> None:
    """Robots and redirect failures remain terminal; only HTML yields metadata."""
    calls = []

    async def get(url: str, cap: int, bounds: probe.Bounds) -> tuple[dict, bytes]:
        assert cap
        assert bounds
        calls.append(url)
        if mode == "parse":
            raise ValueError
        if url.endswith("robots.txt"):
            if mode == "absent":
                return {"url": url, "status": 404, "outcome": "http_error"}, b""
            return {"url": url, "status": 200, "outcome": "observed"}, (
                b"User-agent: *\nDisallow: /private\n"
            )
        if mode in {"limit", "disallowed"}:
            return {
                "url": url,
                "status": 302,
                "outcome": "redirect",
                "redirect_url": "https://example.org/private"
                if mode == "disallowed"
                else "https://example.org/again",
            }, b""
        return {
            "url": url,
            "status": 200,
            "outcome": "observed",
            "media_type": "text/html" if mode in {"html", "absent"} else "text/plain",
        }, b'<title>Public portal</title><a href="/foi">FOI</a>'

    result = asyncio.run(
        probe.collect_candidates(
            [candidate()], probe.Bounds(origin_interval=0), get=get
        )
    )[0]
    expected = {
        "html": "observed",
        "plain": "non_html_metadata",
        "disallowed": "robots_disallowed",
        "limit": "redirect_limit",
        "parse": "metadata_parse_rejected",
        "absent": "observed",
    }[mode]
    assert result["outcome"] == expected
    assert result["finished_at"] >= result["observed_at"]
    if mode in {"html", "absent"}:
        assert result["homepage"]["title"] == "Public portal"
        assert result["homepage"]["links"][0]["kind"] == "foi"
    elif mode == "parse":
        assert result["homepage"] is None
    else:
        assert result["homepage"]["links"] == []
    if mode == "disallowed":
        assert "https://example.org/private" not in calls
        assert result["redirect_chain"][-1]["body_sha256"] is None
    if mode == "limit":
        assert len(calls) == 5  # One robots request, four bounded page hops.


def test_duplicate_candidates_fail_before_io() -> None:
    """Duplicate accounting keys cannot silently collapse the denominator."""
    with pytest.raises(ValueError, match="duplicate_probe_candidate"):
        asyncio.run(probe.collect_candidates([candidate(), candidate()]))


def test_collect_file_binds_exact_input_and_filters_prior_reviews(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The wrapper hashes exact bytes and sends only outstanding candidates."""
    selected = {**candidate(), "factual_review": "retained_evidence_assessed"}
    prior = {
        **candidate(),
        "source_id": "prior",
        "factual_review": "bounded_observations_assessed",
    }
    path = tmp_path / "baseline.json"
    payload = json.dumps({"sources": [selected, prior]}, indent=2).encode()
    path.write_bytes(payload)

    async def collect(rows: list, bounds: probe.Bounds) -> list:
        assert rows == [selected]
        assert bounds == probe.Bounds()
        return [{"source_id": "synthetic", "outcome": "timeout"}]

    monkeypatch.setattr(probe, "collect_candidates", collect)
    result = asyncio.run(probe.collect_file(path))
    assert result["baseline_sha256"] == hashlib.sha256(payload).hexdigest()
    assert (
        result["collector_sha256"]
        == hashlib.sha256(Path(probe.__file__).read_bytes()).hexdigest()
    )
    assert result["sources"] == [{"source_id": "synthetic", "outcome": "timeout"}]
    assert result["scope"] == "metadata_observation_only_no_original_body_retained"
    assert path.read_bytes() == payload


def test_cohort_cli_matches_offline_assessment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The actual entry point emits the same complete offline assessment."""
    track = (
        Path(__file__).parents[1]
        / "conductor/tracks/global_foi_public_archive_20260830"
    )
    expected = json.loads((track / "candidate-assessment-complete.json").read_bytes())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cohort",
            str(track / "candidate-assessment.json"),
            str(track / "candidate-observations-remaining-20260907.json"),
        ],
    )
    runpy.run_path(
        str(Path(probe.__file__).with_name("foi_candidate_cohort.py")),
        run_name="__main__",
    )
    assert json.loads(capsys.readouterr().out) == expected
