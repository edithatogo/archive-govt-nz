"""Tests for overhang calculation, House expansion, and majority thresholds."""

from archive_govt_nz.domains.elections.contracts import PartyVoteRow
from archive_govt_nz.domains.elections.overhang_calculator import (
    compute_overhang_analysis,
)
from archive_govt_nz.domains.elections.sainte_lague import compute_sainte_lague


def test_2026_preliminary_11_seat_overhang():
    # Synthetic 2026 stress scenario (NOT the official preliminary result).
    parties = [
        PartyVoteRow(
            party_name="National",
            party_votes=800000,
            party_vote_percentage=29.2,
            electorate_seats_won=43,
        ),
        PartyVoteRow(
            party_name="Labour",
            party_votes=680000,
            party_vote_percentage=24.8,
            electorate_seats_won=16,
        ),
        PartyVoteRow(
            party_name="Greens",
            party_votes=370000,
            party_vote_percentage=13.5,
            electorate_seats_won=3,
        ),
        PartyVoteRow(
            party_name="ACT",
            party_votes=280000,
            party_vote_percentage=10.2,
            electorate_seats_won=1,
        ),
        PartyVoteRow(
            party_name="NZ First",
            party_votes=240000,
            party_vote_percentage=8.8,
            electorate_seats_won=0,
        ),
        PartyVoteRow(
            party_name="TOP",
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
    alloc = compute_sainte_lague(parties, election_year=2026)
    analysis = compute_overhang_analysis(alloc)

    # National entitlement = 36, won 43 -> overhang = 7
    nat = next(d for d in analysis.overhang_details if d.party_name == "National")
    assert nat.overhang_seats == 7

    # Te Pāti Māori entitlement = 5, won 9 -> overhang = 4
    tpm = next(d for d in analysis.overhang_details if d.party_name == "Te Pāti Māori")
    assert tpm.overhang_seats == 4

    # Total Overhang = 11
    assert analysis.overhang_seats_total == 11
    # Total House expands to 131 seats
    assert analysis.total_house_seats == 131
    # Majority threshold = floor(131 / 2) + 1 = 66
    assert analysis.majority_threshold == 66


def test_historical_2005_overhang():
    # 2005 scenario: Māori Party 2.12% party vote, won 4 electorates, entitled to 3 -> 1 overhang (121 seats)
    parties = [
        PartyVoteRow(
            party_name="Labour",
            party_votes=935805,
            party_vote_percentage=41.1,
            electorate_seats_won=31,
        ),
        PartyVoteRow(
            party_name="National",
            party_votes=889373,
            party_vote_percentage=39.1,
            electorate_seats_won=31,
        ),
        PartyVoteRow(
            party_name="NZ First",
            party_votes=130115,
            party_vote_percentage=5.7,
            electorate_seats_won=0,
        ),
        PartyVoteRow(
            party_name="Green",
            party_votes=120521,
            party_vote_percentage=5.3,
            electorate_seats_won=0,
        ),
        PartyVoteRow(
            party_name="Māori Party",
            party_votes=48263,
            party_vote_percentage=2.1,
            electorate_seats_won=4,
        ),
        PartyVoteRow(
            party_name="ACT",
            party_votes=34469,
            party_vote_percentage=1.5,
            electorate_seats_won=1,
        ),
        PartyVoteRow(
            party_name="United Future",
            party_votes=60860,
            party_vote_percentage=2.7,
            electorate_seats_won=1,
        ),
    ]
    alloc = compute_sainte_lague(parties, election_year=2005)
    analysis = compute_overhang_analysis(alloc)

    mp = next(d for d in analysis.overhang_details if d.party_name == "Māori Party")
    assert mp.overhang_seats == 1
    assert analysis.total_house_seats == 121
    assert analysis.majority_threshold == 61


def test_disproportionality_includes_nonqualifying_parties():
    """Excluded party votes must enter both nationwide indices as zero seats."""
    import math
    parties = [
        PartyVoteRow(party_name="A", party_votes=60_000, party_vote_percentage=60, electorate_seats_won=30),
        PartyVoteRow(party_name="B", party_votes=35_000, party_vote_percentage=35, electorate_seats_won=20),
        PartyVoteRow(party_name="C", party_votes=5_000, party_vote_percentage=5, electorate_seats_won=0),
    ]
    allocation = compute_sainte_lague(parties, nominal_seats=10, threshold_pct=6)
    result = compute_overhang_analysis(allocation)
    assert result.disproportionality_indices.loosemore_hanby_index == 5.0
    # Party A: 60% votes / 60% seats, B: 35% / 40%, C: 5% / 0%
    assert math.isclose(result.disproportionality_indices.gallagher_index, 5.0)
