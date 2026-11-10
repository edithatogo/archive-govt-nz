"""Tests for statutory Sainte-Laguë seat allocation."""

from archive_govt_nz.domains.elections.contracts import PartyVoteRow
from archive_govt_nz.domains.elections.sainte_lague import compute_sainte_lague


def test_sainte_lague_standard_120():
    # Simple two party scenario
    parties = [
        PartyVoteRow(
            party_name="Party A",
            party_votes=60000,
            party_vote_percentage=60.0,
            electorate_seats_won=30,
        ),
        PartyVoteRow(
            party_name="Party B",
            party_votes=40000,
            party_vote_percentage=40.0,
            electorate_seats_won=20,
        ),
    ]
    res = compute_sainte_lague(parties, nominal_seats=120)
    assert len(res.allocations) == 2
    # 60% of 120 = 72, 40% of 120 = 48
    a_alloc = next(a for a in res.allocations if a.party_name == "Party A")
    b_alloc = next(a for a in res.allocations if a.party_name == "Party B")
    assert a_alloc.proportional_entitlement == 72
    assert b_alloc.proportional_entitlement == 48
    assert a_alloc.list_seats == 42
    assert b_alloc.list_seats == 28


def test_sainte_lague_5_percent_threshold_exclusion():
    # Party below 5% with 0 electorate seats gets excluded
    parties = [
        PartyVoteRow(
            party_name="Big Party",
            party_votes=96000,
            party_vote_percentage=96.0,
            electorate_seats_won=50,
        ),
        PartyVoteRow(
            party_name="Tiny Party",
            party_votes=4000,
            party_vote_percentage=4.0,
            electorate_seats_won=0,
        ),
    ]
    res = compute_sainte_lague(parties, nominal_seats=120)
    assert "Tiny Party" in res.excluded_parties
    big = next(a for a in res.allocations if a.party_name == "Big Party")
    assert big.total_seats == 120


def test_sainte_lague_coat_tail_exemption():
    # Party below 5% but winning 1 electorate qualifies for list allocation
    parties = [
        PartyVoteRow(
            party_name="Major Party",
            party_votes=96000,
            party_vote_percentage=96.0,
            electorate_seats_won=50,
        ),
        PartyVoteRow(
            party_name="CoatTail Party",
            party_votes=4000,
            party_vote_percentage=4.0,
            electorate_seats_won=1,
        ),
    ]
    res = compute_sainte_lague(parties, nominal_seats=120)
    assert "CoatTail Party" in res.qualifying_parties
    ct = next(a for a in res.allocations if a.party_name == "CoatTail Party")
    assert ct.proportional_entitlement == 5
    assert ct.electorate_seats == 1
    assert ct.list_seats == 4
