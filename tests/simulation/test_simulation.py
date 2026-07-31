"""Deterministic simulation and metamorphic contracts."""

from archive_govt_nz.simulation import simulate_capture


def test_simulation_is_deterministic_under_input_permutation() -> None:
    """Permutation of discovery order cannot alter the simulated receipt."""
    first = simulate_capture(["r3", "r1", "r2"], fail_ids=frozenset({"r2"}))
    second = simulate_capture(["r2", "r3", "r1"], fail_ids=frozenset({"r2"}))
    assert first == second


def test_simulation_metamorphic_addition_is_local() -> None:
    """Adding one resource preserves all prior event outcomes."""
    base = simulate_capture(["r1", "r2"])
    expanded = simulate_capture(["r1", "r2", "r3"])
    base_outcomes = {event.resource_id: event.outcome for event in base.events}
    expanded_outcomes = {event.resource_id: event.outcome for event in expanded.events}
    assert all(expanded_outcomes[key] == value for key, value in base_outcomes.items())
