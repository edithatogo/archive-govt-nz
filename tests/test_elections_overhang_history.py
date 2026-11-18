"""Regression contracts for sourced New Zealand MMP overhang history."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from archive_govt_nz.domains.elections.overhang_history import (
    OVERHANG_BY_YEAR,
    OVERHANG_HISTORY,
)
from archive_govt_nz.domains.elections.predictive_engine import (
    get_historical_longitudinal_records,
)

ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "spaces/nz-election-explorer"


def test_mmp_overhang_history_has_eleven_source_backed_elections() -> None:
    """One record per MMP election, with no missing or duplicate years."""
    assert [row.year for row in OVERHANG_HISTORY] == [
        1996,
        1999,
        2002,
        2005,
        2008,
        2011,
        2014,
        2017,
        2020,
        2023,
        2026,
    ]
    assert [row.overhang_seats for row in OVERHANG_HISTORY] == [
        0,
        0,
        0,
        1,
        2,
        1,
        1,
        0,
        0,
        2,
        11,
    ]
    assert len(OVERHANG_BY_YEAR) == len(OVERHANG_HISTORY)
    assert all(row.source_url.startswith("https://") for row in OVERHANG_HISTORY)


def test_2023_official_overhang_excludes_port_waikato_by_election() -> None:
    """2023 had two overhang seats; its later by-election added a distinct seat."""
    assert OVERHANG_BY_YEAR[2023].overhang_seats == 2
    assert OVERHANG_BY_YEAR[2023].vintage == "official"
    assert 120 + OVERHANG_BY_YEAR[2023].overhang_seats == 122


def test_2026_is_explicitly_preliminary_and_matches_election_fixture() -> None:
    """The chart must not promote the 7 November count to official status."""
    fixture = json.loads(
        (SPACE / "data/2026-preliminary.json").read_text(encoding="utf-8")
    )
    item = OVERHANG_BY_YEAR[2026]
    assert item.vintage == fixture["vintage"] == "preliminary"
    assert item.published_date == fixture["published_date"] == "2026-11-07"
    assert item.overhang_seats == fixture["overhang_seats"] == 11
    assert item.source_url == fixture["source_url"]


def test_static_space_overhang_history_is_an_exact_export() -> None:
    """The static Space must not silently diverge from the Python figures."""
    actual = json.loads(
        (SPACE / "data/overhang-history.json").read_text(encoding="utf-8")
    )
    assert actual["schema_version"] == "1.0.0"
    assert actual["nominal_seats"] == 120
    assert actual["elections"] == [asdict(row) for row in OVERHANG_HISTORY]


def test_longitudinal_engine_uses_verified_overhang_values() -> None:
    """Other longitudinal fields cannot silently overwrite seat history."""
    records = get_historical_longitudinal_records()
    assert len(records) == 11
    assert {r.election_year: r.overhang_seats for r in records} == {
        row.year: row.overhang_seats for row in OVERHANG_HISTORY
    }
    assert next(r for r in records if r.election_year == 2023).total_house_seats == 122


def test_static_history_plot_is_data_driven_and_zero_based() -> None:
    """Do not surface the stale 120+overhang bitmap as the primary time series."""
    html = (SPACE / "index.html").read_text(encoding="utf-8")
    assert 'id="chart-longitudinal-overhang"' in html
    assert "data/overhang-history.json" in html
    assert "data/2026-preliminary.json" in html
    assert "Overhang seats above 120" in html
    assert '<img src="overhang_expansion_timeline.png"' not in html
    assert "11 MMP elections" in html


def test_historical_source_captures_are_identified_without_inventing_hashes() -> None:
    """Existing evidence is linked; uncaptured elections remain unverified."""
    receipt_path = ROOT / "evidence/nz-election-results-official-2023-20261110.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    capture = next(
        entry
        for entry in receipt["files"]
        if entry["url"].endswith("/statistics/csv/overall-results-summary.csv")
    )
    row = OVERHANG_BY_YEAR[2023]
    assert row.source_url == capture["url"]
    assert row.source_sha256 == capture["sha256"]
    assert row.capture_timestamp == receipt["finished_at"]
    assert row.capture_receipt == str(receipt_path.relative_to(ROOT))
    assert all(
        row.source_sha256 is None and row.capture_timestamp is None
        for row in OVERHANG_HISTORY
        if row.year in (1996, 1999, 2002, 2005, 2008, 2011, 2014, 2026)
    )
    assert OVERHANG_BY_YEAR[2026].capture_receipt is None


def test_public_dashboard_removes_legacy_unverified_research() -> None:
    """The published results surface must contain no unsupported research claims."""
    html = (SPACE / "index.html").read_text(encoding="utf-8")
    assert "Provisional results" in html
    assert "7 November 2026" in html
    assert "data/2026-preliminary.json" in html
    assert 'id="chart-longitudinal-overhang"' in html
    assert "76,429" not in html
    assert "94.2%" not in html
    assert "800,000" not in html
    assert "2029 Forecast" not in html
    assert "2014" in html
    assert "Port Waikato" in html
    assert "Cost / MP" not in html
