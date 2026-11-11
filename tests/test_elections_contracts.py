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


def test_causal_overhang_attribution_contract():
    from archive_govt_nz.domains.elections.contracts import (
        BoothLevelSplitRecord,
        CausalOverhangAttribution,
        MaoriRollTransferShock,
        OverhangDriverContribution,
    )

    booth = BoothLevelSplitRecord(
        booth_id="BOOTH_AKL_01",
        electorate_name="Auckland Central",
        voting_place_address="Auckland Town Hall",
        total_candidate_votes=1450,
        total_party_votes=1480,
        candidate_votes_by_party={"Greens": 650, "Labour": 400, "National": 350},
        party_votes_by_party={
            "Greens": 520,
            "Labour": 410,
            "National": 320,
            "TOP": 120,
        },
        split_differential={"Greens": 0.088, "Labour": -0.007, "National": 0.020},
        advance_voting=True,
    )
    assert booth.booth_id == "BOOTH_AKL_01"
    assert booth.split_differential["Greens"] == 0.088

    shock = MaoriRollTransferShock(
        electorate_name="Te Tai Hauāuru",
        electorate_type="maori",
        pre_reform_roll_2023=35400,
        post_reform_roll_2026=41200,
        net_transfers_onto_maori_roll=5800,
        pct_roll_expansion=0.1638,
        tpm_candidate_margin_shift=0.142,
        iv_z_eligibility=1.0,
    )
    assert shock.net_transfers_onto_maori_roll == 5800

    attr = CausalOverhangAttribution(
        analysis_timestamp=datetime.now(UTC),
        total_overhang_seats=11,
        national_overhang_seats=7,
        tpm_overhang_seats=4,
        oaxaca_blinder_decomposition={
            "split_ticket_voting": 5.0,
            "minor_party_siphon_denominator": 3.3,
            "incumbency_buffer": 1.5,
            "maori_roll_switch_shock": 2.4,
            "unexplained_residual": -1.2,
        },
        rdd_incumbency_lates={"late_estimate": 0.042, "p_value": 0.018},
        iv_maori_roll_estimates={"first_stage_f_stat": 28.4, "tpm_margin_beta": 0.142},
        shapley_seat_attributions=[
            OverhangDriverContribution(
                driver_id="split_voting_decoupling",
                driver_name="Candidate vs Party Vote Decoupling",
                methodology="shapley_additive_attribution",
                seats_attributed_national=3.8,
                seats_attributed_tpm=1.2,
                total_seats_attributed=5.0,
                confidence_interval_95=[4.2, 5.8],
                p_value=0.001,
                causal_interpretation="Voters split tickets to express coalition preference.",
            ),
            OverhangDriverContribution(
                driver_id="minor_party_siphon_denominator",
                driver_name="Minor Party 5% Clearence Denominator Compression",
                methodology="shapley_additive_attribution",
                seats_attributed_national=2.1,
                seats_attributed_tpm=0.3,
                total_seats_attributed=2.4,
                confidence_interval_95=[1.8, 3.0],
                p_value=0.004,
                causal_interpretation="41.4% third party vote depressed National list ceiling.",
            ),
            OverhangDriverContribution(
                driver_id="maori_roll_switch_shock",
                driver_name="Continuous Māori Roll Transfer Law Shock",
                methodology="instrumental_variables_2sls",
                seats_attributed_national=0.0,
                seats_attributed_tpm=2.1,
                total_seats_attributed=2.1,
                confidence_interval_95=[1.6, 2.6],
                p_value=0.0005,
                causal_interpretation="Net transfer of high-propensity voters onto Māori roll.",
            ),
            OverhangDriverContribution(
                driver_id="incumbency_candidate_brand",
                driver_name="Causal Incumbency Officeholder Treatment",
                methodology="sharp_rdd",
                seats_attributed_national=1.1,
                seats_attributed_tpm=0.4,
                total_seats_attributed=1.5,
                confidence_interval_95=[0.8, 2.2],
                p_value=0.015,
                causal_interpretation="2023 wave incumbency insulated local electorate MPs.",
            ),
        ],
        total_attributed_sum=11.0,
        unexplained_residual_seats=0.0,
        counterfactual_review_2012={
            "seats_with_4pct_threshold": 127,
            "overhang_with_compensatory_seats": 0,
        },
    )
    assert attr.total_overhang_seats == 11
    assert len(attr.shapley_seat_attributions) == 4
    assert sum(s.total_seats_attributed for s in attr.shapley_seat_attributions) == 11.0
