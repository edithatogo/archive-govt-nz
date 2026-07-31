"""Deterministic change-driven version decisions with tombstones."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class VersionState(StrEnum):
    """Material and non-material observation outcomes."""

    INITIAL = "initial"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    TOMBSTONE = "tombstone"


@dataclass(frozen=True, slots=True)
class VersionDecision:
    """Evidence needed to persist one version relationship."""

    state: VersionState
    fingerprint: str
    previous_fingerprint: str | None
    reason: str
    policy_version: str


def decide_version(
    current: dict[str, Any],
    previous: dict[str, Any] | None = None,
    *,
    policy_version: str = "version-policy/v1",
    withdrawn: bool = False,
) -> VersionDecision:
    """Compare canonical metadata/resource evidence and preserve withdrawal."""
    fingerprint = _fingerprint(current)
    previous_fingerprint = None if previous is None else _fingerprint(previous)
    if withdrawn:
        return VersionDecision(
            VersionState.TOMBSTONE,
            fingerprint,
            previous_fingerprint,
            "source_withdrawn",
            policy_version,
        )
    if previous is None:
        return VersionDecision(
            VersionState.INITIAL, fingerprint, None, "first_observation", policy_version
        )
    if fingerprint == previous_fingerprint:
        return VersionDecision(
            VersionState.UNCHANGED,
            fingerprint,
            previous_fingerprint,
            "no_material_change",
            policy_version,
        )
    return VersionDecision(
        VersionState.CHANGED,
        fingerprint,
        previous_fingerprint,
        "material_change",
        policy_version,
    )


def _fingerprint(value: dict[str, Any]) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
