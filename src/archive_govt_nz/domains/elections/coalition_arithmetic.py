"""Deterministic parliamentary coalition arithmetic, not political feasibility.

Uses one reconciled seat snapshot. No probabilities, coalition negotiation
assumptions, party-policy similarity or Electoral Commission source claims are
inferred by these pure functions. Publication requires separate vintage and
source-provenance checks.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations

MAX_ACTIVE_PARTIES = 16


@dataclass(frozen=True, slots=True)
class MinimalWinningCoalition:
    """A group in which every participating party is necessary for a majority."""

    parties: tuple[str, ...]
    seats: int
    surplus_seats: int


@dataclass(frozen=True, slots=True)
class CoalitionArithmetic:
    """Exact integer results for the supplied and internally reconciled House."""

    house_seats: int
    majority_threshold: int
    minimal_winning: tuple[MinimalWinningCoalition, ...]


def analyse_coalition_arithmetic(
    seat_counts: Mapping[str, int], *, house_size: int
) -> CoalitionArithmetic:
    """Enumerate minimal winning seat combinations from one complete snapshot.

    Every positive-seat party is eligible *arithmetically*, with no assumptions
    about its willingness to cooperate. Exclude zero-seat parties from combinations,
    but include their zero counts in the House reconciliation. Reject missing,
    negative, fractional or duplicated chamber seats rather than inventing MPs.

    Complexity is exponential in active parties; bound it before enumeration.
    """
    if (
        isinstance(house_size, bool)
        or not isinstance(house_size, int)
        or house_size <= 0
    ):
        msg = "House size must be a positive integer"
        raise ValueError(msg)
    if not isinstance(seat_counts, Mapping) or not seat_counts:
        msg = "Supply a complete named party-seat mapping"
        raise ValueError(msg)
    for party, seats in seat_counts.items():
        if not isinstance(party, str) or not party or party != party.strip():
            msg = "Party identifiers must be nonblank, unpadded names"
            raise ValueError(msg)
        if isinstance(seats, bool) or not isinstance(seats, int) or seats < 0:
            msg = "Seat counts must be nonnegative integers"
            raise ValueError(msg)
    if sum(seat_counts.values()) != house_size:
        msg = "All party seats must reconcile exactly to the House size"
        raise ValueError(msg)
    active = sorted(party for party, seats in seat_counts.items() if seats > 0)
    if len(active) > MAX_ACTIVE_PARTIES:
        msg = "Too many parliamentary parties for exhaustive enumeration"
        raise ValueError(msg)
    majority = house_size // 2 + 1
    minimal: list[MinimalWinningCoalition] = []
    for group_size in range(1, len(active) + 1):
        for parties in combinations(active, group_size):
            total = sum(seat_counts[party] for party in parties)
            if total < majority:
                continue
            if all(total - seat_counts[party] < majority for party in parties):
                minimal.append(
                    MinimalWinningCoalition(
                        parties=parties,
                        seats=total,
                        surplus_seats=total - majority,
                    )
                )
    minimal.sort(
        key=lambda group: (len(group.parties), group.surplus_seats, group.parties)
    )
    return CoalitionArithmetic(
        house_seats=house_size,
        majority_threshold=majority,
        minimal_winning=tuple(minimal),
    )
