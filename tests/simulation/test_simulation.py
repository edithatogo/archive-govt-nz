"""Deterministic simulation and metamorphic contracts."""

import pytest

from archive_govt_nz.simulation import (
    RECOVERY_STAGES,
    simulate_capture,
    simulate_recovery,
)


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


@pytest.mark.parametrize("stage", RECOVERY_STAGES)
def test_recovery_simulation_proves_every_interruption_boundary(stage: str) -> None:
    """Every injected interruption resumes without duplicate objects."""
    receipt = simulate_recovery(["r2", "r1", "r2"], interrupt_stage=stage)
    assert receipt.captured_ids == ("r1", "r2")
    assert receipt.resumed is True
    assert receipt.duplicate_objects == 0
    assert receipt.unchanged_rerun is True


def test_recovery_simulation_rejects_unknown_stage() -> None:
    """Fault injection cannot silently accept an unmodelled boundary."""
    with pytest.raises(ValueError, match="invalid_recovery_stage"):
        simulate_recovery(["r1"], interrupt_stage="unknown")
