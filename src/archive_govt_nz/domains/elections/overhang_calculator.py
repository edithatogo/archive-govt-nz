"""Overhang analysis, Parliament expansion, and disproportionality metrics.

Calculates overhang seats under New Zealand MMP and measures divergence from pure proportionality.
"""

from __future__ import annotations

import math

from archive_govt_nz.domains.elections.contracts import (
    DisproportionalityIndices,
    OverhangAnalysis,
    PartyOverhangDetail,
)
from archive_govt_nz.domains.elections.sainte_lague import SainteLagueResult


def compute_overhang_analysis(
    allocation_result: SainteLagueResult,
    total_votes_cast: int | None = None,
) -> OverhangAnalysis:
    """Analyze overhang seats, expanded Parliament size, and disproportionality.

    Parameters
    ----------
    allocation_result : SainteLagueResult
        Result from compute_sainte_lague.
    total_votes_cast : int, optional
        Total votes cast across all parties (including non-qualifying). If omitted,
        sums votes of qualifying parties.

    Returns
    -------
    OverhangAnalysis
        Detailed overhang breakdown, expanded House size, and Gallagher index.

    """
    allocations = allocation_result.allocations
    excluded_votes = allocation_result.excluded_party_votes
    complete_total = sum(a.party_vote for a in allocations) + sum(excluded_votes.values())
    tot_votes = complete_total if total_votes_cast is None else total_votes_cast
    if tot_votes <= 0 or tot_votes != complete_total:
        raise ValueError('Valid vote total must match qualifying and excluded party votes')

    overhang_details: list[PartyOverhangDetail] = []
    total_overhang_seats = 0

    for a in allocations:
        overhang = max(0, a.electorate_seats - a.proportional_entitlement)
        total_overhang_seats += overhang

    # Expanded House size
    expanded_house = allocation_result.nominal_seats + total_overhang_seats
    majority_threshold = math.floor(expanded_house / 2) + 1

    # Disproportionality calculations
    sum_sq_diff = 0.0
    sum_abs_diff = 0.0

    for a in allocations:
        actual_seats = a.total_seats
        seat_share = (
            (actual_seats / expanded_house) * 100.0 if expanded_house > 0 else 0.0
        )
        vote_share = (a.party_vote / tot_votes) * 100.0 if tot_votes > 0 else 0.0

        diff = seat_share - vote_share
        sum_sq_diff += diff**2
        sum_abs_diff += abs(diff)

        overhang = max(0, a.electorate_seats - a.proportional_entitlement)
        overhang_details.append(
            PartyOverhangDetail(
                party_name=a.party_name,
                proportional_entitlement=a.proportional_entitlement,
                electorate_seats_won=a.electorate_seats,
                overhang_seats=overhang,
                seat_share_percentage=round(seat_share, 2),
                vote_share_percentage=round(vote_share, 2),
            )
        )

    # Excluded parties have zero seats but their vote shares enter both indices.
    for votes in excluded_votes.values():
        vote_share = votes * 100.0 / tot_votes
        sum_sq_diff += vote_share ** 2
        sum_abs_diff += vote_share

    # Gallagher Index: sqrt(0.5 * sum((V_i - S_i)^2))
    gallagher = math.sqrt(0.5 * sum_sq_diff)
    # Loosemore-Hanby Index: 0.5 * sum(|V_i - S_i|)
    loosemore_hanby = 0.5 * sum_abs_diff

    return OverhangAnalysis(
        election_year=allocation_result.election_year,
        vintage=allocation_result.vintage,
        nominal_seats=allocation_result.nominal_seats,
        total_house_seats=expanded_house,
        overhang_seats_total=total_overhang_seats,
        majority_threshold=majority_threshold,
        overhang_details=overhang_details,
        disproportionality_indices=DisproportionalityIndices(
            gallagher_index=round(gallagher, 3),
            loosemore_hanby_index=round(loosemore_hanby, 3),
        ),
    )
