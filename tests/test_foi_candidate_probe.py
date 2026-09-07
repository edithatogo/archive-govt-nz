"""Bounded metadata probes preserve failures and never infer raw eligibility."""

import asyncio
import hashlib
import json
import socket
from collections.abc import AsyncIterator  # noqa: TC003
from pathlib import Path
from types import SimpleNamespace
from urllib.robotparser import RobotFileParser

import httpx
import pytest

from archive_govt_nz import foi_candidate_probe as probe
from archive_govt_nz.foi_candidate_probe import (
    Bounds,
    classify_metadata,
    collect_candidates,
)

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"


def test_obvious_catalogue_disposition_is_scoped_to_observed_interface() -> None:
    """A general dataset catalogue need not wait in a human FOI-review queue."""
    page = {
        "outcome": "observed",
        "title": "National Open Data Portal",
        "links": [
            {
                "url": "https://example.org/datasets",
                "label": "Datasets",
                "kind": "catalogue",
            }
        ],
    }
    assert classify_metadata(page) == "out_of_scope_for_foi_capture"
    page["links"].append(
        {"url": "https://example.org/foi", "label": "FOI", "kind": "foi"}
    )
    assert classify_metadata(page) == "foi_metadata_lead"
    page["outcome"] = "http_error"
    assert classify_metadata(page) == "access_unverified"


def test_every_remaining_source_has_one_dated_outcome() -> None:
    """Even failed probes stay in the cohort denominator without retries."""
    baseline = json.loads((TRACK / "candidate-assessment.json").read_bytes())
    rows = [
        r
        for r in baseline["sources"]
        if r["factual_review"] == "retained_evidence_assessed"
    ]
    calls = []

    async def fake_get(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        assert limit > 0
        assert bounds.workers <= 8
        calls.append(url)
        return {
            "url": url,
            "status": 403,
            "outcome": "http_error",
            "observed_at": "2026-09-07T03:00:00Z",
            "body_bytes": 0,
            "body_sha256": None,
            "media_type": "text/html",
        }, b""

    report = asyncio.run(collect_candidates(rows, get=fake_get))
    assert len(report) == len(rows) == 223
    assert len(calls) == 223
    assert all(r["outcome"] == "robots_unverified" for r in report)
    assert all(r["homepage"] is None for r in report)
    assert {r["source_id"] for r in report} == {r["source_id"] for r in rows}


@pytest.mark.parametrize(
    "kwargs", [{"workers": 0}, {"request_seconds": 0}, {"max_bytes": 0}]
)
def test_invalid_bounds_fail_before_requests(kwargs: dict) -> None:
    """Invalid bounds cannot accidentally mean unbounded collection."""
    with pytest.raises(ValueError, match="bounds"):
        Bounds(**kwargs)


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1/",
        "https://localhost/",
        "https://example.org/?secret=x",
        "http://example.org/",
        "https://example.org:bad/",
    ],
)
def test_unsafe_urls_never_reach_dns(url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shared syntactic guard runs before any network side effect."""

    async def forbidden(host: str) -> str:
        pytest.fail(f"unexpected DNS lookup: {host}")

    monkeypatch.setattr(probe, "public_address", forbidden)
    record, body = asyncio.run(probe.safe_get(url, 100, Bounds()))
    assert record["outcome"] == "unsafe_url"
    assert record["url"] is None
    assert body == b""


def test_private_dns_answers_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A public-looking name cannot resolve to an internal host."""

    async def check() -> None:
        async def answers(*args: object, **kwargs: object) -> list:
            assert args
            assert kwargs
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]

        monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", answers)
        with pytest.raises(ValueError, match="non_public_dns"):
            await probe.public_address("example.org")

    asyncio.run(check())


def test_validated_address_is_pinned_with_original_sni(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connection DNS cannot be rebound after validation, while TLS keeps its host."""
    original = httpx.AsyncClient
    seen = []

    async def resolve(host: str) -> str:
        assert host == "example.org"
        return "93.184.215.14"

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)

        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self) -> AsyncIterator[bytes]:
                yield b"<title>Test</title>"

        return httpx.Response(
            200, headers={"Content-Type": "text/html"}, stream=Stream()
        )

    def client(**kwargs: object) -> httpx.AsyncClient:
        assert kwargs == {"trust_env": False, "follow_redirects": False}
        return original(
            transport=httpx.MockTransport(handle),
            trust_env=False,
            follow_redirects=False,
        )

    monkeypatch.setattr(probe, "public_address", resolve)
    monkeypatch.setattr(probe.httpx, "AsyncClient", client)
    record, body = asyncio.run(probe.safe_get("https://example.org/", 100, Bounds()))
    assert seen[0].url.host == "93.184.215.14"
    assert seen[0].headers["host"] == "example.org"
    assert seen[0].extensions["sni_hostname"] == "example.org"
    assert record["outcome"] == "observed"
    assert record["body_sha256"] == hashlib.sha256(body).hexdigest()


def test_robots_restriction_stops_page_request() -> None:
    """Source metadata collection cannot bypass a discovered robots restriction."""
    rows = [
        {
            "source_id": "s",
            "entity_id": "NZ",
            "source_url": "https://example.org/",
            "retained_receipt_sha256": "0" * 64,
        }
    ]
    calls = []

    async def get(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        assert limit == probe.ROBOTS_BYTES
        assert bounds.workers > 0
        calls.append(url)
        return {
            "url": url,
            "status": 200,
            "outcome": "observed",
        }, b"User-agent: *\nDisallow: /\n"

    results = asyncio.run(collect_candidates(rows, get=get))
    assert results[0]["outcome"] == "robots_disallowed"
    assert calls == ["https://example.org/robots.txt"]


@pytest.mark.parametrize(
    "text",
    [
        "User-agent: *\nDisallow: /private/",
        "User-agent: *\nAllow: /public/\nDisallow: /private/",
        "# Disallow: /*$\nUser-agent: *\nDisallow: /private/ # *$",
        "User-agent: *\nSitemap: https://example.org/*$",
        "User-agent: *\nDisallow:\nCrawl-delay: 5",
    ],
)
def test_simple_robots_rules_remain_supported(text: str) -> None:
    """Do not confuse the default agent or comments with complex path rules."""
    assert probe.robots_path_rules_supported(text)


def test_other_agent_complex_path_also_fails_closed() -> None:
    """Avoid relying on runtime-specific group selection to bypass the guard."""
    assert not probe.robots_path_rules_supported(
        "User-agent: other\nDisallow: /private/*\n\nUser-agent: *\nAllow: /\n"
    )


@pytest.mark.parametrize(
    ("headers", "payload", "expected"),
    [
        ({"content-length": "101"}, b"", "byte_limit"),
        ({}, b"x" * 101, "byte_limit"),
        ({"content-encoding": "gzip"}, b"", "unsupported_content_encoding"),
        ({"content-type": "application/pdf"}, b"", "non_text_metadata"),
        ({}, b"abc", "observed"),
    ],
)
def test_streaming_byte_and_encoding_limits(
    headers: dict, payload: bytes, expected: str
) -> None:
    """Reject oversized and compressed inputs without retaining partial bodies."""

    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield payload

    response = httpx.Response(
        200, headers={"content-type": "text/html", **headers}, stream=Stream()
    )
    record = {"received_bytes": 0, "body_bytes": 0, "body_sha256": None}
    result, body = asyncio.run(probe._read_response(response, record, 100))  # noqa: SLF001
    assert result["outcome"] == expected
    assert len(body) <= 100
    if expected != "observed":
        assert body == b""
        assert result["body_sha256"] is None


def test_deadline_keeps_all_candidates_and_partial_traces() -> None:
    """A slow origin cannot erase a candidate or monopolize the cohort."""
    rows = [
        {
            "source_id": str(i),
            "entity_id": "NZ",
            "source_url": f"https://example{i}.org/",
            "retained_receipt_sha256": "0" * 64,
        }
        for i in range(12)
    ]
    active = peak = 0

    async def slow(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        nonlocal active, peak
        assert url
        assert limit
        assert bounds
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(10)
        finally:
            active -= 1
        return {}, b""

    result = asyncio.run(
        collect_candidates(
            rows,
            Bounds(
                workers=2, source_seconds=0.01, total_seconds=0.025, origin_interval=0
            ),
            get=slow,
        )
    )
    assert len(result) == 12
    assert peak <= 2
    assert {row["outcome"] for row in result} <= {"source_timeout", "cohort_deadline"}
    assert all(row["finished_at"] >= row["observed_at"] for row in result)


def test_cross_site_redirect_is_not_requested() -> None:
    """Do not transfer robots policy or source identity to another website."""
    calls = []

    async def redirect(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        calls.append(url)
        assert limit
        assert bounds
        return {
            "url": url,
            "status": 302,
            "outcome": "redirect",
            "redirect_url": "https://elsewhere.org/",
        }, b""

    row = {
        "source_id": "s",
        "entity_id": "NZ",
        "source_url": "https://example.org/",
        "retained_receipt_sha256": "0" * 64,
    }
    result = asyncio.run(collect_candidates([row], get=redirect))
    assert len(calls) == 1
    assert result[0]["robots"][0]["outcome"] == "cross_site_redirect_not_followed"
    assert result[0]["homepage"] is None


def test_metadata_drops_arbitrary_personal_text_and_unsafe_links() -> None:
    """Only bounded title and known navigation labels survive HTML parsing."""
    parser = probe.Metadata("https://example.org/")
    parser.feed(
        "<title>Portal</title><p>Personal correspondence SECRET</p>"
        '<a href="/person">A private name</a><a href="http://localhost/">FOI</a>'
        '<a href="/dataset?token=SECRET">Datasets</a><a href="/foi">FOI</a>'
    )
    assert parser.title == "Portal"
    assert parser.links == [
        {"url": "https://example.org/foi", "label": "FOI", "kind": "foi"}
    ]


@pytest.mark.parametrize(("crawl_delay", "interval"), [(5, 1), (1, 5)])
def test_every_redirect_hop_respects_shared_origin_crawl_delay(
    monkeypatch: pytest.MonkeyPatch, crawl_delay: int, interval: int
) -> None:
    """Pacing applies inside the shared origin lock, not once before a chain."""

    async def check() -> None:
        clock = [100.0]
        starts = []

        async def sleep(seconds: float) -> None:
            clock[0] += seconds

        async def get(url: str, cap: int, bounds: Bounds) -> tuple[dict, bytes]:
            assert url.startswith("https://")
            assert cap
            assert bounds
            starts.append(clock[0])
            clock[0] += 0.2
            if len(starts) <= 2:
                return {
                    "outcome": "redirect",
                    "redirect_url": f"https://www.example.org/hop{len(starts)}",
                }, b""
            return {"outcome": "observed"}, b"ok"

        collector = probe._Collector(Bounds(origin_interval=interval), get)  # noqa: SLF001
        monkeypatch.setattr(collector, "loop", SimpleNamespace(time=lambda: clock[0]))
        collector.last["example.org"] = clock[0]
        policy = RobotFileParser()
        policy.parse(["User-agent: *", f"Crawl-delay: {crawl_delay}"])
        monkeypatch.setattr(probe.asyncio, "sleep", sleep)
        chain = []
        await collector.follow("https://example.org/start", 100, chain, policy)
        # Another request without its own policy must respect the known origin delay.
        await collector.follow("https://example.org/robots.txt", 100, [])
        delay = max(crawl_delay, interval)
        assert starts == [100 + delay * i for i in range(1, 5)]

    asyncio.run(check())


@pytest.mark.parametrize(
    "name", ["request_seconds", "source_seconds", "total_seconds", "origin_interval"]
)
@pytest.mark.parametrize(
    "value", [float("inf"), float("-inf"), float("nan"), True, False, "10", None]
)
def test_time_budgets_reject_nonfinite_or_non_numeric(name: str, value: object) -> None:
    """A duration cannot disable timeout/pacing through nonfinite or coerced values."""
    with pytest.raises(ValueError, match="invalid_probe_bounds"):
        Bounds(**{name: value})  # type: ignore[arg-type]  # Deliberately invalid input.


@pytest.mark.parametrize("name", ["workers", "max_bytes", "max_redirects"])
@pytest.mark.parametrize(
    "value", [True, False, 1.5, float("inf"), float("nan"), "1", None]
)
def test_count_budgets_require_real_integers(name: str, value: object) -> None:
    """Booleans and fractional/coerced counts are not meaningful resource budgets."""
    with pytest.raises(ValueError, match="invalid_probe_bounds"):
        Bounds(**{name: value})  # type: ignore[arg-type]  # Deliberately invalid input.


@pytest.mark.parametrize(
    "kwargs", [{"max_bytes": 1000001}, {"max_redirects": 4}, {"workers": 9}]
)
def test_count_budgets_cannot_expand_hard_caps(kwargs: dict) -> None:
    """Configured cohorts cannot silently exceed the declared hard count caps."""
    with pytest.raises(ValueError, match="invalid_probe_bounds"):
        Bounds(**kwargs)


@pytest.mark.parametrize(
    "rule",
    [
        "Disallow: /private/*",
        "Disallow: /*.pdf$",
        "Allow: /public/*",
        "Disallow: /end$",
        "  dIsAlLoW: /x%2A",
        "Allow: /x%24",
        "Disallow: /elsewhere/* # unrelated path",
    ],
)
def test_complex_robots_rules_fail_closed_even_with_legacy_allow(
    monkeypatch: pytest.MonkeyPatch, rule: str
) -> None:
    """A permissive old parser cannot admit any page when rule semantics differ."""
    calls = []
    parser_calls = []

    def legacy_allow(*args: object) -> bool:
        parser_calls.append(args)
        return True

    async def get(url: str, limit: int, bounds: Bounds) -> tuple[dict, bytes]:
        calls.append(url)
        assert limit
        assert bounds
        body = ("User-agent: *\n" + rule + "\n").encode()
        return {
            "url": url,
            "status": 200,
            "outcome": "observed",
            "media_type": "text/plain",
        }, body

    monkeypatch.setattr(probe.RobotFileParser, "can_fetch", legacy_allow)
    row = {
        "source_id": "s",
        "entity_id": "NZ",
        "source_url": "https://example.org/",
        "retained_receipt_sha256": "0" * 64,
    }
    result = asyncio.run(collect_candidates([row], Bounds(origin_interval=0), get=get))
    assert result[0]["outcome"] == "robots_unsupported_rules"
    assert result[0]["homepage"] is None
    assert result[0]["robots_policy"]["allowed"] is None
    assert parser_calls == []
    assert calls == ["https://example.org/robots.txt"]
