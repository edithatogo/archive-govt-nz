"""Shadow comparison and delayed-owner rejection without external writes."""

from dataclasses import replace
from typing import Any

import pytest

from archive_govt_nz.foi_ownership import (
    DIMENSIONS,
    OwnerFence,
    ShadowSnapshot,
    TransferEvidence,
    compare_shadow,
    propose_transfer,
    require_owner,
)


def snapshot() -> ShadowSnapshot:
    """Snapshot."""
    return ShadowSnapshot(
        "nz-fyi", "a" * 64, tuple((name, "b" * 64) for name in DIMENSIONS)
    )


def fence() -> OwnerFence:
    """Fence."""
    return OwnerFence("nz-fyi", "edithatogo/fyi-archive", 1, "run-1", 200)


def evidence() -> TransferEvidence:
    """Evidence."""
    return TransferEvidence("nz-fyi", 1, 0, "c" * 64, "d" * 64, snapshot(), snapshot())


def transfer(**kwargs: object) -> OwnerFence:
    """Transfer."""
    args: dict[str, Any] = {
        "current": fence(),
        "expected": fence(),
        "proposed": OwnerFence("nz-fyi", "edithatogo/archive-govt-nz", 2, "run-2", 300),
        "now": 100,
        "evidence": evidence(),
    }
    args.update(kwargs)
    return propose_transfer(**args)


def test_transition_rejects_old_jobs_and_rollback_never_reuses_epoch() -> None:
    """Test transition rejects old jobs and rollback never reuses epoch."""
    new = transfer()
    require_owner(new, new.owner, 2, "run-2", 100)
    with pytest.raises(ValueError, match="owner_fence_mismatch"):
        require_owner(new, fence().owner, 1, "run-1", 100)
    rollback = transfer(
        current=new,
        expected=new,
        proposed=OwnerFence("nz-fyi", fence().owner, 3, "run-3", 300),
        evidence=replace(evidence(), expected_epoch=2),
    )
    assert rollback.epoch == 3
    with pytest.raises(ValueError, match="owner_fence_mismatch"):
        require_owner(rollback, rollback.owner, 1, "run-1", 100)


def test_shadow_parity_is_order_independent_and_capture_bound() -> None:
    """Test shadow parity is order independent and capture bound."""
    assert compare_shadow(snapshot(), snapshot()) == compare_shadow(
        snapshot(),
        replace(snapshot(), dimensions=tuple(reversed(snapshot().dimensions))),
    )
    for changed in (
        replace(snapshot(), source_id="au-rtk"),
        replace(snapshot(), capture_sha256="c" * 64),
        replace(snapshot(), dimensions=tuple((n, "c" * 64) for n in DIMENSIONS)),
    ):
        with pytest.raises(ValueError, match="shadow_parity_mismatch"):
            compare_shadow(snapshot(), changed)


@pytest.mark.parametrize(
    "changed",
    [
        {"source_id": ""},
        {"capture_sha256": "bad"},
        {"dimensions": ()},
        {"dimensions": (("cases", "b" * 64),) * 9},
        {"dimensions": tuple((n, "bad") for n in DIMENSIONS)},
    ],
)
def test_invalid_shadow(changed: dict[str, Any]) -> None:
    """Test invalid shadow."""
    with pytest.raises(ValueError, match="invalid_shadow"):
        compare_shadow(snapshot(), replace(snapshot(), **changed))


@pytest.mark.parametrize(
    "changed",
    [
        {"source_id": ""},
        {"owner": "unknown"},
        {"epoch": 0},
        {"epoch": True},
        {"lease_id": ""},
        {"expires_at": True},
        {"expires_at": 0},
    ],
)
def test_invalid_fence(changed: dict[str, Any]) -> None:
    """Test invalid fence."""
    with pytest.raises(ValueError, match="invalid_owner_fence"):
        require_owner(replace(fence(), **changed), fence().owner, 1, "run-1", 100)


@pytest.mark.parametrize("now", [200, 201, -1, True])
def test_expired_or_invalid_clock(now: int) -> None:
    """Test expired or invalid clock."""
    with pytest.raises(ValueError, match="invalid_or_expired_clock"):
        require_owner(fence(), fence().owner, 1, "run-1", now)


@pytest.mark.parametrize(
    "changed",
    [
        {"expected": replace(fence(), epoch=2)},
        {"expected": replace(fence(), expires_at=201)},
        {"proposed": replace(fence(), epoch=2, lease_id="run-2")},
        {"proposed": replace(fence(), owner="edithatogo/archive-govt-nz", epoch=2)},
        {"proposed": replace(fence(), expires_at=100)},
        {"evidence": replace(evidence(), source_id="au-rtk")},
        {"evidence": replace(evidence(), expected_epoch=2)},
        {"evidence": replace(evidence(), active_jobs=1)},
        {"evidence": replace(evidence(), active_jobs=False)},
        {"evidence": replace(evidence(), quiescence_sha256="bad")},
        {"evidence": replace(evidence(), restore_sha256="bad")},
        {
            "evidence": replace(
                evidence(), donor=replace(snapshot(), source_id="au-rtk")
            )
        },
    ],
)
def test_transfer_refuses_unbound_or_unsafe_inputs(changed: dict[str, Any]) -> None:
    """Test transfer refuses unbound or unsafe inputs."""
    with pytest.raises(ValueError, match=r"owner_|transfer_"):
        transfer(**changed)


def test_boolean_epoch_cannot_alias_a_valid_execution_epoch() -> None:
    """JSON booleans cannot alias monotonically increasing integer epochs."""
    with pytest.raises(ValueError, match="owner_fence_mismatch"):
        require_owner(fence(), fence().owner, epoch=True, lease_id="run-1", now=100)
    with pytest.raises(ValueError, match="unbound_transfer_evidence"):
        transfer(evidence=replace(evidence(), expected_epoch=True))


@pytest.mark.parametrize(
    "changed",
    [
        {"source_id": "au-rtk"},
        {"epoch": 3},
        {"expires_at": 99},
    ],
)
def test_proposal_must_keep_scope_and_increment_exactly(
    changed: dict[str, Any],
) -> None:
    """A transfer cannot silently change scope or skip the next epoch."""
    candidate = OwnerFence("nz-fyi", "edithatogo/archive-govt-nz", 2, "run-2", 300)
    with pytest.raises(ValueError, match="invalid_owner_transition"):
        transfer(proposed=replace(candidate, **changed))


@pytest.mark.parametrize(
    "changed",
    [
        {"source_id": True},
        {"source_id": 1},
        {"lease_id": True},
        {"lease_id": 1},
    ],
)
def test_ownership_identity_types_cannot_alias(changed: dict[str, Any]) -> None:
    """Truthiness and Python bool/int equality cannot supply ownership identity."""
    candidate = replace(fence(), **changed)
    with pytest.raises(ValueError, match="invalid_owner_fence"):
        require_owner(
            candidate, candidate.owner, candidate.epoch, candidate.lease_id, 100
        )
    with pytest.raises(ValueError, match="invalid_owner_fence"):
        transfer(
            proposed=replace(candidate, owner="edithatogo/archive-govt-nz", epoch=2)
        )


@pytest.mark.parametrize(
    "dimensions",
    [
        list(snapshot().dimensions),
        (("cases", "a" * 64),) * 10000,
        (None,) * 10,
    ],
)
def test_shadow_preflight_rejects_shape_before_mapping(dimensions: object) -> None:
    """Oversized or non-tuple dimensions fail before constructing a mapping."""
    values: dict[str, Any] = {"dimensions": dimensions}
    with pytest.raises(ValueError, match="invalid_shadow"):
        compare_shadow(snapshot(), replace(snapshot(), **values))
