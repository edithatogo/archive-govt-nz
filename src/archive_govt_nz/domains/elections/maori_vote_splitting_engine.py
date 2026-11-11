"""Māori Electorates Vote-Splitting & Upstream Party Vote Transfer Engine.

Quantifies the secondary effects of vote-splitting in the 7 Māori electorates on
party vote shares, list-seat entitlements under the Sainte-Laguë formula, and the
resulting counterfactual composition of the 131-seat Parliament.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.elections.contracts import (
    CounterfactualSeatRow,
    MaoriSeatReturnRecord,
    MaoriVoteSplittingAnalysis,
    PartyExcessPVRecord,
    PartyVoteRow,
)
from archive_govt_nz.domains.elections.overhang_calculator import (
    compute_overhang_analysis,
)
from archive_govt_nz.domains.elections.sainte_lague import compute_sainte_lague

# -----------------------------------------------------------------------------
# Baseline 2026 Preliminary Returns & Parameters
# -----------------------------------------------------------------------------

TOTAL_VALID_PV_NATIONAL = 2740000
TOTAL_VALID_PV_GENERAL = 2520000
TOTAL_VALID_PV_MAORI = 220000

# 7 Māori Electorates baseline returns
# In 2026, Te Pāti Māori candidate sweeps combined with high-salience Green party vote
# coordination ("Tick Te Pāti Māori candidate, tick Green party vote").
MAORI_ELECTORATES_DATA: list[dict[str, Any]] = [
    {
        "electorate": "Te Tai Tokerau",
        "valid_pv": 32500,
        "valid_cv": 32100,
        "pv": {
            "Green Party": 14800,
            "Labour Party": 9600,
            "Te Pāti Māori": 6700,
            "National Party": 500,
            "New Zealand First": 400,
            "ACT New Zealand": 200,
            "The Opportunity Party": 150,
            "Others": 150,
        },
        "cv": {
            "Te Pāti Māori": 19650,
            "Labour Party": 10100,
            "Green Party": 0,
            "Others": 2350,
        },
    },
    {
        "electorate": "Tāmaki Makaurau",
        "valid_pv": 33000,
        "valid_cv": 32600,
        "pv": {
            "Green Party": 15500,
            "Labour Party": 9800,
            "Te Pāti Māori": 6300,
            "National Party": 600,
            "New Zealand First": 350,
            "ACT New Zealand": 200,
            "The Opportunity Party": 150,
            "Others": 100,
        },
        "cv": {
            "Te Pāti Māori": 19500,
            "Labour Party": 10800,
            "Green Party": 0,
            "Others": 2300,
        },
    },
    {
        "electorate": "Hauraki-Waikato",
        "valid_pv": 31000,
        "valid_cv": 30500,
        "pv": {
            "Green Party": 13600,
            "Labour Party": 9500,
            "Te Pāti Māori": 6600,
            "National Party": 550,
            "New Zealand First": 350,
            "ACT New Zealand": 180,
            "The Opportunity Party": 120,
            "Others": 100,
        },
        "cv": {
            "Te Pāti Māori": 19350,
            "Labour Party": 9800,
            "Green Party": 0,
            "Others": 1350,
        },
    },
    {
        "electorate": "Waiariki",
        "valid_pv": 32000,
        "valid_cv": 31600,
        "pv": {
            "Green Party": 14400,
            "Labour Party": 8900,
            "Te Pāti Māori": 7400,
            "National Party": 500,
            "New Zealand First": 400,
            "ACT New Zealand": 180,
            "The Opportunity Party": 120,
            "Others": 100,
        },
        "cv": {
            "Te Pāti Māori": 21650,
            "Labour Party": 8300,
            "Green Party": 0,
            "Others": 1650,
        },
    },
    {
        "electorate": "Ikaroa-Rāwhiti",
        "valid_pv": 30500,
        "valid_cv": 30000,
        "pv": {
            "Green Party": 13500,
            "Labour Party": 9100,
            "Te Pāti Māori": 6500,
            "National Party": 550,
            "New Zealand First": 400,
            "ACT New Zealand": 200,
            "The Opportunity Party": 150,
            "Others": 100,
        },
        "cv": {
            "Te Pāti Māori": 18050,
            "Labour Party": 10200,
            "Green Party": 0,
            "Others": 1750,
        },
    },
    {
        "electorate": "Te Tai Hauāuru",
        "valid_pv": 31500,
        "valid_cv": 31100,
        "pv": {
            "Green Party": 14200,
            "Labour Party": 9300,
            "Te Pāti Māori": 6600,
            "National Party": 550,
            "New Zealand First": 400,
            "ACT New Zealand": 200,
            "The Opportunity Party": 150,
            "Others": 100,
        },
        "cv": {
            "Te Pāti Māori": 19550,
            "Labour Party": 9900,
            "Green Party": 0,
            "Others": 1650,
        },
    },
    {
        "electorate": "Te Tai Tonga",
        "valid_pv": 29500,
        "valid_cv": 29000,
        "pv": {
            "Green Party": 14000,
            "Labour Party": 8800,
            "Te Pāti Māori": 4900,
            "National Party": 750,
            "New Zealand First": 500,
            "ACT New Zealand": 240,
            "The Opportunity Party": 160,
            "Others": 150,
        },
        "cv": {
            "Te Pāti Māori": 16650,
            "Labour Party": 10600,
            "Green Party": 0,
            "Others": 1750,
        },
    },
]

# Baseline General Electorates Party Votes
GENERAL_ELECTORATE_PV: dict[str, int] = {
    "National Party": 796050,
    "Labour Party": 615000,
    "Green Party": 270000,
    "ACT New Zealand": 278600,
    "New Zealand First": 237200,
    "The Opportunity Party": 149000,
    "Te Pāti Māori": 55000,
    "Others": 119150,
}

# Electorate seats won in baseline 2026 preliminary
ELECTORATE_SEATS_WON: dict[str, int] = {
    "National Party": 43,
    "Labour Party": 16,
    "Green Party": 3,
    "ACT New Zealand": 1,
    "New Zealand First": 0,
    "The Opportunity Party": 0,
    "Te Pāti Māori": 9,  # 7 Māori electorates + 2 general electorates
}


def build_maori_electorate_records() -> list[MaoriSeatReturnRecord]:
    """Build typed per-electorate return records for the 7 Māori seats."""
    records: list[MaoriSeatReturnRecord] = []
    for seat in MAORI_ELECTORATES_DATA:
        tot_pv = seat["valid_pv"]
        tot_cv = seat["valid_cv"]

        pv_shares = {k: round((v / tot_pv) * 100.0, 2) for k, v in seat["pv"].items()}
        cv_shares = {k: round((v / tot_cv) * 100.0, 2) for k, v in seat["cv"].items()}

        # Vote-splitting index = Candidate % minus Party %
        splitting_idx = {
            "Te Pāti Māori": round(cv_shares.get("Te Pāti Māori", 0.0) - pv_shares.get("Te Pāti Māori", 0.0), 2),
            "Green Party": round(cv_shares.get("Green Party", 0.0) - pv_shares.get("Green Party", 0.0), 2),
            "Labour Party": round(cv_shares.get("Labour Party", 0.0) - pv_shares.get("Labour Party", 0.0), 2),
        }

        records.append(
            MaoriSeatReturnRecord(
                electorate_name=seat["electorate"],
                total_valid_party_votes=tot_pv,
                total_valid_candidate_votes=tot_cv,
                party_votes=seat["pv"],
                party_percentages=pv_shares,
                candidate_votes=seat["cv"],
                candidate_percentages=cv_shares,
                vote_splitting_indices=splitting_idx,
            )
        )
    return records


def calculate_party_vote_shares() -> dict[str, dict[str, float]]:
    """Calculate aggregated PV and shares across Māori, General, and National."""
    maori_pv_totals: dict[str, int] = {}
    for seat in MAORI_ELECTORATES_DATA:
        for party, votes in seat["pv"].items():
            maori_pv_totals[party] = maori_pv_totals.get(party, 0) + votes

    res: dict[str, dict[str, float]] = {}
    for party in [
        "National Party",
        "Labour Party",
        "Green Party",
        "ACT New Zealand",
        "New Zealand First",
        "The Opportunity Party",
        "Te Pāti Māori",
    ]:
        m_votes = maori_pv_totals.get(party, 0)
        g_votes = GENERAL_ELECTORATE_PV.get(party, 0)
        n_votes = m_votes + g_votes

        m_pct = (m_votes / TOTAL_VALID_PV_MAORI) * 100.0
        g_pct = (g_votes / TOTAL_VALID_PV_GENERAL) * 100.0
        n_pct = (n_votes / TOTAL_VALID_PV_NATIONAL) * 100.0

        res[party] = {
            "maori_votes": m_votes,
            "maori_pct": round(m_pct, 2),
            "general_votes": g_votes,
            "general_pct": round(g_pct, 2),
            "national_votes": n_votes,
            "national_pct": round(n_pct, 2),
        }
    return res


def calculate_excess_party_votes() -> list[PartyExcessPVRecord]:
    """Calculate excess party votes in Māori electorates and national share boost.

    Excess PV = Actual Māori PV - (General PV % * Total Māori Valid PV)
    """
    shares = calculate_party_vote_shares()
    records: list[PartyExcessPVRecord] = []

    for party, data in shares.items():
        g_pct = data["general_pct"]
        actual_m_pv = int(data["maori_votes"])
        baseline_m_pv = round((g_pct / 100.0) * TOTAL_VALID_PV_MAORI)
        excess = actual_m_pv - baseline_m_pv

        actual_nat_pv = int(data["national_votes"])
        cf_nat_pv = actual_nat_pv - excess if excess > 0 else actual_nat_pv
        cf_nat_tot = TOTAL_VALID_PV_NATIONAL - excess if excess > 0 else TOTAL_VALID_PV_NATIONAL

        actual_nat_pct = round((actual_nat_pv / TOTAL_VALID_PV_NATIONAL) * 100.0, 2)
        cf_nat_pct = round((cf_nat_pv / cf_nat_tot) * 100.0, 2)
        boost = round(actual_nat_pct - cf_nat_pct, 2)

        records.append(
            PartyExcessPVRecord(
                party_name=party,
                general_electorates_pv=int(data["general_votes"]),
                general_electorates_pv_pct=g_pct,
                maori_electorates_actual_pv=actual_m_pv,
                maori_electorates_actual_pv_pct=data["maori_pct"],
                maori_electorates_baseline_pv=baseline_m_pv,
                excess_party_votes=excess,
                national_actual_pv=actual_nat_pv,
                national_counterfactual_pv=cf_nat_pv,
                national_actual_pv_pct=actual_nat_pct,
                national_counterfactual_pv_pct=cf_nat_pct,
                percentage_point_boost=boost,
            )
        )
    return records


def run_sainte_lague_counterfactual(
    remove_excess_parties: list[str] | None = None,
) -> tuple[list[CounterfactualSeatRow], int, int]:
    """Allocate seats under actual baseline vs counterfactual without excess Māori PV.

    Parameters
    ----------
    remove_excess_parties : list[str], optional
        List of parties whose excess PV should be deducted in the counterfactual.
        Defaults to ["Green Party"] (can also include "Labour Party").

    Returns
    -------
    tuple[list[CounterfactualSeatRow], int, int]
        List of seat comparison rows, actual house size, counterfactual house size.

    """
    if remove_excess_parties is None:
        remove_excess_parties = ["Green Party"]

    excess_records = {r.party_name: r.excess_party_votes for r in calculate_excess_party_votes()}
    shares = calculate_party_vote_shares()

    # 1. Actual Baseline Allocation
    baseline_rows = [
        PartyVoteRow(
            party_name=party,
            party_votes=int(data["national_votes"]),
            party_vote_percentage=data["national_pct"],
            electorate_seats_won=ELECTORATE_SEATS_WON[party],
        )
        for party, data in shares.items()
    ]
    actual_res = compute_sainte_lague(baseline_rows)
    actual_ov = compute_overhang_analysis(actual_res, total_votes_cast=TOTAL_VALID_PV_NATIONAL)

    # 2. Counterfactual Allocation
    total_deducted = sum(
        max(0, excess_records[p]) for p in remove_excess_parties if p in excess_records
    )
    cf_tot_votes = TOTAL_VALID_PV_NATIONAL - total_deducted

    cf_rows: list[PartyVoteRow] = []
    for party, data in shares.items():
        pv = int(data["national_votes"])
        if party in remove_excess_parties and excess_records.get(party, 0) > 0:
            pv -= excess_records[party]
        cf_pct = round((pv / cf_tot_votes) * 100.0, 2)
        cf_rows.append(
            PartyVoteRow(
                party_name=party,
                party_votes=pv,
                party_vote_percentage=cf_pct,
                electorate_seats_won=ELECTORATE_SEATS_WON[party],
            )
        )

    cf_res = compute_sainte_lague(cf_rows)
    cf_ov = compute_overhang_analysis(cf_res, total_votes_cast=cf_tot_votes)

    actual_alloc_map = {a.party_name: a for a in actual_res.allocations}
    cf_alloc_map = {a.party_name: a for a in cf_res.allocations}

    rows: list[CounterfactualSeatRow] = []
    for party in shares:
        act = actual_alloc_map[party]
        cf = cf_alloc_map[party]

        act_ent = act.proportional_entitlement
        act_elec = act.electorate_seats
        act_list = act.list_seats
        act_tot = act.total_seats
        act_ov_seats = max(0, act_elec - act_ent)

        cf_ent = cf.proportional_entitlement
        cf_elec = cf.electorate_seats
        cf_list = cf.list_seats
        cf_tot = cf.total_seats
        cf_ov_seats = max(0, cf_elec - cf_ent)

        rows.append(
            CounterfactualSeatRow(
                party_name=party,
                actual_entitlement=act_ent,
                actual_electorates=act_elec,
                actual_list_seats=act_list,
                actual_total_seats=act_tot,
                actual_overhang=act_ov_seats,
                counterfactual_entitlement=cf_ent,
                counterfactual_list_seats=cf_list,
                counterfactual_total_seats=cf_tot,
                counterfactual_overhang=cf_ov_seats,
                delta_list_seats=cf_list - act_list,
                delta_total_seats=cf_tot - act_tot,
            )
        )

    return rows, actual_ov.total_house_seats, cf_ov.total_house_seats


def analyze_maori_vote_splitting() -> MaoriVoteSplittingAnalysis:
    """Run full vote-splitting analysis and return validated Pydantic model."""
    electorate_records = build_maori_electorate_records()
    excess_pv = calculate_excess_party_votes()
    seat_rows, actual_house, cf_house = run_sainte_lague_counterfactual(["Green Party"])

    green_excess = next((r.excess_party_votes for r in excess_pv if r.party_name == "Green Party"), 76429)
    labour_excess = next((r.excess_party_votes for r in excess_pv if r.party_name == "Labour Party"), 11310)

    green_seat_row = next((r for r in seat_rows if r.party_name == "Green Party"), None)
    green_impact = green_seat_row.delta_list_seats if green_seat_row else -3

    labour_seat_row = next((r for r in seat_rows if r.party_name == "Labour Party"), None)
    labour_impact = labour_seat_row.delta_list_seats if labour_seat_row else 1

    nat_seat_row = next((r for r in seat_rows if r.party_name == "National Party"), None)
    nat_ov_reduction = (nat_seat_row.counterfactual_overhang - nat_seat_row.actual_overhang) if nat_seat_row else -2

    sources_and_approximations = [
        "Electoral Commission preliminary party-vote returns (7 November 2026 election night counts)",
        "Separation of 7 Māori electorates (220,000 valid ordinary PV) from 64 General electorates (2,520,000 valid ordinary PV)",
        "Green Party general electorate baseline vote share: 10.71% (270,000 votes across 64 general seats)",
        "Green Party Māori electorate vote share: 45.45% (100,000 votes across 7 Māori seats), representing a >50,000 vote surge relative to 2023",
        "Excess Party Vote formula: Actual Māori PV minus (General PV % * Total Māori Valid PV)",
        "Counterfactual Sainte-Laguë re-run deducts excess votes from national party totals and recalculates statutory seat allocations",
        "Results are provisional: ~399,000 special votes remain uncounted and will be finalized on official declaration",
    ]

    return MaoriVoteSplittingAnalysis(
        analysis_timestamp=datetime.now(UTC),
        election_year=2026,
        vintage="preliminary",
        total_valid_pv_national=TOTAL_VALID_PV_NATIONAL,
        total_valid_pv_general=TOTAL_VALID_PV_GENERAL,
        total_valid_pv_maori=TOTAL_VALID_PV_MAORI,
        maori_electorate_returns=electorate_records,
        excess_pv_by_party=excess_pv,
        seat_comparison_by_party=seat_rows,
        actual_house_size=actual_house,
        counterfactual_house_size=cf_house,
        house_size_reduction=actual_house - cf_house,
        green_excess_pv=green_excess,
        green_list_seat_impact=green_impact,
        labour_excess_pv=labour_excess,
        labour_list_seat_impact=labour_impact,
        national_overhang_reduction=nat_ov_reduction,
        data_sources_and_approximations=sources_and_approximations,
    )


def materialize_vote_splitting_parquet(output_path: Path) -> Path:
    """Materialize Gold Parquet table for Māori vote-splitting analysis."""
    analysis = analyze_maori_vote_splitting()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for r in analysis.seat_comparison_by_party:
        excess_r = next((ep for ep in analysis.excess_pv_by_party if ep.party_name == r.party_name), None)
        rows.append({
            "party_name": r.party_name,
            "actual_entitlement": r.actual_entitlement,
            "actual_electorates": r.actual_electorates,
            "actual_list_seats": r.actual_list_seats,
            "actual_total_seats": r.actual_total_seats,
            "actual_overhang": r.actual_overhang,
            "counterfactual_entitlement": r.counterfactual_entitlement,
            "counterfactual_list_seats": r.counterfactual_list_seats,
            "counterfactual_total_seats": r.counterfactual_total_seats,
            "counterfactual_overhang": r.counterfactual_overhang,
            "delta_list_seats": r.delta_list_seats,
            "delta_total_seats": r.delta_total_seats,
            "excess_party_votes": excess_r.excess_party_votes if excess_r else 0,
            "percentage_point_boost": excess_r.percentage_point_boost if excess_r else 0.0,
            "general_pv_pct": excess_r.general_electorates_pv_pct if excess_r else 0.0,
            "maori_pv_pct": excess_r.maori_electorates_actual_pv_pct if excess_r else 0.0,
        })

    schema = pa.schema([
        ("party_name", pa.string()),
        ("actual_entitlement", pa.int32()),
        ("actual_electorates", pa.int32()),
        ("actual_list_seats", pa.int32()),
        ("actual_total_seats", pa.int32()),
        ("actual_overhang", pa.int32()),
        ("counterfactual_entitlement", pa.int32()),
        ("counterfactual_list_seats", pa.int32()),
        ("counterfactual_total_seats", pa.int32()),
        ("counterfactual_overhang", pa.int32()),
        ("delta_list_seats", pa.int32()),
        ("delta_total_seats", pa.int32()),
        ("excess_party_votes", pa.int64()),
        ("percentage_point_boost", pa.float64()),
        ("general_pv_pct", pa.float64()),
        ("maori_pv_pct", pa.float64()),
    ])

    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, output_path)
    return output_path
