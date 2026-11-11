"""Metamorphic properties for the NZ MMP seat-allocation engine.

These are synthetic election scenarios, not published 2026 election data.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.domains.elections.contracts import PartyVoteRow
from archive_govt_nz.domains.elections.sainte_lague import compute_sainte_lague


def _scenario(votes_a: int, votes_b: int) -> list[PartyVoteRow]:
    total = votes_a + votes_b
    return [
        PartyVoteRow(
            party_name="Synthetic A",
            party_votes=votes_a,
            party_vote_percentage=100 * votes_a / total,
            electorate_seats_won=0,
        ),
        PartyVoteRow(
            party_name="Synthetic B",
            party_votes=votes_b,
            party_vote_percentage=100 * votes_b / total,
            electorate_seats_won=0,
        ),
    ]


@settings(max_examples=60, deadline=None)
@given(
    first=st.integers(min_value=1, max_value=1_000_000),
    second=st.integers(min_value=1, max_value=1_000_000),
    scale=st.integers(min_value=1, max_value=100),
)
def test_vote_scaling_preserves_seats(first: int, second: int, scale: int) -> None:
    """Multiplying every party vote by the same factor cannot change seats."""
    baseline = compute_sainte_lague(_scenario(first, second), threshold_pct=0.0)
    scaled = compute_sainte_lague(
        _scenario(first * scale, second * scale),
        threshold_pct=0.0,
    )
    before = {item.party_name: item.total_seats for item in baseline.allocations}
    after = {item.party_name: item.total_seats for item in scaled.allocations}
    assert before == after
    assert sum(before.values()) == 120


@settings(max_examples=60, deadline=None)
@given(
    first=st.integers(min_value=1, max_value=1_000_000),
    second=st.integers(min_value=1, max_value=1_000_000),
)
def test_allocation_conserves_nominal_seats(first: int, second: int) -> None:
    """Every allocated seat must be accounted for exactly once."""
    result = compute_sainte_lague(_scenario(first, second), threshold_pct=0.0)
    assert sum(item.proportional_entitlement for item in result.allocations) == 120
    assert all(item.list_seats >= 0 for item in result.allocations)
    assert all(item.total_seats == item.list_seats for item in result.allocations)
