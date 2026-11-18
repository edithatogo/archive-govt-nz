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
        1996, 1999, 2002, 2005, 2008, 2011, 2014, 2017, 2020, 2023, 2026,
    ]
    assert [row.overhang_seats for row in OVERHANG_HISTORY] == [
        0, 0, 0, 1, 2, 1, 1, 0, 0, 2, 11,
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
    assert (
        next(r for r in records if r.election_year == 2023).total_house_seats
        == 122
    )


def test_static_history_plot_is_data_driven_and_zero_based() -> None:
    """Do not surface the stale 120+overhang bitmap as the primary time series."""
    html = (SPACE / "index.html").read_text(encoding="utf-8")
    assert 'id="chart-longitudinal-overhang"' in html
    assert "data/overhang-history.json" in html
    assert "data/2026-preliminary.json" in html
    assert "Overhang seats above 120" in html
    assert '<img src="overhang_expansion_timeline.png"' not in html
    assert "11 MMP elections" in html
