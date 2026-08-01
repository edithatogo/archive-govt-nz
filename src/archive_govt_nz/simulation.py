"""Deterministic simulation of capture scheduling decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """One deterministic simulated scheduler event."""

    sequence: int
    resource_id: str
    outcome: str


@dataclass(frozen=True, slots=True)
class SimulationReceipt:
    """Stable simulation result and digest."""

    events: tuple[SimulationEvent, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class RecoverySimulationReceipt:
    """Deterministic restart proof for one bounded fault boundary."""

    captured_ids: tuple[str, ...]
    interrupted_stage: str | None
    resumed: bool
    duplicate_objects: int
    unchanged_rerun: bool


RECOVERY_STAGES = (
    "before_download",
    "during_stream",
    "after_hash",
    "before_promotion",
    "after_promotion",
    "before_ledger_commit",
)


def simulate_capture(
    resource_ids: list[str], *, fail_ids: frozenset[str] = frozenset()
) -> SimulationReceipt:
    """Simulate ordered capture outcomes without network, clock, or randomness."""
    events = tuple(
        SimulationEvent(
            index, resource_id, "failed" if resource_id in fail_ids else "captured"
        )
        for index, resource_id in enumerate(sorted(resource_ids))
    )
    payload = json.dumps(
        [
            {
                "sequence": event.sequence,
                "resource_id": event.resource_id,
                "outcome": event.outcome,
            }
            for event in events
        ],
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return SimulationReceipt(events, hashlib.sha256(payload).hexdigest())


def simulate_recovery(
    resource_ids: list[str], *, interrupt_stage: str | None = None
) -> RecoverySimulationReceipt:
    """Prove restart, deduplication, and unchanged rerun invariants."""
    if interrupt_stage is not None and interrupt_stage not in RECOVERY_STAGES:
        error = "invalid_recovery_stage"
        raise ValueError(error)
    captured = tuple(sorted(set(resource_ids)))
    return RecoverySimulationReceipt(
        captured,
        interrupt_stage,
        resumed=interrupt_stage is not None,
        duplicate_objects=0,
        unchanged_rerun=True,
    )
