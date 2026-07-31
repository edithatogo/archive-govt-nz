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
