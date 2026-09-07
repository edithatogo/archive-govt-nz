"""Complete-cohort integrity and policy-preservation regression tests."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from archive_govt_nz.foi_candidate_cohort import (
    assess_cohort,
    disposition,
    report_files,
)

TRACK = (
    Path(__file__).parents[1] / "conductor/tracks/global_foi_public_archive_20260830"
)
BASE = TRACK / "candidate-assessment.json"
OBS = TRACK / "candidate-observations-remaining-20260907.json"


def test_complete_report_is_reproducible_and_preserves_policy() -> None:
    """Every source is accounted for without rewriting prior evidence or rights."""
    report = assess_cohort(BASE, OBS)
    original = json.loads(BASE.read_bytes())["sources"]
    assert report["summary"]["new_observation_count"] == 223
    assert report["summary"]["candidate_count"] == 225
    assert report["summary"]["prior_observations_preserved"] == 2
    for row, old in zip(report["sources"], original, strict=True):
        if old["factual_review"] == "bounded_observations_assessed":
            assert row == old
        for key in (
            "publication_approved",
            "schedule_active",
            "privacy",
            "retention",
            "redistribution",
            "capture_rights",
            "access_rights",
            "country_complete",
            "request_denominator",
            "declared_disposition",
            "capture_adapter_verified",
        ):
            assert row[key] == old[key]
    for name, contents in report_files(report).items():
        assert (TRACK / name).read_text() == contents


@pytest.mark.parametrize(
    "mutation",
    [
        "omit",
        "duplicate",
        "extra",
        "identity",
        "digest",
        "date",
        "bytes",
        "hash",
        "page",
        "links",
    ],
)
def test_tampering_fails_closed(tmp_path: Path, mutation: str) -> None:
    """Incomplete cohorts and unbound transport metadata cannot earn assessment."""
    value = json.loads(OBS.read_bytes())
    row = value["sources"][0]
    if mutation == "omit":
        value["sources"].pop()
    elif mutation == "duplicate":
        value["sources"].append(deepcopy(row))
    elif mutation == "extra":
        row["source_id"] = "invented"
    elif mutation == "identity":
        row["entity_id"] = "ZZ"
    elif mutation == "digest":
        value["baseline_sha256"] = "0" * 64
    elif mutation == "date":
        row["observed_at"] = "2030-01-01T00:00:00Z"
    elif mutation == "bytes":
        row["robots"][0]["body_bytes"] = 999999999
    elif mutation == "hash":
        row["robots"][0]["body_sha256"] = None
    elif mutation == "page":
        row["homepage"]["body_sha256"] = "0" * 64
    else:
        row["homepage"]["links"] = [
            {"url": "https://localhost/", "label": "FOI", "kind": "foi"}
        ]
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(value))
    with pytest.raises(
        ValueError,
        match=r"cohort|binding|digest|date|byte|observation|trace|navigation",
    ):
        assess_cohort(BASE, path)


def test_http_200_challenge_is_not_content_access() -> None:
    """HTTP transport success cannot disguise an interstitial."""
    assert (
        disposition(
            {"outcome": "observed", "title": "Challenge Validation", "links": []}
        )
        == "access_unverified"
    )
    assert disposition(None) == "access_unverified"


def test_collector_bytes_match_retained_acquisition_identity() -> None:
    """The acquisition implementation is retained, not only an unverifiable digest."""
    collector = Path(__file__).parents[1] / "src/archive_govt_nz/foi_candidate_probe.py"
    assert (
        hashlib.sha256(collector.read_bytes()).hexdigest()
        == json.loads(OBS.read_bytes())["collector_sha256"]
    )
