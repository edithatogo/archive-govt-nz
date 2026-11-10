"""Statutory Sainte-Laguë seat allocation engine under the Electoral Act 1993 (NZ).

Implements the proportional allocation algorithm prescribed in Schedule 4 of the Act.
"""

from __future__ import annotations

from typing import Literal

from archive_govt_nz.domains.elections.contracts import (
    PartyAllocation,
    PartyVoteRow,
    SainteLagueResult,
)


def compute_sainte_lague(
    parties: list[PartyVoteRow],
    election_year: int = 2026,
    vintage: Literal["preliminary", "official"] = "preliminary",
    nominal_seats: int = 120,
    threshold_pct: float = 5.0,
    electorate_threshold: int = 1,
) -> SainteLagueResult:
    """Allocate nominal seats using the statutory Sainte-Laguë formula.

    Parameters
    ----------
    parties : list[PartyVoteRow]
        List of parties with party vote counts and electorate seats won.
    election_year : int
        Election year (e.g. 2026).
    vintage : {"preliminary", "official"}
        Result vintage.
    nominal_seats : int
        Standard Parliament baseline (120 seats).
    threshold_pct : float
        Party vote percentage hurdle (default 5.0%).
    electorate_threshold : int
        Electorate seats needed to waive the 5% threshold (default 1 seat).

    Returns
    -------
    SainteLagueResult
        Proportional seat entitlements and qualifications.

    """
    total_votes = sum(p.party_votes for p in parties)
    if total_votes == 0:
        raise ValueError("Total votes cannot be zero.")

    # 1. Evaluate qualification
    qualifying: list[PartyVoteRow] = []
    excluded: list[str] = []
    qual_reasons: dict[
        str, Literal["threshold_5_percent", "electorate_seat", "both"]
    ] = {}

    for p in parties:
        pct = (p.party_votes / total_votes) * 100.0
        crossed_threshold = pct >= threshold_pct
        won_electorate = p.electorate_seats_won >= electorate_threshold

        if crossed_threshold and won_electorate:
            qualifying.append(p)
            qual_reasons[p.party_name] = "both"
        elif crossed_threshold:
            qualifying.append(p)
            qual_reasons[p.party_name] = "threshold_5_percent"
        elif won_electorate:
            qualifying.append(p)
            qual_reasons[p.party_name] = "electorate_seat"
        else:
            excluded.append(p.party_name)

    # 2. Sainte-Laguë quotients iteration: divisor = 2s + 1 (1, 3, 5, 7, ...)
    seats_allocated: dict[str, int] = {p.party_name: 0 for p in qualifying}

    if qualifying:
        for _ in range(nominal_seats):
            # Find party with highest quotient
            best_party = None
            best_quotient = -1.0

            for p in qualifying:
                s = seats_allocated[p.party_name]
                quotient = p.party_votes / (2 * s + 1)
                # Deterministic tie-breaking: higher raw party votes wins tie
                if quotient > best_quotient or (
                    quotient == best_quotient
                    and best_party is not None
                    and p.party_votes
                    > next(
                        x.party_votes for x in qualifying if x.party_name == best_party
                    )
                ):
                    best_quotient = quotient
                    best_party = p.party_name

            if best_party is not None:
                seats_allocated[best_party] += 1

    # 3. Assemble PartyAllocation items
    allocations: list[PartyAllocation] = []
    for p in qualifying:
        entitlement = seats_allocated[p.party_name]
        elec_won = p.electorate_seats_won
        list_won = max(0, entitlement - elec_won)
        total = elec_won + list_won  # If elec_won > entitlement, overhang happens here

        allocations.append(
            PartyAllocation(
                party_name=p.party_name,
                qualification_reason=qual_reasons[p.party_name],
                party_vote=p.party_votes,
                proportional_entitlement=entitlement,
                electorate_seats=elec_won,
                list_seats=list_won,
                total_seats=total,
            )
        )

    # Sort allocations descending by total seats, then party vote
    allocations.sort(key=lambda a: (a.total_seats, a.party_vote), reverse=True)

    return SainteLagueResult(
        election_year=election_year,
        vintage=vintage,
        nominal_seats=nominal_seats,
        qualifying_parties=[p.party_name for p in qualifying],
        excluded_parties=excluded,
        allocations=allocations,
    )
