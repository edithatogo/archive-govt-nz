"""Tests for campaign finance econometric causal inference and multivariate attribution."""

from archive_govt_nz.domains.elections.finance_causal_engine import (
    calculate_gini,
    compute_campaign_finance_attribution,
    run_rdd_spend_analysis,
)
from archive_govt_nz.domains.elections.multivariate_exploratory import (
    run_exploratory_multivariate_analysis,
)
from archive_govt_nz.domains.elections.special_votes_simulator import (
    simulate_special_votes,
)


def test_gini_calculation():
    # Equal distribution has Gini near 0
    assert calculate_gini([100.0, 100.0, 100.0, 100.0]) == 0.0
    # Skewed distribution has high Gini
    high_gini = calculate_gini([10.0, 20.0, 50.0, 50000.0])
    assert high_gini > 0.70


def test_rdd_spend_analysis():
    margins = [10.0, 50.0, -20.0, -60.0]
    spend_diffs = [12000.0, 15000.0, -8000.0, -11000.0]
    rdd = run_rdd_spend_analysis(margins, spend_diffs, bandwidth=100.0)
    assert rdd["bandwidth"] == 100.0
    assert "local_average_treatment_effect" in rdd
    assert rdd["p_value"] < 0.05


def test_campaign_finance_attribution():
    parties = [
        {
            "party_name": "National",
            "donations": 4000000.0,
            "expenses": 4500000.0,
            "party_votes": 732000,
        },
        {
            "party_name": "Labour",
            "donations": 3500000.0,
            "expenses": 3900000.0,
            "party_votes": 695000,
        },
    ]
    electorates = [
        {
            "electorate_name": "Nelson",
            "winner_spend": 28000.0,
            "runner_up_spend": 26500.0,
            "margin": 68,
        },
    ]
    attrib = compute_campaign_finance_attribution(parties, electorates, year=2026)
    assert attrib.election_year == 2026
    assert len(attrib.parties_finance) == 2
    assert attrib.parties_finance[0].cost_per_party_vote > 0


def test_multivariate_exploratory_and_shap():
    res = run_exploratory_multivariate_analysis([], year=2026)
    assert len(res.feature_matrix_variables) > 5
    assert "PC1_Generational_Housing" in res.pca_decomposition["factor_loadings"]
    assert "TOP" in res.shap_attribution["top_drivers_by_party"]
    assert res.elastic_net_drivers["renting_ratio"] > 0


def test_special_votes_monte_carlo():
    electorates = [
        {
            "electorate_name": "Nelson",
            "winner": "National",
            "runner_up": "Labour",
            "margin": 68,
            "total_votes": 36000,
        },
        {
            "electorate_name": "Te Tai Tokerau",
            "winner": "Labour",
            "runner_up": "Te Pāti Māori",
            "margin": 112,
            "total_votes": 28000,
        },
    ]
    sim = simulate_special_votes(electorates, iterations=1000, seed=123)
    assert sim.election_year == 2026
    assert len(sim.vulnerable_electorates) == 2
    # Nelson margin is only 68 votes with ~5k specials; should have high flip probability
    nelson = next(
        v for v in sim.vulnerable_electorates if v.electorate_name == "Nelson"
    )
    assert nelson.flip_probability > 0.50


def test_counterfactual_engine():
    from archive_govt_nz.domains.elections.contracts import PartyVoteRow
    from archive_govt_nz.domains.elections.counterfactual_engine import (
        run_counterfactual_2012_review_scenario,
        run_counterfactual_compulsory_voting,
    )

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
            party_name="The Opportunity Party (TOP)",
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

    res_2012 = run_counterfactual_2012_review_scenario(parties)
    assert res_2012["scenario"] == "2012_mmp_review_recommendations"
    assert res_2012["majority_threshold"] > 60

    res_comp = run_counterfactual_compulsory_voting(parties)
    assert res_comp["scenario"] == "compulsory_voting_95_percent_turnout"
    assert res_comp["total_house_seats"] >= 120
