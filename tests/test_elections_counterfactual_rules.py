"""Unit tests for counterfactual voting rules and boundary geography engines."""

from __future__ import annotations

from archive_govt_nz.domains.elections.counterfactual_policy_rules_engine import (
    compute_gallagher_index,
    run_counterfactual_rules_analysis,
)
from archive_govt_nz.domains.elections.electorate_boundary_geography_engine import (
    compute_boundary_geography_analysis,
)


def test_counterfactual_rules_analysis() -> None:
    """Verify counterfactual voting rules scenarios and Gallagher calculations."""
    analysis = run_counterfactual_rules_analysis()
    assert len(analysis.scenarios) == 7

    # Check status quo
    sq = next(s for s in analysis.scenarios if s.rule_id == "mmp_status_quo_2026")
    assert sq.total_house_seats == 131
    assert sq.majority_threshold == 66
    assert sq.overhang_seats["National Party"] == 7
    assert sq.overhang_seats["Te Pāti Māori"] == 4

    # Check German leveling
    ger = next(s for s in analysis.scenarios if s.rule_id == "german_ausgleichsmandate_leveling")
    assert ger.total_house_seats == 148
    assert ger.majority_threshold == 75
    assert ger.overhang_seats["National Party"] == 0

    # Check IRV
    irv = next(s for s in analysis.scenarios if s.rule_id == "preferential_irv_in_electorates")
    assert irv.total_house_seats == 124
    assert irv.party_seats["Labour Party"] == 38
    assert irv.overhang_seats["National Party"] == 0

    # Check Gallagher calculation
    v = {"A": 50.0, "B": 50.0}
    s = {"A": 50.0, "B": 50.0}
    assert compute_gallagher_index(v, s) == 0.0


def test_boundary_geography_analysis() -> None:
    """Verify Representation Commission quota mechanics and 8th Māori seat analysis."""
    analysis = compute_boundary_geography_analysis()
    assert analysis.south_island_fixed_seats == 16
    assert analysis.tolerance_limit_pct == 5.0
    assert len(analysis.historical_cycles) == 7

    # Verify list pool contraction from 1996 to 2026
    first_cycle = analysis.historical_cycles[0]
    latest_cycle = analysis.historical_cycles[-1]
    assert first_cycle.total_electorates == 65  # 120 - 65 = 55 list seats
    assert latest_cycle.total_electorates == 72  # 120 - 72 = 48 list seats

    # Verify 8th Māori seat threshold data
    m8 = analysis.maori_electorate_8th_seat_threshold
    assert m8["current_maori_seats"] == 7
    assert m8["rounding_threshold_for_8th_seat"] == 7.500
    assert m8["exact_quotient"] > 7.40
