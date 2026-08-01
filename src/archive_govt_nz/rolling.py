"""Deterministic rolling-archive history and manifest reconciliation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .versioning import VersionDecision, VersionState, decide_version

_SHA256_LENGTH = 64


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """One retained observation in a rolling resource history."""

    fingerprint: str
    state: str
    reason: str
    manifest_sha256: str
    previous_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class Reconciliation:
    """Machine-readable comparison of local and remote manifests."""

    state: str
    local_sha256: str
    remote_sha256: str | None
    missing_remote: tuple[str, ...]
    unexpected_remote: tuple[str, ...]


def update_history(
    history: list[HistoryEntry],
    decision: VersionDecision,
    manifest_sha256: str,
    *,
    max_entries: int = 32,
) -> list[HistoryEntry]:
    """Append a decision while retaining a bounded, auditable tail.

    A tombstone is an entry, never a deletion: it links to the prior
    fingerprint and therefore preserves withdrawal provenance even when the
    history tail is bounded.
    """
    if max_entries < 1:
        error = "max_entries_must_be_positive"
        raise ValueError(error)
    if len(manifest_sha256) != _SHA256_LENGTH:
        error = "manifest_sha256_must_be_sha256"
        raise ValueError(error)
    entry = HistoryEntry(
        decision.fingerprint,
        decision.state.value,
        decision.reason,
        manifest_sha256,
        decision.previous_fingerprint,
    )
    return [*history, entry][-max_entries:]


def reconcile_manifests(
    local: Mapping[str, Any], remote: Mapping[str, Any] | None
) -> Reconciliation:
    """Compare canonical manifest identity and item IDs without side effects."""
    local_bytes = _canonical(local)
    local_sha = hashlib.sha256(local_bytes).hexdigest()
    if remote is None:
        return Reconciliation("remote-missing", local_sha, None, (), ())
    remote_sha = hashlib.sha256(_canonical(remote)).hexdigest()
    local_ids = _ids(local)
    remote_ids = _ids(remote)
    missing = tuple(sorted(local_ids - remote_ids))
    unexpected = tuple(sorted(remote_ids - local_ids))
    state = "matched" if local_sha == remote_sha else "diverged"
    if missing or unexpected:
        state = "item-set-mismatch"
    return Reconciliation(state, local_sha, remote_sha, missing, unexpected)


def _ids(manifest: Mapping[str, Any]) -> set[str]:
    values = manifest.get("items", manifest.get("records", []))
    if not isinstance(values, list):
        return set()
    return {
        str(item["id"])
        for item in values
        if isinstance(item, Mapping) and "id" in item
    }


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


__all__ = [
    "HistoryEntry",
    "Reconciliation",
    "VersionState",
    "decide_version",
    "reconcile_manifests",
    "update_history",
]
