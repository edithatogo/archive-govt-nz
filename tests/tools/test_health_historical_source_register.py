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
    assert len(records) == 131
    assert len({row["url"] for row in records}) == len(records)
    assert len({row["source_id"] for row in records}) == len(records)
    assert len({(r["edition_year"], r["family"], r["kind"]) for r in records}) == len(
        records
    )
    assert len(records) == len(
        {(r["edition_year"], r["family"], r["kind"]) for r in records}
    )
    assert {(r["family"], r["kind"]) for r in records} == {
        ("budget", "expenditure"),
        ("budget", "revenue"),
        ("befu", "charts"),
        ("befu", "expense_tables"),
        ("hyefu", "charts"),
        ("hyefu", "expense_tables"),
        ("befu", "sna_series_tables"),
        ("befu", "gaap_series_tables"),
        ("befu", "additional_gaap_tables"),
        ("befu", "contents"),
        ("befu", "economic_outlook"),
        ("befu", "fiscal_outlook"),
        ("befu", "revenue"),
        ("befu", "specific_fiscal_risks"),
        ("befu", "responsibility_summary"),
        ("befu", "responsibility"),
        ("befu", "risks_scenarios"),
        ("befu", "full_release"),
        ("befu", "additional_fiscal_information"),
        ("befu", "additional_information"),
        ("befu", "cover_contents"),
        ("befu", "economic_forecasts"),
        ("befu", "economic_tax_outlook"),
        ("befu", "financial_information"),
        ("befu", "glossary"),
        ("befu", "responsibility_economic_outlook"),
        ("befu", "summary_tables"),
        ("befu", "tax_tables"),
        ("defu", "gaap_series_tables"),
        ("defu", "annex_glossary_link"),
        ("defu", "additional_gaap_tables"),
        ("defu", "economic_forecasts"),
        ("befu", "expenses"),
        ("vote_health", "main_estimates"),
        ("vote_health", "supplementary_estimates"),
    }
    assert {
        (row["edition_year"], row["family"], row["kind"])
        for row in records
        if row["edition_year"] in range(2007, 2017)
    } >= {
        (year, "budget", kind)
        for year in range(2007, 2017)
        for kind in ("expenditure", "revenue")
    } - {(2006, "budget", kind) for kind in ("expenditure", "revenue")}
    assert (2013, "befu", "charts") in {
        (row["edition_year"], row["family"], row["kind"]) for row in records
    }
    assert (2015, "hyefu", "charts") in {
        (row["edition_year"], row["family"], row["kind"]) for row in records
    }
    budget_records = [row for row in records if row["family"] == "budget"]
    assert {(row["edition_year"], row["kind"]) for row in budget_records} == {
        (year, kind)
        for year in range(2007, 2027)
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
        assert parsed.path.endswith((".xls", ".xlsx", ".pdf")) or (
            row["family"] == "befu" and row["kind"] in {"expense_tables", "expenses"}
        )
        assert not parsed.query
        assert not parsed.fragment
    for gap in report["edition_dispositions"]:
        assert gap["edition_year"] in report["edition_years"]
        assert gap["evidence_url"] in report["observed_pages"]
        assert gap["other_custodian_availability"] == "not_investigated"


def test_befu_2001_addendum_preserves_baseline_and_records_seven_locators() -> None:
    """New source observations extend a dated snapshot, not pinned evidence."""
    track = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    base_bytes = (track / "historical-source-register.json").read_bytes()
    base = json.loads(base_bytes)
    successor = json.loads(
        (track / "historical-source-register-20261024.json").read_text()
    )
    receipt = json.loads((track / "source-census-befu-2001-20261024.json").read_text())
    assert len(base["resource_observations"]) == 131
    assert len(successor["resource_observations"]) == 138
    assert (
        receipt["baseline_register"]["sha256"] == hashlib.sha256(base_bytes).hexdigest()
    )
    assert receipt["baseline_register"]["resource_count"] == 131
    assert receipt["successor_register"]["resource_count"] == 138
    successor_path = track / "historical-source-register-20261024.json"
    assert (
        receipt["successor_register"]["sha256"]
        == hashlib.sha256(successor_path.read_bytes()).hexdigest()
    )
    registered = {
        row["source_id"]: row
        for row in successor["resource_observations"]
        if row["edition_year"] == 2001 and row["family"] == "befu"
    }
    observed = {row["source_id"]: row for row in receipt["resources"]}
    assert len(registered) == 8
    assert len(observed) == 7
    assert all(registered[key] == value for key, value in observed.items())
    assert len({row["url"] for row in registered.values()}) == 8
    assert len({row["source_id"] for row in registered.values()}) == 8
    assert {row["url"].rsplit("/", 1)[-1] for row in observed.values()} == {
        "befu01-resp.pdf",
        "befu01-1.pdf",
        "befu01-2.pdf",
        "befu01-3.pdf",
        "befu01-4.pdf",
        "befu01-5.pdf",
        "befu01-ann.pdf",
    }
    assert receipt["page_observations"]["linked_resource_count_on_page"] == 8
    assert all(row["disposition"] == "discovered" for row in observed.values())
    assert all(row["rights_state"] == "not_evaluated" for row in observed.values())
    assert all(
        row["sha256"] is None and row["byte_count"] is None for row in observed.values()
    )
    assert all(row["native_layout_verified"] is False for row in observed.values())
    assert all(
        row["source_id"]
        == "treasury-historical-" + hashlib.sha256(row["url"].encode()).hexdigest()[:16]
        for row in observed.values()
    )
    assert receipt["period_observations"][0]["period_tokens"] == [
        "1997/98",
        "1998/99",
        "1999/2000",
        "2000/01",
        "2001/02",
        "2002/03",
        "2003/04",
        "2004/05",
    ]
    assert receipt["period_observations"][0]["unit_literal"] == "$ million"
    assert receipt["whole_edition_enumeration"] == "pending"
    assert receipt["whole_history_complete"] is False
    assert receipt["preservation_mutations"] is False


def test_befu_1998_links_preserve_status_scope_and_withdrawal_boundaries() -> None:
    """Release notices cannot change differently dated retained source records."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    report = json.loads(path.read_text())
    rows = [r for r in report["resource_observations"] if r["edition_year"] == 1998]
    assert {r["url"].rsplit("/", 1)[-1] for r in rows} == {
        "befu98-cont.pdf",
        "befu98-1.pdf",
        "befu98-2.pdf",
        "befu98-3.pdf",
        "befu98-sna.pdf",
        "befu98-4.pdf",
        "befu98-5.pdf",
        "befu98-gaap.pdf",
        "befu98-resp-summ.pdf",
        "befu98.pdf",
    }
    for row in rows:
        assert row["family"] == "befu"
        assert row["issue_date"] == "1998-05-14"
        assert row["native_layout_verified"] is False
        assert row["rights_state"] == "not_evaluated"
    sna = next(row for row in rows if row["kind"] == "sna_series_tables")
    assert sna["layout_status"] == "reader_footer_year_disagrees_with_release_context"
    full = next(row for row in rows if row["kind"] == "full_release")
    assert (
        full["publisher_title"] == "Budget Economic & Fiscal Update 1998 - Budget 1998"
    )
    notice = next(
        row for row in report["edition_dispositions"] if row["edition_year"] == 1998
    )
    assert notice["fiscal_period"] == "not_established_from_notice"
    assert notice["retained_capture_mutations"] is False
    observation = json.loads(
        (path.parent / "source-census-befu-1998-20261017.json").read_text()
    )
    assert observation["resources"] == rows
    assert observation["native_payload_capture_performed"] is False
    captured = json.loads((path.parent / "source-census.json").read_text())["records"]
    references = observation["existing_capture_references"]
    assert len(references) == 2
    by_id = {row["source_id"]: row for row in captured}
    assert all(
        by_id[reference["source_id"]][key] == value
        for reference in references
        for key, value in reference.items()
    )


def test_defu_2002_discovery_preserves_name_and_layout_qualification() -> None:
    """Exact discovery links cannot imply native layout or redistribution credit."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    report = json.loads(path.read_text(encoding="utf-8"))
    sources = {
        row["kind"]: row
        for row in report["resource_observations"]
        if row["edition_year"] == 2002 and row["family"] == "defu"
    }
    assert {key: row["url"].rsplit("/", 1)[-1] for key, row in sources.items()} == {
        "gaap_series_tables": "defu02-6.pdf",
        "annex_glossary_link": "defu02-7.pdf",
        "additional_gaap_tables": "add-gaap-defu02.pdf",
        "economic_forecasts": "extra-econ-forecasts-defu02.xls",
    }
    for row in sources.values():
        assert row["release_title"] == "December Economic and Fiscal Update (DEFU) 2002"
        assert row["issue_date"] == "2002-12-19"
        assert row["rights_state"] == "not_evaluated"
        assert row["sha256"] is None
        assert row["byte_count"] is None
    annex = sources["annex_glossary_link"]
    assert annex["layout_status"] == "publisher_label_web_reader_extent_discrepancy"
    assert annex["native_layout_verified"] is False
    befu = next(
        row
        for row in report["resource_observations"]
        if (row["edition_year"], row["family"], row["kind"])
        == (2002, "befu", "additional_gaap_tables")
    )
    assert befu["url"].endswith("/add-gaap02.pdf")
    observation = json.loads(
        (path.parent / "source-census-2002-befu-defu-20261017.json").read_text()
    )
    observed = {row["source_id"]: row for row in observation["resources"]}
    assert len(observed) == 5
    assert observed == {
        row["source_id"]: row
        for row in report["resource_observations"]
        if row["source_id"] in observed
    }
    assert observation["native_payload_capture_performed"] is False
    assert report["fully_enumerated_editions"] == []


def test_befu_2002_locator_preserves_rights_and_fixity_gaps() -> None:
    """The official BEFU source is identified without claiming captured bytes."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    records = json.loads(path.read_text(encoding="utf-8"))["resource_observations"]
    source = next(
        row
        for row in records
        if (row["edition_year"], row["family"], row["kind"])
        == (2002, "befu", "gaap_series_tables")
    )
    assert source["url"] == (
        "https://www.treasury.govt.nz/sites/default/files/2007-09/befu02-gaap.pdf"
    )
    assert source["rights_state"] == "not_evaluated"
    assert source["sha256"] is None
    assert source["byte_count"] is None


def test_vote_health_2002_locators_preserve_period_and_restructuring_context() -> None:
    """The two exact Vote Health PDFs keep their distinct fiscal periods."""
    path = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
        / "historical-source-register.json"
    )
    report = json.loads(path.read_text(encoding="utf-8"))
    records = report["resource_observations"]
    sources = {
        row["kind"]: row
        for row in records
        if row["edition_year"] == 2002 and row["family"] == "vote_health"
    }
    assert set(sources) == {"main_estimates", "supplementary_estimates"}
    assert sources["main_estimates"]["fiscal_year"] == "2002/03"
    assert sources["main_estimates"]["url"].endswith("/est02health.pdf")
    assert sources["supplementary_estimates"]["fiscal_year"] == "2001/02"
    assert sources["supplementary_estimates"]["url"].endswith("/supp02health.pdf")
    for source in sources.values():
        assert source["rights_state"] == "not_evaluated"
        assert source["rights_evidence"] == "resource_page_states_cc_by_4_0"
        assert source["sha256"] is None
        assert source["byte_count"] is None
    assert report["fully_enumerated_editions"] == []
    assert report["pending_editions"] == list(range(1997, 2027))


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


def test_befu_1999_identity_and_year_end_publication_dispositions() -> None:
    """A publisher typo and absent original must not fabricate source identity."""
    track = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    report = json.loads((track / "historical-source-register.json").read_text())
    rows = [r for r in report["resource_observations"] if r["edition_year"] == 1999]
    assert {r["url"].rsplit("/", 1)[-1] for r in rows} == {
        "befu99-cont.pdf",
        "befu99-resp.pdf",
        "befu99-1.pdf",
        "befu99-2.pdf",
        "befu99-3.pdf",
        "befu99-4.pdf",
        "befu99-gaap.pdf",
    }
    contents = next(r for r in rows if r["kind"] == "contents")
    assert contents["publisher_title"] == "BEFU 2019 Contents"
    assert contents["release_title"] == "Budget Economic and Fiscal Update (BEFU) 1999"
    assert (
        contents["layout_status"] == "publisher_label_year_disagrees_with_reader_cover"
    )
    assert all(r["issue_date"] == "1999-05-20" for r in rows)
    observation = json.loads(
        (track / "source-census-befu-1999-20261017.json").read_text()
    )
    assert observation["resources"] == rows
    assert observation["numeric_cells_admitted"] is False
    assert observation["native_payload_capture_performed"] is False
    assert observation["fiscal_expense_table"]["status_tokens"] == [
        "Actual",
        "Actual",
        "Actual",
        "Actual",
        "Actual",
        "Forecast",
        "Projection",
        "Projection",
        "Projection",
    ]
    assert observation["gaap_definitions"]["forecast"] == "1999/2000"
    gaps = {
        r["edition_year"]: r
        for r in report["edition_dispositions"]
        if r["family"] == "december_economic_and_fiscal_update"
    }
    assert (
        gaps[1998]["disposition"]
        == "publisher_reported_publication_original_locator_unresolved"
    )
    assert gaps[1998]["publication_date"] == "1998-12-09"
    assert (
        gaps[1999]["disposition"] == "publisher_reports_no_december_update_publication"
    )
    for gap in gaps.values():
        assert gap["original_document_url"] is None
        assert gap["replacement_source_admitted"] is False
        assert gap["retained_capture_mutations"] is False
    assert report["fully_enumerated_editions"] == []


def test_remaining_locator_years_preserve_discovery_and_url_alias_boundaries() -> None:
    """Every year has a locator without claiming complete families or new captures."""
    track = (
        Path(__file__).parents[2]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    history = json.loads((track / "historical-source-register.json").read_text())
    observation = json.loads(
        (track / "source-census-locator-gaps-20261017.json").read_text()
    )
    rows = [
        r
        for r in history["resource_observations"]
        if r["edition_year"] in {2000, 2003, 2004, 2006, 2025, 2026}
    ]
    assert len(rows) == 38
    assert observation["resources"] == rows
    assert {r["edition_year"] for r in history["resource_observations"]} == set(
        range(1997, 2027)
    )
    assert history["fully_enumerated_editions"] == []
    assert history["whole_history_complete"] is False
    by_file = {r["url"].rsplit("/", 1)[-1]: r for r in rows}
    assert by_file["befu03-sumtab.pdf"]["publisher_title"].startswith(
        "Financial Information -"
    )
    assert by_file["befu03-add1.pdf"]["publisher_title"].startswith("Summary Tables -")
    assert by_file["befu04-add2.xls"]["publisher_title"].endswith("Update 2005")
    assert all(
        by_file[name]["native_layout_verified"] is False
        for name in [
            "befu03-sumtab.pdf",
            "befu03-add1.pdf",
            "befu04-add2.xls",
        ]
    )
    related = observation["related_links_pending_scope_review"]
    assert len(related) == 4
    assert all(r["disposition"] == "discovered" for r in related)
    assert all(
        r["scope_review"] == "pending_content_review_before_inclusion_or_exclusion"
        for r in related
    )
    assert observation["native_capture_performed"] is False
    assert observation["url_alias_byte_equivalence_verified"] is False
    census = json.loads((track / "source-census.json").read_text())["records"]
    by_id = {r["source_id"]: r for r in census}
    references = observation["existing_capture_references"]
    assert len(references) == 2
    assert all(
        by_id[r["source_id"]][key] == value
        for r in references
        for key, value in r.items()
    )
    assert not {r["url"] for r in references} & {r["url"] for r in rows}
