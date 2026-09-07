"""Factual review must preserve the independent rights and coverage boundaries."""

import copy
import hashlib
import json
import runpy
import sys
from pathlib import Path

import pytest

from archive_govt_nz.foi_candidate_assessment import (
    assess_candidates,
    assessment_files,
    main,
)

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"
SEEDS = ROOT / "config/foi"
ROLLOUT = TRACK / "country-rollout-20260831.json"
OBSERVATIONS = TRACK / "factual-observations-al-bh-20260907.json"


def test_complete_cohort_and_retained_evidence_accounting() -> None:
    """Two sites have bounded access evidence; 223 only retain discovery claims."""
    report = assess_candidates(SEEDS, ROLLOUT, TRACK, OBSERVATIONS)
    assert report["summary"] == {
        "candidates": 225,
        "retained_receipts_assessed": 225,
        "bounded_factual_reviews": 2,
        "anonymous_html_endpoints_observed": 2,
        "request_response_register_landings_observed": 1,
        "general_data_catalogues_observed": 1,
        "candidates_without_transport_observations": 223,
        "capture_adapters_verified": 0,
        "publication_credit_granted": 0,
    }
    rows = {r["source_id"]: r for r in report["sources"]}
    al, bh, kw = (
        rows[key]
        for key in ("al-idp-transparency", "bh-government-open-data", "kw-open-data")
    )
    assert al["factual_review"] == "bounded_observations_assessed"
    assert al["foi_scope"] == "request_response_register_landing_page_observed"
    assert bh["foi_scope"] == "not_established"
    assert bh["interface"] == "general_data_catalogue_observed"
    assert bh["robots"]["linked_api_allowed"] is False
    assert al["robots"]["crawl_delay_seconds"] is None
    assert kw["source_access"] == "not_observed"
    assert kw["factual_review"] == "retained_evidence_assessed"
    assert all(row["redistribution"] == "not_assessed" for row in rows.values())
    assert all(row["publication_approved"] is False for row in rows.values())
    assert all(row["request_denominator"] is None for row in rows.values())
    assert all(row["country_complete"] is False for row in rows.values())


@pytest.mark.parametrize(
    "mode", ["pin", "receipt", "entity", "duplicate", "omitted", "cross_host", "unsafe"]
)
def test_invalid_observation_binding_is_rejected(tmp_path: Path, mode: str) -> None:
    """A factual observation cannot be substituted or silently dropped."""
    observation = json.loads(OBSERVATIONS.read_bytes())
    source = observation["sources"][0]
    if mode == "pin":
        observation["rollout_sha256"] = "0" * 64
    elif mode == "receipt":
        source["retained_receipt_sha256"] = "0" * 64
    elif mode == "entity":
        source["entity_id"] = "NZ"
    elif mode == "duplicate":
        observation["sources"].append(copy.deepcopy(source))
    elif mode == "omitted":
        observation["sources"].pop()
    elif mode == "cross_host":
        source["pages"][0]["final_url"] = "https://example.org/"
    else:
        source["pages"][0]["requested_url"] = "https://127.0.0.1/"
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation), encoding="utf-8")
    with pytest.raises(ValueError, match=r"observation|unsafe"):
        assess_candidates(SEEDS, ROLLOUT, TRACK, path)


def test_report_rendering_is_deterministic() -> None:
    """Both report forms have one source of truth and unknown denominators."""
    report = assess_candidates(SEEDS, ROLLOUT, TRACK, OBSERVATIONS)
    files = assessment_files(report)
    assert (
        json.loads(files["candidate-assessment.json"])["summary"] == report["summary"]
    )
    assert files == assessment_files(
        assess_candidates(SEEDS, ROLLOUT, TRACK, OBSERVATIONS)
    )
    assert b"human approval" not in files["candidate-assessment.md"]
    for name, payload in files.items():
        assert (TRACK / name).read_bytes() == payload


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", True),
        ("status", 600),
        ("body_bytes", -1),
        ("body_bytes", 2_000_001),
        ("body_sha256", "bad"),
        ("body_retained", True),
        ("observed_at", "2026-09-07"),
        ("authentication", "credentialed"),
        ("method", "POST"),
        ("title", "x" * 201),
        ("source_id", "different"),
        ("redirect_chain", []),
        ("role", "wrong"),
    ],
)
def test_transport_contract_rejects_malformed_values(
    tmp_path: Path, field: str, value: object
) -> None:
    """Only bounded dated anonymous observations may support factual findings."""
    observation = json.loads(OBSERVATIONS.read_bytes())
    observation["sources"][0]["pages"][0][field] = value
    path = tmp_path / "observations.json"
    path.write_text(json.dumps(observation), encoding="utf-8")
    with pytest.raises(ValueError, match="observation"):
        assess_candidates(SEEDS, ROLLOUT, TRACK, path)


@pytest.mark.parametrize(
    "mode", ["forbidden", "empty", "non_html", "no_links", "self_link"]
)
def test_inadequate_page_evidence_does_not_establish_register_scope(
    tmp_path: Path, mode: str
) -> None:
    """HTTP failure, non-HTML, empty bodies and self-links cannot prove a register."""
    observation = json.loads(OBSERVATIONS.read_bytes())
    page = observation["sources"][0]["pages"][1]
    if mode == "forbidden":
        page["status"] = page["redirect_chain"][-1]["status"] = 403
    elif mode == "empty":
        page["body_bytes"] = 0
    elif mode == "non_html":
        page["media_type"] = "application/pdf"
    elif mode == "no_links":
        page["selected_links"] = []
    else:
        page["selected_links"] = [{"url": page["final_url"], "label": "2026"}]
    path = tmp_path / "observations.json"
    path.write_text(json.dumps(observation), encoding="utf-8")
    row = next(
        r
        for r in assess_candidates(SEEDS, ROLLOUT, TRACK, path)["sources"]
        if r["source_id"] == "al-idp-transparency"
    )
    assert row["source_id"] == "al-idp-transparency"
    assert row["foi_scope"] == "not_established"
    assert row["publication_approved"] is False


@pytest.mark.parametrize(
    ("text", "status", "expected"),
    [
        ("User-agent: *\nDisallow: /api/\n", 200, False),
        ("User-agent: *\nDisallow:\nCrawl-delay: 5\n", 200, True),
        ("User-agent: *\n Disallow: /*api*\n", 200, False),
        ("", 503, None),
    ],
)
def test_robots_policy_is_independent_and_conservative(
    tmp_path: Path, text: str, status: int, expected: object
) -> None:
    """Default-agent restrictions and missing responses cannot grant access."""
    observation = json.loads(OBSERVATIONS.read_bytes())
    robots = observation["sources"][1]["robots"]
    robots.update(
        text=text, status=status, body_sha256=hashlib.sha256(text.encode()).hexdigest()
    )
    path = tmp_path / "observations.json"
    path.write_text(json.dumps(observation), encoding="utf-8")
    row = next(
        r
        for r in assess_candidates(SEEDS, ROLLOUT, TRACK, path)["sources"]
        if r["source_id"] == "bh-government-open-data"
    )
    assert row["robots"]["linked_api_allowed"] is expected
    assert row["source_access"] == "anonymous_html_observed"
    assert row["schedule_active"] is False
    if "Crawl-delay" in text:
        assert row["robots"]["crawl_delay_seconds"] == 5


@pytest.mark.parametrize("rule", ["Disallow: /*api*", "Disallow: /api/$"])
def test_legacy_parser_cannot_grant_complex_rule_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rule: str
) -> None:
    """Legacy prefix-only parsing cannot override conservative admission."""
    monkeypatch.setattr(
        "archive_govt_nz.foi_candidate_assessment.RobotFileParser.can_fetch",
        lambda *_args: True,
    )
    test_robots_policy_is_independent_and_conservative(
        tmp_path, f"User-agent: *\n{rule}\n", 200, expected=False
    )


def test_restrictions_survive_factual_review(monkeypatch: pytest.MonkeyPatch) -> None:
    """A retained restriction cannot disappear through favourable access claims."""
    read = Path.read_bytes

    def restricted(path: Path) -> bytes:
        payload = read(path)
        if path.name == "kw-open-data-discovery-20260905.json":
            receipt = json.loads(payload)
            receipt.update(
                disposition="restricted",
                rights_decision="disallowed",
                privacy_decision="restricted",
                access_decision="unknown",
                capture_decision="disallowed",
                retention_decision="restricted",
                public_metadata_observed=True,
                publication_approved=True,
            )
            return json.dumps(receipt).encode()
        return payload

    monkeypatch.setattr(Path, "read_bytes", restricted)
    row = next(
        r
        for r in assess_candidates(SEEDS, ROLLOUT, TRACK, OBSERVATIONS)["sources"]
        if r["source_id"] == "kw-open-data"
    )
    assert row["declared_disposition"] == "restricted"
    assert row["redistribution"] == "disallowed"
    assert row["privacy"] == "restricted"
    assert row["capture_rights"] == "disallowed"
    assert row["retention"] == "restricted"
    assert row["access_rights"] == "unknown"
    assert row["source_access"] == "not_observed"
    assert row["publication_approved"] is False

    assert row["source_url"] is None


@pytest.mark.parametrize("output_format", ["json", "md"])
def test_cli_reports_without_network_or_mutation(
    capsys: pytest.CaptureFixture[str], output_format: str
) -> None:
    """The offline command renders exactly the library result."""
    assert (
        main(
            [
                "--seeds",
                str(SEEDS),
                "--rollout",
                str(ROLLOUT),
                "--evidence-dir",
                str(TRACK),
                "--observations",
                str(OBSERVATIONS),
                "--format",
                output_format,
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out.encode()
        == assessment_files(assess_candidates(SEEDS, ROLLOUT, TRACK, OBSERVATIONS))[
            f"candidate-assessment.{output_format}"
        ]
    )


def test_module_failure_is_redacted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unavailable observations produce exit 2 without input details or a report."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "foi_candidate_assessment",
            "--seeds",
            str(SEEDS),
            "--rollout",
            str(ROLLOUT),
            "--evidence-dir",
            str(TRACK),
            "--observations",
            str(tmp_path / "absent"),
        ],
    )
    with pytest.raises(SystemExit) as result:
        runpy.run_path(
            str(ROOT / "src/archive_govt_nz/foi_candidate_assessment.py"),
            run_name="__main__",
        )
    assert result.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err
        == "FOI factual assessment rejected invalid or unavailable inputs.\n"
    )
