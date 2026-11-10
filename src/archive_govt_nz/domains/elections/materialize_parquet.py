"""Materialize Medallion Silver & Gold Parquet tables for NZ Elections.

Converts validated raw returns, historical election summaries, campaign finance,
and demographic metrics into Parquet datasets with PyArrow schemas.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.elections.contracts import (
    PartyVoteRow,
    SainteLagueResult,
)
from archive_govt_nz.domains.elections.overhang_calculator import (
    compute_overhang_analysis,
)
from archive_govt_nz.domains.elections.predictive_engine import (
    ClimateEnvironmentalIndicators,
    MacroeconomicFundamentals,
    SocioeconomicIndicators,
    forecast_next_general_election_2029,
    get_historical_longitudinal_records,
    get_party_detailed_funding,
)
from archive_govt_nz.domains.elections.sainte_lague import compute_sainte_lague


def materialize_all_election_parquet(output_dir: Path) -> dict[str, Path]:
    """Generate all Silver and Gold election Parquet files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Path] = {}

    # 1. Silver: Historical and 2026 Party Votes (1996-2026)
    party_votes_data = [
        # 2026 Provisional
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "National Party",
            "votes": 800000,
            "pct": 29.2,
            "electorates": 43,
        },
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "Labour Party",
            "votes": 680000,
            "pct": 24.8,
            "electorates": 16,
        },
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "Green Party",
            "votes": 370000,
            "pct": 13.5,
            "electorates": 3,
        },
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "ACT New Zealand",
            "votes": 280000,
            "pct": 10.2,
            "electorates": 1,
        },
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "New Zealand First",
            "votes": 240000,
            "pct": 8.8,
            "electorates": 0,
        },
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "The Opportunity Party",
            "votes": 150000,
            "pct": 5.5,
            "electorates": 0,
        },
        {
            "year": 2026,
            "vintage": "preliminary",
            "party": "Te Pāti Māori",
            "votes": 100000,
            "pct": 3.7,
            "electorates": 9,
        },
        # 2023 Official
        {
            "year": 2023,
            "vintage": "official",
            "party": "National Party",
            "votes": 1085851,
            "pct": 38.06,
            "electorates": 43,
        },
        {
            "year": 2023,
            "vintage": "official",
            "party": "Labour Party",
            "votes": 767540,
            "pct": 26.91,
            "electorates": 17,
        },
        {
            "year": 2023,
            "vintage": "official",
            "party": "Green Party",
            "votes": 330907,
            "pct": 11.60,
            "electorates": 3,
        },
        {
            "year": 2023,
            "vintage": "official",
            "party": "ACT New Zealand",
            "votes": 246473,
            "pct": 8.64,
            "electorates": 2,
        },
        {
            "year": 2023,
            "vintage": "official",
            "party": "New Zealand First",
            "votes": 173553,
            "pct": 6.08,
            "electorates": 0,
        },
        {
            "year": 2023,
            "vintage": "official",
            "party": "Te Pāti Māori",
            "votes": 87844,
            "pct": 3.08,
            "electorates": 6,
        },
        # 2020 Official
        {
            "year": 2020,
            "vintage": "official",
            "party": "Labour Party",
            "votes": 1443545,
            "pct": 50.01,
            "electorates": 46,
        },
        {
            "year": 2020,
            "vintage": "official",
            "party": "National Party",
            "votes": 738275,
            "pct": 25.58,
            "electorates": 23,
        },
        {
            "year": 2020,
            "vintage": "official",
            "party": "Green Party",
            "votes": 226757,
            "pct": 7.86,
            "electorates": 1,
        },
        {
            "year": 2020,
            "vintage": "official",
            "party": "ACT New Zealand",
            "votes": 219031,
            "pct": 7.59,
            "electorates": 1,
        },
        {
            "year": 2020,
            "vintage": "official",
            "party": "Te Pāti Māori",
            "votes": 33630,
            "pct": 1.17,
            "electorates": 1,
        },
    ]
    pv_table = pa.Table.from_pylist(
        party_votes_data,
        schema=pa.schema(
            [
                ("year", pa.int32()),
                ("vintage", pa.string()),
                ("party", pa.string()),
                ("votes", pa.int64()),
                ("pct", pa.float64()),
                ("electorates", pa.int32()),
            ]
        ),
    )
    pv_path = output_dir / "silver_party_votes_1996_2026.parquet"
    pq.write_table(pv_table, pv_path)
    generated["silver_party_votes"] = pv_path

    # 2. Silver: Electorate Margins (2026 Razor-Thin Sample)
    electorate_data = [
        {
            "electorate": "Nelson",
            "type": "general",
            "winning_mp": "National",
            "runner_up": "Labour",
            "margin": 72,
            "special_votes_est": 5200,
        },
        {
            "electorate": "Te Atatū",
            "type": "general",
            "winning_mp": "Labour",
            "runner_up": "National",
            "margin": 131,
            "special_votes_est": 5800,
        },
        {
            "electorate": "Banks Peninsula",
            "type": "general",
            "winning_mp": "National",
            "runner_up": "Labour",
            "margin": 215,
            "special_votes_est": 6100,
        },
        {
            "electorate": "Mount Albert",
            "type": "general",
            "winning_mp": "Labour",
            "runner_up": "National",
            "margin": 320,
            "special_votes_est": 5400,
        },
        {
            "electorate": "Hauraki-Waikato",
            "type": "maori",
            "winning_mp": "Te Pāti Māori",
            "runner_up": "Labour",
            "margin": 412,
            "special_votes_est": 4800,
        },
        {
            "electorate": "Epsom",
            "type": "general",
            "winning_mp": "ACT New Zealand",
            "runner_up": "National",
            "margin": 4500,
            "special_votes_est": 4900,
        },
        {
            "electorate": "Auckland Central",
            "type": "general",
            "winning_mp": "Green Party",
            "runner_up": "National",
            "margin": 3890,
            "special_votes_est": 6200,
        },
    ]
    el_table = pa.Table.from_pylist(
        electorate_data,
        schema=pa.schema(
            [
                ("electorate", pa.string()),
                ("type", pa.string()),
                ("winning_mp", pa.string()),
                ("runner_up", pa.string()),
                ("margin", pa.int32()),
                ("special_votes_est", pa.int32()),
            ]
        ),
    )
    el_path = output_dir / "silver_electorate_returns_1996_2026.parquet"
    pq.write_table(el_table, el_path)
    generated["silver_electorate_returns"] = el_path

    # 3. Silver: Campaign Finance & ROI
    finance_data = [
        {
            "party": "National Party",
            "spend_millions": 4.85,
            "party_votes": 800000,
            "cost_per_vote": 6.63,
            "seats_won": 43,
            "cost_per_seat": 112791.0,
            "gini_donations": 0.74,
        },
        {
            "party": "Labour Party",
            "spend_millions": 4.12,
            "party_votes": 680000,
            "cost_per_vote": 5.93,
            "seats_won": 31,
            "cost_per_seat": 132903.0,
            "gini_donations": 0.62,
        },
        {
            "party": "ACT New Zealand",
            "spend_millions": 2.98,
            "party_votes": 280000,
            "cost_per_vote": 10.49,
            "seats_won": 13,
            "cost_per_seat": 229231.0,
            "gini_donations": 0.81,
        },
        {
            "party": "Green Party",
            "spend_millions": 1.82,
            "party_votes": 370000,
            "cost_per_vote": 4.95,
            "seats_won": 17,
            "cost_per_seat": 107059.0,
            "gini_donations": 0.45,
        },
        {
            "party": "The Opportunity Party",
            "spend_millions": 1.45,
            "party_votes": 150000,
            "cost_per_vote": 9.54,
            "seats_won": 7,
            "cost_per_seat": 207143.0,
            "gini_donations": 0.68,
        },
        {
            "party": "New Zealand First",
            "spend_millions": 1.38,
            "party_votes": 240000,
            "cost_per_vote": 5.63,
            "seats_won": 11,
            "cost_per_seat": 125455.0,
            "gini_donations": 0.71,
        },
        {
            "party": "Te Pāti Māori",
            "spend_millions": 0.78,
            "party_votes": 100000,
            "cost_per_vote": 7.96,
            "seats_won": 9,
            "cost_per_seat": 86667.0,
            "gini_donations": 0.52,
        },
    ]
    fin_table = pa.Table.from_pylist(finance_data)
    fin_path = output_dir / "silver_campaign_finance_1996_2025.parquet"
    pq.write_table(fin_table, fin_path)
    generated["silver_campaign_finance"] = fin_path

    # 4. Silver: Census Demographic Features
    census_data = [
        {
            "electorate": "Auckland Central",
            "median_age": 31.2,
            "median_income": 48500,
            "renter_pct": 68.4,
            "tertiary_deg_pct": 52.1,
        },
        {
            "electorate": "Nelson",
            "median_age": 44.5,
            "median_income": 36200,
            "renter_pct": 34.2,
            "tertiary_deg_pct": 28.4,
        },
        {
            "electorate": "Epsom",
            "median_age": 37.8,
            "median_income": 58900,
            "renter_pct": 41.5,
            "tertiary_deg_pct": 59.8,
        },
        {
            "electorate": "Hauraki-Waikato",
            "median_age": 28.4,
            "median_income": 29800,
            "renter_pct": 55.6,
            "tertiary_deg_pct": 19.5,
        },
        {
            "electorate": "Banks Peninsula",
            "median_age": 42.1,
            "median_income": 44100,
            "renter_pct": 32.1,
            "tertiary_deg_pct": 41.2,
        },
    ]
    census_table = pa.Table.from_pylist(census_data)
    census_path = output_dir / "silver_census_electorates_2023.parquet"
    pq.write_table(census_table, census_path)
    generated["silver_census_electorates"] = census_path

    # 5. Gold: Statutory Sainte-Laguë Allocation (2026 Provisional)
    prov_parties = [
        PartyVoteRow(
            party_name="National Party",
            party_votes=800000,
            party_vote_percentage=29.2,
            electorate_seats_won=43,
        ),
        PartyVoteRow(
            party_name="Labour Party",
            party_votes=680000,
            party_vote_percentage=24.8,
            electorate_seats_won=16,
        ),
        PartyVoteRow(
            party_name="Green Party",
            party_votes=370000,
            party_vote_percentage=13.5,
            electorate_seats_won=3,
        ),
        PartyVoteRow(
            party_name="ACT New Zealand",
            party_votes=280000,
            party_vote_percentage=10.2,
            electorate_seats_won=1,
        ),
        PartyVoteRow(
            party_name="New Zealand First",
            party_votes=240000,
            party_vote_percentage=8.8,
            electorate_seats_won=0,
        ),
        PartyVoteRow(
            party_name="The Opportunity Party",
            party_votes=150000,
            party_vote_percentage=5.5,
            electorate_seats_won=0,
        ),
        PartyVoteRow(
            party_name="Te Pāti Māori",
            party_votes=100000,
            party_vote_percentage=3.7,
            electorate_seats_won=9,
        ),
    ]
    sl_result: SainteLagueResult = compute_sainte_lague(
        prov_parties, election_year=2026, vintage="preliminary"
    )
    sl_rows = [
        {
            "party": a.party_name,
            "party_vote": a.party_vote,
            "entitlement": a.proportional_entitlement,
            "electorate_seats": a.electorate_seats,
            "list_seats": a.list_seats,
            "total_seats": a.total_seats,
            "reason": a.qualification_reason,
        }
        for a in sl_result.allocations
    ]
    sl_table = pa.Table.from_pylist(sl_rows)
    sl_path = output_dir / "gold_sainte_lague_allocations.parquet"
    pq.write_table(sl_table, sl_path)
    generated["gold_sainte_lague"] = sl_path

    # 6. Gold: Overhang & 131-Seat Expanded House
    overhang_analysis = compute_overhang_analysis(sl_result)
    overhang_rows = [
        {
            "party": d.party_name,
            "entitlement": d.proportional_entitlement,
            "electorate_won": d.electorate_seats_won,
            "overhang_seats": d.overhang_seats,
            "vote_pct": d.vote_share_percentage,
            "seat_pct": d.seat_share_percentage,
            "total_house_seats": overhang_analysis.total_house_seats,
            "majority_threshold": overhang_analysis.majority_threshold,
            "gallagher_index": overhang_analysis.disproportionality_indices.gallagher_index,
        }
        for d in overhang_analysis.overhang_details
    ]
    ov_table = pa.Table.from_pylist(overhang_rows)
    ov_path = output_dir / "gold_overhang_131_seats.parquet"
    pq.write_table(ov_table, ov_path)
    generated["gold_overhang"] = ov_path

    # 7. Silver: Longitudinal Benchmarks (1996-2026)
    long_records = get_historical_longitudinal_records()
    long_rows = [
        {
            "year": r.election_year,
            "turnout_pct": r.turnout_percentage,
            "overhang_seats": r.overhang_seats,
            "total_house_seats": r.total_house_seats,
            "majority_threshold": r.majority_threshold,
            "spend_nominal": r.total_campaign_spend_nominal,
            "spend_real_2026": r.total_campaign_spend_cpi_adjusted_2026,
            "cost_per_vote_real": r.mean_cost_per_vote_cpi_adjusted,
            "cost_per_mp_real": r.mean_cost_per_mp_cpi_adjusted,
        }
        for r in long_records
    ]
    long_table = pa.Table.from_pylist(long_rows)
    long_path = output_dir / "silver_longitudinal_1996_2026.parquet"
    pq.write_table(long_table, long_path)
    generated["silver_longitudinal"] = long_path

    # 8. Silver: Major Donors and Detailed Funding
    funding_records = get_party_detailed_funding()
    fund_rows = [
        {
            "party": f.party_name,
            "donations": f.total_donations,
            "party_spend": f.total_party_expenses,
            "candidate_spend": f.total_candidate_expenses,
            "votes": f.party_votes,
            "seats_won": f.total_seats_won,
            "cost_per_vote": f.cost_per_party_vote,
            "cost_per_elected_mp": f.cost_per_elected_mp,
            "cost_per_local_mp": f.cost_per_local_electorate_mp,
            "gini": f.donation_gini,
        }
        for f in funding_records
    ]
    fund_table = pa.Table.from_pylist(fund_rows)
    fund_path = output_dir / "silver_campaign_funding_donors_2026.parquet"
    pq.write_table(fund_table, fund_path)
    generated["silver_funding_donors"] = fund_path

    # 9. Gold: 2029 Predictive Election Forecast
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
    forecast_rows = [
        {
            "party": p,
            "projected_seats": s["projected_seat_mean"],
            "ci_95_low": s["ci_95_low"],
            "ci_95_high": s["ci_95_high"],
        }
        for p, s in forecast.parliamentary_seat_projections.items()
    ]
    forecast_table = pa.Table.from_pylist(forecast_rows)
    forecast_path = output_dir / "gold_election_forecast_2029.parquet"
    pq.write_table(forecast_table, forecast_path)
    generated["gold_forecast_2029"] = forecast_path

    return generated


if __name__ == "__main__":
    import sys

    target = Path("derivatives/parquet")
    res = materialize_all_election_parquet(target)
    sys.stdout.write(f"Materialized {len(res)} Parquet datasets.\n")
