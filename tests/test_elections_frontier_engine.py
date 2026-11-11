"""Unit and integration tests for the Frontier Visualization Engine & Strategic Recommendations."""

from __future__ import annotations

from pathlib import Path

from archive_govt_nz.domains.elections.frontier_engine import (
    compute_bayesian_polling_aggregation,
    compute_committee_shapley_shubik_power,
    compute_overhang_elasticity_net,
    compute_quantum_probability_field,
    compute_splintering_hypervolume,
    compute_zk_merkle_audit_proofs,
)
from archive_govt_nz.domains.elections.generate_frontier_and_recommendations import (
    generate_all_frontier_suite_complete,
)


def test_overhang_elasticity_net_calculation() -> None:
    """Verify that overhang elasticity net correctly calculates geometric stretch and strain."""
    res = compute_overhang_elasticity_net()
    assert res["total_house_seats"] == 131
    assert res["total_overhang_seats"] == 11
    assert res["expanded_effective_radius"] > res["statutory_baseline_radius"]

    nodes = {n["party"]: n for n in res["party_nodes"]}
    assert nodes["National"]["overhang"] == 7
    assert nodes["Te Pāti Māori"]["overhang"] == 4
    assert nodes["National"]["strain_energy_joules"] > 0
    assert nodes["Te Pāti Māori"]["strain_energy_joules"] > 0
    assert nodes["Labour"]["overhang"] == 0
    assert nodes["Labour"]["strain_energy_joules"] == 0


def test_quantum_probability_fields() -> None:
    """Verify continuous probability density fields and superposition state collapse."""
    res = compute_quantum_probability_field(
        special_votes_count=399000, rightward_decay_pp=-1.65
    )
    assert res["special_votes_total"] == 399000

    clouds = {c["electorate"]: c for c in res["superposition_clouds"]}
    # Nelson should collapse to Labour under -1.65 pp drift
    assert clouds["Nelson"]["state_status"] == "FLIPPED_TO_CHALLENGER"
    assert clouds["Nelson"]["flip_probability"] > 0.70
    assert clouds["Nelson"]["projected_official_margin"] < 0

    # Te Atatū should be held by Labour
    assert clouds["Te Atatū"]["state_status"] == "HELD_BY_INCUMBENT"
    assert clouds["Te Atatū"]["projected_official_margin"] > 0


def test_political_splintering_hypervolume() -> None:
    """Verify multi-dimensional political splintering metrics."""
    res = compute_splintering_hypervolume()
    assert res["total_third_party_share_pct"] == 41.4
    assert res["splinter_parties"]["TOP"]["seats"] == 7
    assert res["fragmentation_index_enp"] > 5.0


def test_committee_shapley_shubik_power() -> None:
    """Verify Shapley-Shubik pivotal voting power in a 131-seat chamber with a 66 quota."""
    res = compute_committee_shapley_shubik_power()
    assert res["parliament_size"] == 131
    assert res["majority_quota"] == 66
    assert res["single_mp_defection_margin"] == 1

    powers = res["power_indices"]
    # Sum of Shapley-Shubik indices across parties should approximately equal 1.0
    total_power = sum(p["shapley_shubik_power"] for p in powers.values())
    assert abs(total_power - 1.0) < 0.02


def test_bayesian_polling_aggregation() -> None:
    """Verify Bayesian Kalman dynamic linear model de-biasing."""
    res = compute_bayesian_polling_aggregation()
    assert len(res["pollsters_audited"]) == 4
    latent = res["debiased_latent_vote"]
    assert latent["National"] > 28.0
    assert latent["Labour"] > 24.0
    assert latent["TOP"] >= 5.0


def test_zk_merkle_provenance_audit() -> None:
    """Verify Merkle tree cryptographic root verification of polling sheets."""
    res = compute_zk_merkle_audit_proofs()
    assert res["leaf_count"] == 4
    assert len(res["leaf_hashes"]) == 4
    assert len(res["merkle_root"]) == 64
    assert res["audit_status"] == "CRYPTOGRAPHICALLY_VERIFIED"


def test_frontier_figures_suite_generation(tmp_path: Path) -> None:
    """Verify generation of all 9 frontier and recommendation figures."""
    figs = generate_all_frontier_suite_complete(tmp_path)
    assert len(figs) == 9
    for name, path in figs.items():
        assert path.exists(), f"Figure missing: {name}"
        assert path.stat().st_size > 1000, f"Figure too small: {name}"
