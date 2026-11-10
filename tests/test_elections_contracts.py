"""Tests for election data contracts and Pydantic validation."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from archive_govt_nz.domains.elections.contracts import (
    ElectorateResultRow,
    PartyVoteRow,
    RawElectionResults,
)


def test_party_vote_row_valid():
    row = PartyVoteRow(
        party_name="National Party",
        party_votes=732000,
        party_vote_percentage=26.8,
        electorate_seats_won=43,
    )
    assert row.party_name == "National Party"
    assert row.electorate_seats_won == 43


def test_party_vote_row_invalid_percentage():
    with pytest.raises(ValidationError):
        PartyVoteRow(
            party_name="Bad Party",
            party_votes=100,
            party_vote_percentage=105.0,  # exceeds 100
        )


def test_electorate_result_row():
    row = ElectorateResultRow(
        electorate_name="Epsom",
        type="general",
        winning_candidate="David Seymour",
        winning_party="ACT New Zealand",
        margin=4500,
    )
    assert row.type == "general"
    assert row.margin == 4500


def test_raw_election_results_payload():
    payload = RawElectionResults(
        election_year=2026,
        vintage="preliminary",
        captured_at=datetime.now(UTC),
        total_votes_cast=2730000,
        special_votes_estimated=400000,
        special_votes_counted=False,
        parties=[
            PartyVoteRow(
                party_name="National",
                party_votes=732000,
                party_vote_percentage=26.8,
                electorate_seats_won=43,
            ),
            PartyVoteRow(
                party_name="Labour",
                party_votes=695000,
                party_vote_percentage=25.4,
                electorate_seats_won=16,
            ),
        ],
        electorates=[
            ElectorateResultRow(
                electorate_name="Epsom",
                type="general",
                winning_candidate="David Seymour",
                winning_party="ACT",
                margin=4500,
            )
        ],
    )
    assert payload.election_year == 2026
    assert payload.vintage == "preliminary"
    assert len(payload.parties) == 2
