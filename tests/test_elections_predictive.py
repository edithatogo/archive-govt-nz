"""Tests for predictive machine learning and longitudinal election analytics."""

from __future__ import annotations

from archive_govt_nz.domains.elections.contracts import (
    ClimateEnvironmentalIndicators,
    MacroeconomicFundamentals,
    SocioeconomicIndicators,
)
from archive_govt_nz.domains.elections.predictive_engine import (
    calculate_cost_per_local_member,
    forecast_next_general_election_2029,
    get_historical_longitudinal_records,
    get_major_donors_archive,
    get_party_detailed_funding,
    predict_knife_edge_electorates_xgboost,
)


def test_predict_knife_edge_electorates_xgboost() -> None:
    """Test calibrated XGBoost prediction on 2026 preliminary close contests."""
    close_seats = [
        {
            "electorate_name": "Nelson",
            "prelim_winner": "National",
            "runner_up": "Labour",
            "margin": 72,
            "special_votes_pct": 14.5,
        },
        {
            "electorate_name": "Te Atatū",
            "prelim_winner": "Labour",
            "runner_up": "National",
            "margin": 131,
            "special_votes_pct": 15.0,
        },
        {
            "electorate_name": "Banks Peninsula",
            "prelim_winner": "National",
            "runner_up": "Labour",
            "margin": 215,
            "special_votes_pct": 14.0,
        },
    ]
    forecasts = predict_knife_edge_electorates_xgboost(close_seats)
    assert len(forecasts) == 3

    nelson = next(f for f in forecasts if f.electorate_name == "Nelson")
    # Nelson margin of 72 with high special vote share should exhibit high flip probability (> 65%)
    assert nelson.flip_probability_xgboost > 0.65

    te_atatu = next(f for f in forecasts if f.electorate_name == "Te Atatū")
    # Te Atatū is held by Labour, so flip probability to challenger National should be low (< 40%)
    assert te_atatu.flip_probability_xgboost < 0.40


def test_forecast_next_general_election_2029() -> None:
    """Test 2029 forecast with macroeconomic fundamentals, deprivation, and climate."""
    macro = MacroeconomicFundamentals(
        real_gdp_growth_pct=1.8,
        cpi_inflation_pct=2.4,
        two_year_mortgage_rate_pct=5.8,
        unemployment_rate_pct=4.8,
        incumbent_term_count=2,
    )
    socio = SocioeconomicIndicators(
        nzdep_median_decile=5.4,
        housing_affordability_ratio=7.2,
        food_cost_annual_change_pct=3.1,
    )
    climate = ClimateEnvironmentalIndicators(
        drought_soil_moisture_deficit_anomaly=0.2,
        severe_flood_cyclone_disaster_events=1,
    )

    forecast = forecast_next_general_election_2029(macro, socio, climate)
    assert forecast.target_election_year == 2029
    assert "National" in forecast.parliamentary_seat_projections
    assert "Labour" in forecast.parliamentary_seat_projections
    assert sum(forecast.coalition_formation_probabilities.values()) == 1.0


def test_calculate_cost_per_local_member() -> None:
    """Test candidate spending and cost per local electorate MP."""
    sample_candidates = [
        {
            "electorate_name": "Nelson",
            "party_name": "National",
            "candidate_expenditure": 28000.0,
            "electorate_won": True,
        },
        {
            "electorate_name": "Banks Peninsula",
            "party_name": "National",
            "candidate_expenditure": 26000.0,
            "electorate_won": True,
        },
        {
            "electorate_name": "Mount Albert",
            "party_name": "National",
            "candidate_expenditure": 22000.0,
            "electorate_won": False,
        },
        {
            "electorate_name": "Nelson",
            "party_name": "Labour",
            "candidate_expenditure": 29000.0,
            "electorate_won": False,
        },
        {
            "electorate_name": "Mount Albert",
            "party_name": "Labour",
            "candidate_expenditure": 27000.0,
            "electorate_won": True,
        },
    ]
    res = calculate_cost_per_local_member(sample_candidates)
    assert "National" in res
    assert res["National"]["electorates_won"] == 2
    # Total National candidate spend = 76,000 / 2 = 38,000
    assert res["National"]["cost_per_local_mp"] == 38000.0


def test_longitudinal_and_major_donors() -> None:
    """Test historical longitudinal benchmarks and major donor records."""
    records = get_historical_longitudinal_records()
    assert len(records) == 11
    # Check 2026 overhang
    rec_2026 = next(r for r in records if r.election_year == 2026)
    assert rec_2026.overhang_seats == 11
    assert rec_2026.total_house_seats == 131
    assert rec_2026.majority_threshold == 66

    donors = get_major_donors_archive()
    assert len(donors) >= 10
    hart = [d for d in donors if d.donor_name == "Graeme Hart"]
    assert len(hart) >= 2

    funding = get_party_detailed_funding()
    assert len(funding) == 7
    tpm = next(f for f in funding if f.party_name == "Te Pāti Māori")
    assert tpm.cost_per_local_electorate_mp == 23333.0
    top = next(f for f in funding if f.party_name == "The Opportunity Party")
    assert top.cost_per_local_electorate_mp is None
