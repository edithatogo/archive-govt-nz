"""Reproducible deterministic NZ MMP majority-coalition arithmetic tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from archive_govt_nz.domains.elections.coalition_arithmetic import (
    analyse_coalition_arithmetic,
)


@pytest.mark.parametrize(
    ("seats", "house_size"),
    [
        ({}, 0),
        ({"A": 3}, 0),
        ({"A": 2, "B": 1}, 4),
        ({"A": -1, "B": 2}, 1),
        ({"A": True, "B": 1}, 2),
        ({"A": 1.0, "B": 1}, 2),
        ({"": 1}, 1),
        ({" A ": 1}, 1),
        ({"A": 0}, 0),
    ],
)
def test_rejects_invalid_or_unreconciled_house(
    seats: dict[str, int], house_size: int
) -> None:
    """No arithmetic output from invalid seats, missing MPs or fake counts."""
    with pytest.raises(ValueError):
        analyse_coalition_arithmetic(seats, house_size=house_size)


def test_exact_minimal_winning_coalitions_and_surpluses() -> None:
    """Exclude nonminimal supersets, retain only critical-member coalitions."""
    report = analyse_coalition_arithmetic({"A": 5, "B": 3, "C": 2}, house_size=10)
    assert report.house_seats == 10
    assert report.majority_threshold == 6
    assert [c.parties for c in report.minimal_winning] == [
        ("A", "C"),
        ("A", "B"),
    ]
    assert [c.seats for c in report.minimal_winning] == [7, 8]
    assert [c.surplus_seats for c in report.minimal_winning] == [1, 2]


def test_zero_seat_parties_cannot_make_coalitions_and_input_order_independent() -> None:
    """Zero-seat parties are excluded, not invented as voting power."""
    one = analyse_coalition_arithmetic(
        {"B": 3, "Zero": 0, "A": 5, "C": 2}, house_size=10
    )
    two = analyse_coalition_arithmetic(
        {"C": 2, "A": 5, "B": 3, "Zero": 0}, house_size=10
    )
    assert one == two
    assert all("Zero" not in c.parties for c in one.minimal_winning)


def test_single_party_majority_is_minimal() -> None:
    """Do not require a fictitious coalition partner for a majority party."""
    report = analyse_coalition_arithmetic({"A": 6, "B": 2, "C": 2}, house_size=10)
    assert tuple(c.parties for c in report.minimal_winning) == (("A",),)
    assert report.minimal_winning[0].surplus_seats == 0


def test_even_and_odd_house_majority_rules() -> None:
    """Quota is floor(house/2)+1, never merely half the chamber."""
    even_house = analyse_coalition_arithmetic({"A": 61, "B": 59}, house_size=120)
    odd_house = analyse_coalition_arithmetic({"A": 61, "B": 60}, house_size=121)
    assert even_house.majority_threshold == 61
    assert odd_house.majority_threshold == 61


def test_preliminary_2026_frozen_fixture_right_bloc_is_arithmetic_only() -> None:
    """The exact fixture's 67-seat combination is mathematically minimal winning."""
    fixture = (
        Path(__file__).resolve().parents[1]
        / "spaces/nz-election-explorer/data/2026-preliminary.json"
    )
    data = json.loads(fixture.read_text(encoding="utf-8"))
    assert data["vintage"] == "preliminary"
    counts = {p["name"]: p["total_seats"] for p in data["parties"]}
    report = analyse_coalition_arithmetic(counts, house_size=data["total_seats"])
    assert report.majority_threshold == data["majority"] == 66
    right = frozenset({"National Party", "ACT New Zealand", "New Zealand First Party"})
    coalitions = {frozenset(c.parties): c for c in report.minimal_winning}
    assert coalitions[right].seats == 67
    assert coalitions[right].surplus_seats == 1
    assert sum(counts.values()) == data["total_seats"] == 131


def test_exhaustive_subset_bound_rejects_unreasonable_party_count() -> None:
    """Enumeration is explicitly bounded rather than unbounded exponential work."""
    party_seats = {f"Party {i}": 1 for i in range(17)}
    with pytest.raises(ValueError, match="Too many parliamentary parties"):
        analyse_coalition_arithmetic(party_seats, house_size=17)
