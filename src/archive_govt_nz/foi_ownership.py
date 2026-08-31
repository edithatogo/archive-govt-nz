"""Pure ownership proposals and shadow parity; no shared authority is mutated."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

OWNERS = frozenset({"edithatogo/fyi-archive", "edithatogo/archive-govt-nz"})
DIMENSIONS = (
    "cases",
    "events",
    "attachments",
    "raw_hashes",
    "revisions",
    "queues",
    "checkpoints",
    "retries",
    "takedowns",
)


def _fail(reason: str) -> None:
    raise ValueError(reason)


def _digest(value: str) -> bool:
    return re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class OwnerFence:
    """Source-scoped execution identity with an exclusive Unix expiry."""

    source_id: str
    owner: str
    epoch: int
    lease_id: str
    expires_at: int


def _validate(fence: OwnerFence) -> None:
    if (
        type(fence.source_id) is not str
        or not fence.source_id
        or fence.owner not in OWNERS
        or type(fence.epoch) is not int
        or fence.epoch < 1
        or type(fence.lease_id) is not str
        or not fence.lease_id
        or type(fence.expires_at) is not int
        or fence.expires_at <= 0
    ):
        _fail("invalid_owner_fence")


def require_owner(
    fence: OwnerFence, owner: str, epoch: int, lease_id: str, now: int
) -> None:
    """Check a freshly read authority record before an execution side effect."""
    _validate(fence)
    if type(now) is not int or now < 0 or now >= fence.expires_at:
        _fail("invalid_or_expired_clock")
    if type(epoch) is not int or (owner, epoch, lease_id) != (
        fence.owner,
        fence.epoch,
        fence.lease_id,
    ):
        _fail("owner_fence_mismatch")


@dataclass(frozen=True)
class ShadowSnapshot:
    """Hashes of canonical projections from the same retained capture input."""

    source_id: str
    capture_sha256: str
    dimensions: tuple[tuple[str, str], ...]


def _shadow(snapshot: ShadowSnapshot) -> dict[str, str]:
    if type(snapshot.dimensions) is not tuple or len(snapshot.dimensions) != len(
        DIMENSIONS
    ):
        _fail("invalid_shadow")
    values = dict(snapshot.dimensions)
    if (
        not snapshot.source_id
        or not _digest(snapshot.capture_sha256)
        or set(values) != set(DIMENSIONS)
        or not all(_digest(value) for value in values.values())
    ):
        _fail("invalid_shadow")
    return values


def compare_shadow(donor: ShadowSnapshot, receiver: ShadowSnapshot) -> str:
    """Require full bounded parity; counts alone cannot establish equality."""
    left, right = _shadow(donor), _shadow(receiver)
    if (
        donor.source_id != receiver.source_id
        or donor.capture_sha256 != receiver.capture_sha256
        or left != right
    ):
        _fail("shadow_parity_mismatch")
    payload = [donor.source_id, donor.capture_sha256, left]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class TransferEvidence:
    """Externally verified receipts; this module cannot authenticate them."""

    source_id: str
    expected_epoch: int
    active_jobs: int
    quiescence_sha256: str
    restore_sha256: str
    donor: ShadowSnapshot
    receiver: ShadowSnapshot


def propose_transfer(
    current: OwnerFence,
    expected: OwnerFence,
    proposed: OwnerFence,
    now: int,
    evidence: TransferEvidence,
) -> OwnerFence:
    """Validate a transfer or rollback proposal before remote atomic persistence."""
    require_owner(current, expected.owner, expected.epoch, expected.lease_id, now)
    if current != expected:
        _fail("owner_fence_conflict")
    _validate(proposed)
    if (
        proposed.owner == current.owner
        or proposed.lease_id == current.lease_id
        or proposed.expires_at <= now
        or proposed.source_id != current.source_id
        or proposed.epoch != current.epoch + 1
    ):
        _fail("invalid_owner_transition")
    if (
        evidence.source_id != current.source_id
        or type(evidence.expected_epoch) is not int
        or evidence.expected_epoch != current.epoch
        or type(evidence.active_jobs) is not int
        or evidence.active_jobs != 0
        or not _digest(evidence.quiescence_sha256)
        or not _digest(evidence.restore_sha256)
        or evidence.donor.source_id != current.source_id
    ):
        _fail("unbound_transfer_evidence")
    compare_shadow(evidence.donor, evidence.receiver)
    return proposed
