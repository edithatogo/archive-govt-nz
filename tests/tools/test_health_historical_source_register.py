"""Historical discovery evidence must retain the full scope and unknown fixity."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


def test_historical_source_register_retains_scope_and_discovery_boundary() -> None:
    """No unvisited edition disappears and no observed link earns byte credit."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "archive-govt-nz.health-historical-sources/v1"
    assert datetime.fromisoformat(report["observed_at"]).utcoffset() is not None
    assert report["edition_years"] == list(range(1997, 2027))
    assert report["edition_count"] == len(report["edition_years"])
    assert report["fully_enumerated_editions"] == []
    assert report["pending_editions"] == report["edition_years"]
    assert report["payload_capture_performed"] is False
    assert report["publication_authorized"] is False
    assert report["whole_history_complete"] is False
    records = report["resource_observations"]
    assert len(records) == 36
    assert len({row["url"] for row in records}) == len(records)
    assert len({row["source_id"] for row in records}) == len(records)
    assert len({(r["edition_year"], r["family"], r["kind"]) for r in records}) == 36
    assert {(r["family"], r["kind"]) for r in records} == {
        ("budget", "expenditure"),
        ("budget", "revenue"),
        ("befu", "charts"),
        ("befu", "expense_tables"),
        ("hyefu", "charts"),
        ("hyefu", "expense_tables"),
        ("befu", "sna_series_tables"),
        ("befu", "gaap_series_tables"),
        ("befu", "expenses"),
    }
    budget_records = [row for row in records if row["family"] == "budget"]
    assert {(row["edition_year"], row["kind"]) for row in budget_records} == {
        (year, kind)
        for year in (2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024)
        for kind in ("expenditure", "revenue")
    }
    by_year = {row["edition_year"]: row for row in budget_records}
    assert by_year[2020]["rights_state"] == "not_evaluated"
    assert by_year[2020]["rights_evidence"] == "landing_page_states_cc_by_4_0"
    assert by_year[2022]["rights_state"] == "not_evaluated"
    assert by_year[2022]["rights_evidence"] == "landing_page_states_cc_by_4_0"
    assert by_year[2021]["rights_evidence"] == "licence_not_observed"
    befu_records = [row for row in records if row["family"] == "befu"]
    assert {
        (row["edition_year"], row["kind"])
        for row in befu_records
        if row["edition_year"] in (2018, 2019)
    } == {
        (year, kind) for year in (2018, 2019) for kind in ("charts", "expense_tables")
    }
    assert all(
        row["rights_state"] == "not_evaluated"
        and row["rights_evidence"] == "landing_page_states_cc_by_4_0"
        for row in records
        if row["edition_year"] in (2018, 2019)
    )
    for row in records:
        assert row["source_id"] == (
            "treasury-historical-"
            + hashlib.sha256(row["url"].encode()).hexdigest()[:16]
        )
        assert row["edition_year"] in report["edition_years"]
        assert row["disposition"] == "discovered"
        assert row["sha256"] is None
        assert row["byte_count"] is None
        assert row["rights_state"] == "not_evaluated"
        assert row["landing_url"] in report["observed_pages"]
        parsed = urlsplit(row["url"])
        assert parsed.scheme == "https"
        assert parsed.netloc == "www.treasury.govt.nz"
        assert parsed.path.endswith((".xls", ".xlsx", ".pdf"))
        assert not parsed.query
        assert not parsed.fragment
    for gap in report["edition_dispositions"]:
        assert gap["edition_year"] in report["edition_years"]
        assert gap["evidence_url"] in report["observed_pages"]
        assert gap["other_custodian_availability"] == "not_investigated"


def test_2017_budget_updates_and_hyefu_locators_are_bounded() -> None:
    """2017 workbook locators retain page-level rights and discovery limits."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    records = json.loads(path.read_text(encoding="utf-8"))["resource_observations"]
    sources = [row for row in records if row["edition_year"] == 2017]
    kinds_by_family = {
        family: {row["kind"] for row in sources if row["family"] == family}
        for family in ("budget", "befu", "hyefu")
    }
    assert kinds_by_family == {
        "budget": {"expenditure", "revenue"},
        "befu": {"charts", "expense_tables"},
        "hyefu": {"charts"},
    }
    assert all(
        row["rights_state"] == "not_evaluated"
        and row["rights_evidence"] == "landing_page_states_cc_by_4_0"
        and row["sha256"] is None
        and row["byte_count"] is None
        for row in sources
    )
