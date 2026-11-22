"""Unit and contract tests for the 5 beyond-frontier methodologies."""

from __future__ import annotations

import numpy as np
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
    assert (
        "Grand Duopoly Coalition (National + Labour)" in sono.coalition_haptic_friction
    )


def test_neural_manifold_landscape():
    latent = compute_neural_manifold_landscape()
    assert latent.n_features == 12
    assert latent.explained_variance_ratio > 0.70
    assert len(latent.electorate_coordinates) >= 6
    # Verify Wellington Central and Napier / Hawke's Bay are co-located in latent protest space
    wlg = next(
        e for e in latent.electorate_coordinates if e["name"] == "Wellington Central"
    )
    hb = next(e for e in latent.electorate_coordinates if "Hawke's Bay" in e["name"])
    dist = (
        (wlg["latent_x"] - hb["latent_x"]) ** 2
        + (wlg["latent_y"] - hb["latent_y"]) ** 2
    ) ** 0.5
    assert dist < 0.3  # Very close in AI latent space despite demographic differences


@pytest.mark.parametrize("embedding", [None, [], (np.zeros((72, 2)),)])
def test_neural_manifold_rejects_non_array_embedding(
    monkeypatch: pytest.MonkeyPatch, embedding: object
) -> None:
    """Unexpected reducer output must fail before coordinate mutation."""

    def fitted(_self: object, _features: np.ndarray) -> object:
        return embedding

    monkeypatch.setattr("umap.umap_.UMAP.fit_transform", fitted)
    with pytest.raises(TypeError, match="embedding must be a NumPy array"):
        compute_neural_manifold_landscape()


@pytest.mark.parametrize("shape", [(71, 2), (72, 3), (144,)])
def test_neural_manifold_rejects_wrong_embedding_shape(
    monkeypatch: pytest.MonkeyPatch, shape: tuple[int, ...]
) -> None:
    """Every electorate needs exactly two coordinates before anchors are applied."""
    embedding = np.zeros(shape)
    original = embedding.copy()

    def fitted(_self: object, _features: np.ndarray) -> np.ndarray:
        return embedding

    monkeypatch.setattr("umap.umap_.UMAP.fit_transform", fitted)
    with pytest.raises(ValueError, match="two-dimensional row per electorate"):
        compute_neural_manifold_landscape()
    np.testing.assert_array_equal(embedding, original)


@pytest.mark.parametrize("fallback", [False, True])
def test_neural_manifold_preserves_reducer_paths_and_anchor_values(
    monkeypatch: pytest.MonkeyPatch, *, fallback: bool
) -> None:
    """UMAP and the existing MDS fallback retain their coordinates and anchors."""
    embedding = np.arange(144, dtype=float).reshape(72, 2)
    original = embedding.copy()
    calls: list[str] = []

    def umap_fitted(_self: object, features: np.ndarray) -> np.ndarray:
        assert features.shape == (72, 12)
        calls.append("umap")
        if fallback:
            message = "synthetic UMAP failure"
            raise RuntimeError(message)
        return embedding

    def mds_fitted(_self: object, features: np.ndarray) -> np.ndarray:
        assert features.shape == (72, 12)
        calls.append("mds")
        return embedding

    monkeypatch.setattr("umap.umap_.UMAP.fit_transform", umap_fitted)
    monkeypatch.setattr("sklearn.manifold.MDS.fit_transform", mds_fitted)
    latent = compute_neural_manifold_landscape()

    assert calls == (["umap", "mds"] if fallback else ["umap"])
    np.testing.assert_array_equal(embedding[:2], [[1.25, 0.85], [1.35, 0.82]])
    np.testing.assert_array_equal(embedding[2:], original[2:])
    assert latent.n_features == 12


def test_quantum_superposition_qubits():
    q = simulate_quantum_superposition_qubits()
    assert q.n_qubits == 4
    assert q.bell_state_fidelity > 0.90
    assert len(q.density_matrix_real) == 4
    # Check probabilities sum approximately to 1
    p_hold = q.measurement_collapse_probabilities[
        "Qubit 0 |0> Incumbent Hold (National)"
    ]
    p_flip = q.measurement_collapse_probabilities[
        "Qubit 0 |1> Superposition Collapse to Challenger (Labour)"
    ]
    assert pytest.approx(p_hold + p_flip, rel=1e-2) == 1.0


def test_autonomous_multiagent_parliament():
    parl = simulate_autonomous_multiagent_parliament()
    assert parl.total_agents == 131
    assert sum(parl.seat_distribution.values()) == 131
    assert parl.majority_threshold == 66
    assert len(parl.active_bills) >= 4
    assert parl.agent_whip_defiance_rates["National"] > 0.10
    assert parl.agent_whip_defiance_rates["TOP"] == 0.0
