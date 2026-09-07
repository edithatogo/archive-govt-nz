"""Source-context census admission and evidence regression tests."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from archive_govt_nz.domains.health_appropriations.source_context_census import (
    Census,
    encode_census,
    validate_evidence,
)

ROOT = Path(__file__).resolve().parents[3]
TRACK = ROOT / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"


def document() -> dict:
    return json.loads((TRACK / "context-census.json").read_text())


def test_retained_census_is_deterministic_and_evidence_bound() -> None:
    census = Census.model_validate(document())
    validate_evidence(census, ROOT)
    assert encode_census(census) == encode_census(
        Census.model_validate_json(encode_census(census))
    )
    assert {row.family for row in census.series} == {
        "cpi",
        "qes",
        "population",
        "gdp",
        "core_crown",
        "total_crown",
    }
    assert all(row.qualification == "unqualified" for row in census.series)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("qualification", "qualified"),
        ("rights", "approved"),
        ("join_policy", ""),
        ("gaps", []),
        ("series_id", ""),
        ("base", ""),
        ("vintage", ""),
        ("unit", ""),
    ],
)
def test_rejects_unsupported_claims_and_empty_context(
    field: str, value: object
) -> None:
    data = document()
    data["series"][0][field] = value
    with pytest.raises(ValidationError):
        Census.model_validate(data)


def test_rejects_duplicate_or_missing_families() -> None:
    data = document()
    data["series"].append(data["series"][0])
    with pytest.raises(ValidationError, match="identity"):
        Census.model_validate(data)
    data = document()
    data["series"] = [row for row in data["series"] if row["family"] != "population"]
    with pytest.raises(ValidationError, match="families"):
        Census.model_validate(data)


@pytest.mark.parametrize("field", ["url", "object_sha256", "observed_at", "source_id"])
def test_source_reference_must_match_retained_census(field: str) -> None:
    data = document()
    data["series"][0]["sources"][0][field] = "changed"
    with pytest.raises((ValueError, ValidationError)):
        validate_evidence(Census.model_validate(data), ROOT)


def test_evidence_hash_drift_is_rejected() -> None:
    data = document()
    data["evidence"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence"):
        validate_evidence(Census.model_validate(data), ROOT)


@pytest.mark.parametrize("path", ["../AGENTS.md", "/etc/passwd", "missing.md"])
def test_evidence_path_escape_or_absence_is_rejected(path: str) -> None:
    data = document()
    data["evidence"][0]["path"] = path
    with pytest.raises(ValueError, match="evidence"):
        validate_evidence(Census.model_validate(data), ROOT)


def test_unknown_evidence_reference_is_rejected() -> None:
    data = document()
    data["series"][0]["evidence"] = ["unknown"]
    with pytest.raises(ValidationError, match="evidence"):
        Census.model_validate(data)


def test_manifest_must_occur_in_cited_evidence() -> None:
    data = document()
    data["series"][0]["retained_manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="manifest"):
        validate_evidence(Census.model_validate(data), ROOT)


def test_duplicate_evidence_and_unpinned_census_are_rejected() -> None:
    data = document()
    data["evidence"].append(data["evidence"][0])
    with pytest.raises(ValidationError, match="duplicate evidence"):
        Census.model_validate(data)
    data = document()
    path = next(
        item["path"]
        for item in data["evidence"]
        if item["path"].endswith("/source-census.json")
    )
    data["evidence"] = [item for item in data["evidence"] if item["path"] != path]
    for row in data["series"]:
        row["evidence"] = [item for item in row["evidence"] if item != path]
    with pytest.raises(ValueError, match="source census evidence missing"):
        validate_evidence(Census.model_validate(data), ROOT)


def test_pinned_selectors_keep_denominator_boundaries() -> None:
    rows = {row.id: row for row in Census.model_validate(document()).series}
    assert rows["cpi-2026q2"].series_id == "CPIQ.SE9A"
    assert rows["qes-2026q2"].series_id == "QEMQ.SASZ9A"
    assert "D27:D58" in rows["core_crown-fiscal-2025"].selector
    assert "E30:E58" in rows["total_crown-fiscal-2025"].selector
    assert "F26:O26" in rows["core-crown-befu-2026"].selector
    assert "F25:O25" in rows["core-crown-hyefu-2025"].selector
    assert "wrong_population_universe" in rows["population-hlfs-rejected"].gaps
    assert rows["population-national-lead"].sources == []
