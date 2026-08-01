"""Reconcile repeated capture observations without duplicating unchanged objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .versioning import VersionDecision, decide_version

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class CaptureReconciliation:
    """Deterministic result for one previous/current capture pair."""

    decisions: dict[str, VersionDecision]
    unchanged_ids: tuple[str, ...]
    changed_ids: tuple[str, ...]
    initial_ids: tuple[str, ...]
    tombstone_ids: tuple[str, ...]

    @property
    def duplicate_objects_avoided(self) -> int:
        """Count unchanged resources that must not create another object."""
        return len(self.unchanged_ids)


def reconcile_capture_observations(
    current: Mapping[str, Mapping[str, Any]],
    previous: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    withdrawn: frozenset[str] = frozenset(),
    disappeared: frozenset[str] = frozenset(),
    policy_changed: frozenset[str] = frozenset(),
) -> CaptureReconciliation:
    """Return version decisions for a deterministic repeated capture run."""
    prior = previous or {}
    ids = sorted(set(current) | set(prior))
    decisions: dict[str, VersionDecision] = {}
    for resource_id in ids:
        observation = current.get(resource_id, prior.get(resource_id, {}))
        decisions[resource_id] = decide_version(
            dict(observation),
            None if resource_id not in prior else dict(prior[resource_id]),
            withdrawn=resource_id in withdrawn,
            disappeared=resource_id in disappeared,
            policy_changed=resource_id in policy_changed,
        )
    groups = {
        "initial": tuple(k for k, v in decisions.items() if v.state.value == "initial"),
        "unchanged": tuple(
            k for k, v in decisions.items() if v.state.value == "unchanged"
        ),
        "changed": tuple(k for k, v in decisions.items() if v.state.value == "changed"),
        "tombstone": tuple(
            k for k, v in decisions.items() if v.state.value == "tombstone"
        ),
    }
    return CaptureReconciliation(
        decisions,
        groups["unchanged"],
        groups["changed"],
        groups["initial"],
        groups["tombstone"],
    )


__all__ = ["CaptureReconciliation", "reconcile_capture_observations"]
