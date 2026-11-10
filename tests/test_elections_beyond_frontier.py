"""Unit and contract tests for the 5 beyond-frontier methodologies."""

from __future__ import annotations

import pytest

from archive_govt_nz.domains.elections.beyond_frontier_engine import (
    compute_neural_manifold_landscape,
    simulate_autonomous_multiagent_parliament,
    simulate_quantum_superposition_qubits,
    simulate_wetware_slime_mould,
    synthesize_psychoacoustic_sonification,
)


def test_wetware_slime_mould_simulation():
    sim = simulate_wetware_slime_mould()
    assert sim.organism == "Physarum polycephalum"
    assert len(sim.chemo_attractant_nodes) >= 12
    assert 0.0 < sim.vein_network_density <= 1.0
    assert len(sim.coalition_fusion_zones) >= 2


def test_psychoacoustic_sonification():
    sono = synthesize_psychoacoustic_sonification()
    assert len(sono.fundamental_frequencies_hz) == 7
    assert sono.fundamental_frequencies_hz["National"] == 220.0
    assert 0.5 < sono.chord_dissonance_score < 1.0
    assert sono.ultrasonic_radiation_pressure_pa > 0
    assert "Grand Duopoly Coalition (National + Labour)" in sono.coalition_haptic_friction


def test_neural_manifold_landscape():
    latent = compute_neural_manifold_landscape()
    assert latent.n_features == 12
    assert latent.explained_variance_ratio > 0.70
    assert len(latent.electorate_coordinates) >= 6
    # Verify Wellington Central and Napier / Hawke's Bay are co-located in latent protest space
    wlg = next(e for e in latent.electorate_coordinates if e["name"] == "Wellington Central")
    hb = next(e for e in latent.electorate_coordinates if "Hawke's Bay" in e["name"])
    dist = ((wlg["latent_x"] - hb["latent_x"]) ** 2 + (wlg["latent_y"] - hb["latent_y"]) ** 2) ** 0.5
    assert dist < 0.3  # Very close in AI latent space despite demographic differences


def test_quantum_superposition_qubits():
    q = simulate_quantum_superposition_qubits()
    assert q.n_qubits == 4
    assert q.bell_state_fidelity > 0.90
    assert len(q.density_matrix_real) == 4
    # Check probabilities sum approximately to 1
    p_hold = q.measurement_collapse_probabilities["Qubit 0 |0> Incumbent Hold (National)"]
    p_flip = q.measurement_collapse_probabilities["Qubit 0 |1> Superposition Collapse to Challenger (Labour)"]
    assert pytest.approx(p_hold + p_flip, rel=1e-2) == 1.0


def test_autonomous_multiagent_parliament():
    parl = simulate_autonomous_multiagent_parliament()
    assert parl.total_agents == 131
    assert sum(parl.seat_distribution.values()) == 131
    assert parl.majority_threshold == 66
    assert len(parl.active_bills) >= 4
    assert parl.agent_whip_defiance_rates["National"] > 0.10
    assert parl.agent_whip_defiance_rates["TOP"] == 0.0
