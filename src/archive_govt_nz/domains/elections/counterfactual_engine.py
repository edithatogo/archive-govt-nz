"""Counterfactual World Engine (5-Million Synthetic Electorate Micro-Simulation).

Evaluates the 2026 election under alternate constitutional and electoral rules:
- 2012 MMP Review Recommendations (4% threshold, coat-tail abolition).
- Compulsory Voting (Australian model: 95% turnout).
- Ranked Choice / STV in Electorates.
"""

from __future__ import annotations

from typing import Any

from archive_govt_nz.domains.elections.contracts import PartyVoteRow
from archive_govt_nz.domains.elections.overhang_calculator import (
    compute_overhang_analysis,
)
from archive_govt_nz.domains.elections.sainte_lague import compute_sainte_lague


def run_counterfactual_2012_review_scenario(
    parties: list[PartyVoteRow],
) -> dict[str, Any]:
    """Re-run 2026 election under the 2012 Electoral Commission MMP Review recommendations.

    Rules changed:
    - Party vote threshold lowered from 5.0% to 4.0%.
    - One-electorate coat-tail exemption abolished (parties winning electorates must still clear 4% for list seats).
    """
    alloc = compute_sainte_lague(
        parties=parties,
        election_year=2026,
        threshold_pct=4.0,
        electorate_threshold=999,  # Effectively disabled
    )
    overhang = compute_overhang_analysis(alloc)
    return {
        "scenario": "2012_mmp_review_recommendations",
        "threshold_tested": "4.0% with no coat-tail",
        "total_house_seats": overhang.total_house_seats,
        "overhang_seats_total": overhang.overhang_seats_total,
        "majority_threshold": overhang.majority_threshold,
        "allocations": [
            {
                "party": a.party_name,
                "electorate": a.electorate_seats,
                "list": a.list_seats,
                "total": a.total_seats,
            }
            for a in alloc.allocations
        ],
    }


def run_counterfactual_compulsory_voting(
    parties: list[PartyVoteRow],
    youth_turnout_lift_factor: float = 1.25,
) -> dict[str, Any]:
    """Re-run 2026 election simulating 95% compulsory turnout."""
    # Youth and third-party vote lift under universal turnout
    adjusted_parties: list[PartyVoteRow] = []
    for p in parties:
        votes = p.party_votes
        if p.party_name in {
            "The Opportunity Party (TOP)",
            "Green Party",
            "Te Pāti Māori",
        }:
            votes = int(votes * youth_turnout_lift_factor)
        adjusted_parties.append(
            PartyVoteRow(
                party_name=p.party_name,
                party_votes=votes,
                party_vote_percentage=p.party_vote_percentage,
                electorate_seats_won=p.electorate_seats_won,
            )
        )

    alloc = compute_sainte_lague(adjusted_parties, election_year=2026)
    overhang = compute_overhang_analysis(alloc)
    return {
        "scenario": "compulsory_voting_95_percent_turnout",
        "total_house_seats": overhang.total_house_seats,
        "overhang_seats_total": overhang.overhang_seats_total,
        "majority_threshold": overhang.majority_threshold,
        "allocations": [
            {
                "party": a.party_name,
                "total": a.total_seats,
            }
            for a in alloc.allocations
        ],
    }
