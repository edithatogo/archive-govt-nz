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
    return json.loads((TRACK / "context-census.json").read_text(encoding="utf-8"))


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
    population = rows["population-national-annual-mean"]
    assert population.sources == []
    assert (
        "export_is_hash_pinned_in_population_annual_context_not_source_census"
        in population.gaps
    )
    assert "DPE056AA" in population.series_id
    assert "Total All Ages" in population.selector
    assert "Mean year ended" in population.selector
    assert "1991" in population.period
    assert "2026" in population.period
    assert "transport_http_warc_receipt_unavailable" in population.gaps


def test_gdp_release_date_is_bound_to_official_page_observation() -> None:
    rows = {row.id: row for row in Census.model_validate(document()).series}
    gdp = rows["gdp-stats-2026q1"]
    assert "published 17 September 2026" in gdp.period
    observation_path = (
        "conductor/tracks/health_appropriations_medallion_assimilation_20260829/"
        "gdp-release-observation-20260930.json"
    )
    assert observation_path in gdp.evidence
    observation = json.loads((ROOT / observation_path).read_text(encoding="utf-8"))
    assert observation["publication_date_string"] == "17 September 2026"
    assert observation["workbook_capture_state"] == "captured_separately"
    assert observation["rights_decision"] == "not_evaluated"


def test_june_gdp_capture_is_a_separate_unqualified_vintage() -> None:
    rows = {row.id: row for row in Census.model_validate(document()).series}
    march = rows["gdp-stats-2026q1"]
    june = rows["gdp-stats-2026q2"]
    assert march.qualification == june.qualification == "unqualified"
    assert june.rights == "not_evaluated"
    assert "C27:BK27" in june.selector
    assert "Table 2" in june.selector
    assert "61" in june.period
    assert "not spliced" in march.period
    assert june.sources[0].source_id == "stats_nz_gdp-588a47c19c9dbc44"
    capture = json.loads(
        (
            ROOT
            / "conductor/tracks/health_appropriations_medallion_assimilation_20260829/"
            "gdp-june-capture-20260930.json"
        ).read_text(encoding="utf-8")
    )
    assert capture["selected_series"]["quarter_observations"] == 61
    assert capture["selected_series"]["currency_code"] == "unverified"
    assert capture["analytical_disposition"]["qualification"] == "unqualified"
