"""Tests for Māori Electorate Vote-Splitting & Upstream Transfer Engine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pyarrow.parquet as pq

from archive_govt_nz.domains.elections.generate_vote_splitting_figures import (
    generate_all_vote_splitting_figures,
)
from archive_govt_nz.domains.elections.maori_vote_splitting_engine import (
    analyze_maori_vote_splitting,
    analyze_system_wide_vote_splitting,
    build_caucus_crowding_out,
    build_general_seat_sample_splits,
    build_maori_electorate_records,
    calculate_excess_party_votes,
    calculate_party_vote_shares,
    materialize_vote_splitting_parquet,
    run_sainte_lague_counterfactual,
)


def test_maori_electorates_data() -> None:
    """Validate data integrity for all 7 Māori electorates."""
    records = build_maori_electorate_records()
    assert len(records) == 7

    names = {r.electorate_name for r in records}
    expected_names = {
        "Te Tai Tokerau",
        "Tāmaki Makaurau",
        "Hauraki-Waikato",
        "Waiariki",
        "Ikaroa-Rāwhiti",
        "Te Tai Hauāuru",
        "Te Tai Tonga",
    }
    assert names == expected_names

    for r in records:
        assert r.total_valid_party_votes > 25000
        assert r.party_percentages["Green Party"] > 40.0
        assert r.candidate_percentages["Te Pāti Māori"] > 50.0
        assert r.candidate_percentages["Green Party"] == 0.0
        # Vote-splitting index for TPM should be strongly positive
        assert r.vote_splitting_indices["Te Pāti Māori"] > 35.0
        # Vote-splitting index for Greens should be strongly negative (all PV, no candidate)
        assert r.vote_splitting_indices["Green Party"] < -40.0


def test_party_vote_shares_and_excess() -> None:
    """Verify party vote share disparities and excess vote calculations."""
    shares = calculate_party_vote_shares()
    assert "Green Party" in shares
    green_data = shares["Green Party"]

    # Greens won ~10.7% in general vs ~45.5% in Māori seats
    assert 10.0 <= green_data["general_pct"] <= 11.5
    assert 40.0 <= green_data["maori_pct"] <= 50.0
    assert 13.0 <= green_data["national_pct"] <= 14.0

    excess_records = calculate_excess_party_votes()
    green_excess = next(r for r in excess_records if r.party_name == "Green Party")

    # Excess party votes should be > 50,000 (roughly 76,000)
    assert green_excess.excess_party_votes > 50000
    assert 70000 <= green_excess.excess_party_votes <= 80000

    # Percentage point boost should be ~2.5 to 2.8 percentage points
    assert 2.0 <= green_excess.percentage_point_boost <= 3.0


def test_counterfactual_sainte_lague_impact() -> None:
    """Verify that removing Green excess PV strips 3 list seats and shrinks Parliament."""
    rows, actual_house, cf_house = run_sainte_lague_counterfactual(["Green Party"])

    assert actual_house == 131
    assert cf_house == 129  # 2 fewer overhang seats overall

    green_row = next(r for r in rows if r.party_name == "Green Party")
    assert green_row.actual_total_seats == 17
    assert green_row.counterfactual_total_seats == 14
    assert green_row.delta_list_seats == -3

    nat_row = next(r for r in rows if r.party_name == "National Party")
    assert nat_row.actual_total_seats == 43
    assert nat_row.counterfactual_total_seats == 43
    # National's entitlement increases from 36 to 38, so overhang drops from 7 to 5
    assert nat_row.actual_overhang == 7
    assert nat_row.counterfactual_overhang == 5

    lab_row = next(r for r in rows if r.party_name == "Labour Party")
    assert lab_row.delta_list_seats == 1  # Labour gains 1 list seat


def test_analyze_maori_vote_splitting_model() -> None:
    """Verify end-to-end Pydantic analysis payload validation."""
    analysis = analyze_maori_vote_splitting()
    assert analysis.election_year == 2026
    assert analysis.vintage == "preliminary"
    assert analysis.actual_house_size == 131
    assert analysis.counterfactual_house_size == 129
    assert analysis.house_size_reduction == 2
    assert analysis.green_list_seat_impact == -3
    assert len(analysis.data_sources_and_approximations) >= 5


def test_parquet_materialization() -> None:
    """Verify writing and reading back the Gold Parquet dataset."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        pq_path = Path(tmp_dir) / "test_vote_splitting.parquet"
        out = materialize_vote_splitting_parquet(pq_path)
        assert out.exists()

        table = pq.read_table(out)
        assert table.num_rows == 7
        assert "delta_list_seats" in table.column_names
        assert "excess_party_votes" in table.column_names


def test_generate_figures() -> None:
    """Verify generation of all 8 vote-splitting figures."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        figs = generate_all_vote_splitting_figures(Path(tmp_dir))
        assert len(figs) == 8
        for p in figs.values():
            assert p.exists()
            assert p.stat().st_size > 10000


def test_system_wide_vote_splitting() -> None:
    """Verify system-wide all-seat vote-splitting and caucus crowding mechanics."""
    analysis = analyze_system_wide_vote_splitting()
    assert analysis.total_electorates == 71
    assert analysis.general_electorates_count == 64
    assert analysis.maori_electorates_count == 7
    assert analysis.total_house_seats == 131
    assert analysis.overhang_seats_total == 11
    assert analysis.plurality_split_general_seats_count == 14
    assert analysis.coalition_threshold_actual == 66

    crowding = build_caucus_crowding_out()
    nat = next(c for c in crowding if c.party_name == "National Party")
    assert nat.list_seats_allocated == 0
    assert nat.crowding_out_status == "complete_extinction"

    tpm = next(c for c in crowding if c.party_name == "Te Pāti Māori")
    assert tpm.list_seats_allocated == 0
    assert tpm.crowding_out_status == "complete_extinction"

    act = next(c for c in crowding if c.party_name == "ACT New Zealand")
    assert act.list_seat_share_pct > 90.0

    general_splits = build_general_seat_sample_splits()
    assert len(general_splits) >= 5
    epsom = next(s for s in general_splits if s.electorate_name == "Epsom")
    assert epsom.split_index_by_party["ACT New Zealand"] > 40.0
