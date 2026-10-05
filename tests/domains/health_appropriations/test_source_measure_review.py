"""The source/measure review remains precise about coverage and evidence gaps."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.source_measure_review import (
    TRACK as TRACK_RELATIVE,
)
from archive_govt_nz.domains.health_appropriations.source_measure_review import (
    _captured_years,
    _check_discovered,
    _family,
    _fiscal_year,
    _Review,
    validate_review,
)

ROOT = Path(__file__).resolve().parents[3]
TRACK = ROOT / TRACK_RELATIVE
REPORT = TRACK / "source-measure-review-20261005.json"


def test_review_reports_exact_series_and_preserves_blockers() -> None:
    report = validate_review(REPORT, ROOT)
    assert report["series_count"] == 8
    assert report["source_families"]["vote_health"]["captured_documents"] == 59
    assert report["source_families"]["vote_health"]["estimates_years"] == [
        1998,
        1999,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2008,
        2014,
        2015,
        2016,
        2017,
        2022,
        2023,
        2024,
        2025,
        2026,
    ]
    assert report["source_families"]["vote_health"]["supplementary_years"] == [
        1998,
        1999,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2008,
        2009,
        2010,
        2011,
        2013,
        2014,
        2015,
        2016,
        2017,
        2018,
        2019,
        2020,
        2021,
        2022,
        2023,
        2024,
        2025,
    ]
    assert report["series"]["population"]["series_id"].startswith("DPE056AA")
    assert (
        report["series"]["population"]["rights"]
        == "publisher_default_observed_unadjudicated"
    )
    population_rights = next(
        item
        for item in report["evidence"]
        if item["path"].endswith("population-rights-review-20261002.md")
    )
    assert (
        population_rights["sha256"]
        == hashlib.sha256(
            (TRACK / "population-rights-review-20261002.md").read_bytes()
        ).hexdigest()
    )
    wages = report["series"]["wages"]
    assert "pay week ending on or before the 20th" in wages["period_basis"]
    assert "not a full-quarter average" in wages["period_basis"]
    assert "not a constant-quality wage index" in wages["analytical_status"]
    assert wages["rights"] == "publisher_default_observed_unadjudicated"
    assert any(
        evidence["path"].endswith("qes-methodology-rights-review-20261002.md")
        for evidence in report["evidence"]
    )
    for path, digest in (
        (
            TRACK / "qes-series-metadata-20261002.json.gz",
            "be2715d1549f68bf2b0e60a9262b204690f8dbf8105c4c565594ea09d566df3f",
        ),
        (
            TRACK / "qes-data-collection-metadata-20261002.json.gz",
            "699a1fbb3df5b849974604b1a67dbbe0b1e15997921a3877699565c15151a19b",
        ),
    ):
        assert hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest() == digest
    assert "2011Q2" in report["series"]["gdp"]["vintage_or_range"]
    assert "2026Q1" in report["series"]["gdp"]["vintage_or_range"]
    assert (
        "Official GDP release for June 2026 exists"
        in report["series"]["gdp"]["vintage_or_range"]
    )
    assert report["source_families"]["historical_editions"]["complete"] is False
    assert (
        len(report["source_families"]["vote_health"]["discovered_estimates_urls"]) == 9
    )
    assert (
        len(report["source_families"]["vote_health"]["discovered_supplementary_urls"])
        == 2
    )


def test_review_rejects_unsubstantiated_admission(tmp_path: Path) -> None:
    report = json.loads(REPORT.read_text())
    report["series"]["population"]["rights"] = "approved"
    path = tmp_path / "review.json"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=r"invalid source-measure review"):
        validate_review(path, ROOT)


def test_review_scope_is_one_supported_literal() -> None:
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    _Review.model_validate(data)
    data["scope"] = "analytical_admission"
    with pytest.raises(ValueError, match="scope"):
        _Review.model_validate(data)


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict]:
    root = tmp_path / "fixture-root"
    track = root / TRACK
    track.mkdir(parents=True, exist_ok=True)
    report = json.loads(REPORT.read_text())
    for evidence in report["evidence"]:
        source = ROOT / evidence["path"]
        target = root / evidence["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        evidence["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    path = tmp_path / "review.json"
    path.write_text(json.dumps(report))
    return path, root, report


def _pin(report: dict, root: Path, relative: str) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    next(item for item in report["evidence"] if item["path"] == relative)["sha256"] = (
        digest
    )


def _mutate_vote(report: dict, mutation: str) -> None:
    vote = report["source_families"]["vote_health"]
    if mutation == "vote_count":
        vote["captured_documents"] += 1
    elif mutation == "vote_estimates":
        vote["estimates_years"].append(2012)
    elif mutation == "vote_supplementary":
        vote["supplementary_years"].append(2026)
    elif mutation == "vote_missing_estimates":
        vote["missing_estimates_years"].pop()
    elif mutation == "vote_missing_supplementary":
        vote["missing_supplementary_years"].pop()
    elif mutation == "discovered_year":
        vote["discovered_estimates_urls"]["2014"] = (
            "https://www.treasury.govt.nz/publications/budget"
        )
    elif mutation == "discovered_url":
        vote["discovered_estimates_urls"]["2012"] = "https://example.com/not-official"
    elif mutation == "discovered_missing":
        vote["discovered_estimates_urls"].pop("2012")
    elif mutation == "discovered_extra":
        vote["discovered_estimates_urls"]["2014"] = (
            "https://www.treasury.govt.nz/publications/budget"
        )


def _mutate_history(report: dict, mutation: str) -> None:
    history = report["source_families"]["historical_editions"]
    if mutation == "historical_locator_count":
        history["locator_count"] += 1
    elif mutation == "historical_editions":
        history["editions_with_locators"].pop()
    elif mutation == "historical_missing":
        history["editions_missing_locators"].pop()
    elif mutation == "historical_complete":
        history["complete"] = True
    elif mutation == "historical_fully_enumerated":
        history["fully_enumerated_editions"] = [2007, 2007]
    elif mutation == "historical_partial":
        history["fully_enumerated_editions"] = [2007]
        history["complete"] = False
    elif mutation == "historical_out_of_scope":
        history["fully_enumerated_editions"] = [1900]


def _mutate_evidence(report: dict, root: Path, mutation: str) -> None:
    item = report["evidence"][0]
    if mutation == "path_escape":
        item["path"] = "../outside.json"
    elif mutation == "absolute_path":
        item["path"] = str((root / TRACK_RELATIVE / "source-census.json").resolve())
    elif mutation == "missing_file":
        item["path"] = f"{TRACK_RELATIVE}/absent.json"
    elif mutation == "evidence_pin":
        item["sha256"] = "0" * 64


def _mutate(report: dict, root: Path, mutation: str) -> None:
    if mutation == "series_count":
        report["series_count"] -= 1
    elif mutation.startswith(("vote_", "discovered_")):
        _mutate_vote(report, mutation)
    elif mutation.startswith("historical_"):
        _mutate_history(report, mutation)
    elif mutation in {"path_escape", "absolute_path", "missing_file", "evidence_pin"}:
        _mutate_evidence(report, root, mutation)
    elif mutation == "captured_forecast":
        report["source_families"]["budget_befu_hyefu"][
            "captured_budget_editions"
        ].append(2008)
    elif mutation == "forecast_locator_editions":
        report["source_families"]["budget_befu_hyefu"][
            "known_historical_workbook_locator_register_editions"
        ].pop()
    elif mutation == "population_id":
        report["series"]["population"]["series_id"] = "wrong"
    elif mutation == "population_hash":
        report["series"]["population"]["source_sha256"] = "0" * 64
    else:
        raise AssertionError(mutation)


def _run_mutation(tmp_path: Path, mutation: str, expected: str) -> None:
    path, root, report = _fixture(tmp_path)
    _mutate(report, root, mutation)
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match=expected):
        validate_review(path, root)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("series_count", "series_count mismatch"),
        ("vote_count", "Vote Health captured count mismatch"),
        ("vote_estimates", "Vote Health Estimates coverage mismatch"),
        ("vote_supplementary", "Vote Health Supplementary coverage mismatch"),
        ("vote_missing_estimates", "Vote Health missing Estimates mismatch"),
        (
            "vote_missing_supplementary",
            "Vote Health missing Supplementary mismatch",
        ),
        ("discovered_year", "invalid discovered Vote Health locator"),
        ("discovered_url", "invalid discovered Vote Health locator"),
        ("discovered_missing", "invalid discovered Vote Health locator"),
        ("discovered_extra", "invalid discovered Vote Health locator"),
        (
            "historical_locator_count",
            "historical edition locator coverage mismatch",
        ),
        ("historical_editions", "historical edition locator coverage mismatch"),
        ("historical_missing", "historical missing edition coverage mismatch"),
        ("historical_complete", "historical completion claim mismatch"),
        ("historical_fully_enumerated", "historical completion claim mismatch"),
        ("historical_out_of_scope", "historical completion claim mismatch"),
        ("captured_forecast", "captured Budget/BEFU/HYEFU edition mismatch"),
        (
            "forecast_locator_editions",
            "historical workbook locator edition mismatch",
        ),
        ("population_id", "population series mismatch"),
        ("population_hash", "population source hash mismatch"),
        ("path_escape", "invalid source-measure evidence"),
        ("absolute_path", "invalid source-measure evidence"),
        ("missing_file", "invalid source-measure evidence"),
        ("evidence_pin", "invalid source-measure evidence"),
    ],
)
def test_review_rejects_drift_and_inconsistent_counts(
    tmp_path: Path, mutation: str, expected: str
) -> None:
    _run_mutation(tmp_path, mutation, expected)


def test_read_review_rejects_missing_or_malformed_json(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid source-measure review schema"):
        validate_review(tmp_path / "missing.json", ROOT)
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{")
    with pytest.raises(ValueError, match="invalid source-measure review schema"):
        validate_review(malformed, ROOT)


def test_review_requires_source_and_history_evidence(tmp_path: Path) -> None:
    path, root, report = _fixture(tmp_path)
    report["evidence"] = []
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="required source census evidence missing"):
        validate_review(path, root)


def test_partial_historical_enumeration_is_valid_when_incomplete(
    tmp_path: Path,
) -> None:
    path, root, report = _fixture(tmp_path)
    _mutate_history(report, "historical_partial")
    path.write_text(json.dumps(report), encoding="utf-8")
    validate_review(path, root)


def test_family_requires_mapping() -> None:
    report = _Review.model_validate(
        {
            "schema_version": "1",
            "observed_at": "today",
            "scope": "inventory_and_period_rights_assessment_only_no_analytical_admission_or_legal_approval",
            "series": {},
            "series_count": 0,
            "source_families": {"broken": []},
            "evidence": [],
        }
    )
    with pytest.raises(TypeError):
        _family(report, "broken")


@pytest.mark.parametrize("title", ["Vote Health Estimates", "Appropriation 2027-28"])
def test_fiscal_year_requires_official_two_digit_fiscal_year(title: str) -> None:
    with pytest.raises(ValueError, match="no fiscal year"):
        _fiscal_year(title)


def test_fiscal_year_and_captured_years_accept_valid_rows() -> None:
    assert _fiscal_year("Vote Health Estimates of Appropriations 2025/26") == 2025
    records = [
        {"family": "budget_2024_table", "disposition": "captured"},
        {"family": "budget_2024_duplicate", "disposition": "captured"},
        {"family": "budget_2025_table", "disposition": "discovered"},
    ]
    assert _captured_years(records, "budget") == [2024]


@pytest.mark.parametrize(
    ("year", "url"),
    [
        (1998, "https://www.treasury.govt.nz/publications/x"),
        (2012, "https://example.com/not-official"),
    ],
)
def test_discovered_locator_rejects_nonmissing_year_and_nonofficial_host(
    year: int, url: str
) -> None:
    with pytest.raises(ValueError, match="invalid discovered Vote Health locator"):
        _check_discovered({"locators": {str(year): url}}, "locators", {2012})
