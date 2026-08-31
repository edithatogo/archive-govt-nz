"""Durable local queue and owner transactions, using synthetic evidence only."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import pytest

from archive_govt_nz.foi_ownership import DIMENSIONS, ShadowSnapshot, TransferEvidence
from archive_govt_nz.foi_scheduler import Budget, SourcePolicy, reserve

if TYPE_CHECKING:
    from pathlib import Path

from archive_govt_nz.foi_ownership import OwnerFence
from archive_govt_nz.foi_queue import QueueRepository
from archive_govt_nz.foi_scheduler import Job, Queue
from archive_govt_nz.foi_state import StateStore


def test_reopen_preserves_owner_and_jobs(tmp_path: Path) -> None:
    """Reopening reconstructs the same owner and pending work."""
    path = tmp_path / "queue.sqlite"
    fence = OwnerFence("nz", "edithatogo/fyi-archive", 1, "owner", 1000)
    repository = QueueRepository(StateStore(path), "nz")
    first = repository.initialize(fence, Queue((Job("a", "nz", 0, 1, 1, 1),)), 1)
    assert QueueRepository(StateStore(path), "nz").read() == first


OWNER = OwnerFence("nz", "edithatogo/fyi-archive", 1, "owner", 1000)
JOBS = Queue((Job("a", "nz", 0, 1, 1, 1),))


def _repository(tmp_path: Path) -> QueueRepository:
    return QueueRepository(StateStore(tmp_path / "queue.sqlite"), "nz")


def _lease(queue: Queue) -> Queue:
    return reserve(
        queue,
        (SourcePolicy("nz", "https://example.org", "eligible"),),
        Budget(1, 1, 1),
        2,
        "capture",
    )


def _evidence(owner: OwnerFence) -> TransferEvidence:
    shadow = ShadowSnapshot(
        "nz", "a" * 64, tuple((name, "b" * 64) for name in DIMENSIONS)
    )
    return TransferEvidence("nz", owner.epoch, 0, "c" * 64, "d" * 64, shadow, shadow)


def test_transaction_recovery_and_stale_version(tmp_path: Path) -> None:
    """A committed reservation survives reopen and rejects stale writers."""
    repo = _repository(tmp_path)
    assert repo.read() is None
    first = repo.initialize(OWNER, JOBS, 1)
    second = repo.transact(first.version, OWNER, 2, _lease)
    assert second.queue.jobs[0].status == "leased"
    assert _repository(tmp_path).read() == second
    with pytest.raises(ValueError, match="version_conflict"):
        repo.transact(first.version, OWNER, 3, lambda queue: queue)
    with pytest.raises(ValueError, match="owner_conflict"):
        repo.transact(
            second.version, replace(OWNER, lease_id="stale"), 3, lambda queue: queue
        )
    with pytest.raises(ValueError, match="expired"):
        repo.transact(second.version, OWNER, 1000, lambda queue: queue)


def test_actual_cas_conflict_preserves_winner(tmp_path: Path) -> None:
    """A competing persistence write prevents the stale proposal from committing."""
    repo = _repository(tmp_path)
    first = repo.initialize(OWNER, JOBS, 1)

    def competing(queue: Queue) -> Queue:
        repo.transact(first.version, OWNER, 2, lambda value: value)
        return queue

    with pytest.raises(ValueError, match="state_conflict"):
        repo.transact(first.version, OWNER, 2, competing)
    current = repo.read()
    assert current is not None
    assert current.version == 2
    assert current.queue == JOBS


def test_transfer_and_rollback_fence_delayed_owner(tmp_path: Path) -> None:
    """Transfer and rollback preserve queue state while advancing the owner epoch."""
    repo = _repository(tmp_path)
    first = repo.initialize(OWNER, JOBS, 1)
    proposed = replace(
        OWNER, owner="edithatogo/archive-govt-nz", epoch=2, lease_id="receiver"
    )
    moved = repo.transfer(first.version, OWNER, proposed, 2, _evidence(OWNER))
    assert moved.queue == JOBS
    assert moved.owner == proposed
    with pytest.raises(ValueError, match="owner_conflict"):
        repo.transact(moved.version, OWNER, 3, _lease)
    rollback = replace(OWNER, epoch=3, lease_id="rollback")
    rolled = repo.transfer(moved.version, proposed, rollback, 3, _evidence(proposed))
    assert rolled.owner == rollback
    assert rolled.queue == JOBS
    with pytest.raises(ValueError, match="owner_conflict"):
        repo.transact(rolled.version, proposed, 4, _lease)


def test_active_queue_prevents_transfer(tmp_path: Path) -> None:
    """An expired or active source lease cannot be hidden by transfer evidence."""
    repo = _repository(tmp_path)
    first = repo.initialize(OWNER, JOBS, 1)
    leased = repo.transact(first.version, OWNER, 2, _lease)
    proposed = replace(
        OWNER, owner="edithatogo/archive-govt-nz", epoch=2, lease_id="receiver"
    )
    with pytest.raises(ValueError, match="not_quiescent"):
        repo.transfer(leased.version, OWNER, proposed, 400, _evidence(OWNER))


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("extra",), 1),
        (("schema_version",), "wrong"),
        (("owner", "extra"), 1),
        (("owner", "epoch"), True),
        (("queue", "extra"), 1),
        (("queue",), []),
        (("queue", "sequence"), True),
        (("queue", "jobs"), {}),
        (("queue", "lease_history"), {}),
        (("queue", "lease_history"), [1]),
        (("queue", "jobs", 0, "bytes"), 1.5),
        (("queue", "jobs", 0, "extra"), 1),
        (("queue", "jobs", 0, "source_id"), "uk"),
    ],
)
def test_serialization_rejects_malformed_payload(
    tmp_path: Path,
    path: tuple[str | int, ...],
    replacement: object,
) -> None:
    """Even correctly hashed stored JSON must satisfy the strict queue schema."""
    repo = _repository(tmp_path)
    repo.initialize(OWNER, JOBS, 1)
    stored = repo.store.read("nz")
    assert stored is not None
    document = copy.deepcopy(stored.document)
    target: Any = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    repo.store.compare_and_swap("nz", 1, document)
    with pytest.raises(
        ValueError, match=r"queue_schema|queue_field_type|queue_source_scope"
    ):
        repo.read()


def test_missing_state_and_invalid_version(tmp_path: Path) -> None:
    """Absent or noninteger expected versions cannot create a transaction."""
    repo = _repository(tmp_path)
    with pytest.raises(ValueError, match="version_conflict"):
        repo.transact(1, OWNER, 1, _lease)
    repo.initialize(OWNER, JOBS, 1)
    with pytest.raises(ValueError, match="version_conflict"):
        repo.transact(version=True, owner=OWNER, now=1, transition=_lease)


def test_reconstruction_rejects_missing_historical_lease_token(tmp_path: Path) -> None:
    """Persisted active tokens cannot disappear from the no-reuse history."""
    repo = _repository(tmp_path)
    first = repo.initialize(OWNER, JOBS, 1)
    leased = repo.transact(first.version, OWNER, 2, _lease)
    stored = repo.store.read("nz")
    assert stored is not None
    document = copy.deepcopy(stored.document)
    document["queue"]["lease_history"] = []
    repo.store.compare_and_swap("nz", leased.version, document)
    with pytest.raises(ValueError, match="invalid queue state"):
        repo.read()


def test_reconstruction_rejects_verified_without_publication_identity(
    tmp_path: Path,
) -> None:
    """Verified status requires well-formed publication identities on reconstruction."""
    repo = _repository(tmp_path)
    first = repo.initialize(OWNER, JOBS, 1)
    leased = repo.transact(first.version, OWNER, 2, _lease)
    stored = repo.store.read("nz")
    assert stored is not None
    document = copy.deepcopy(stored.document)
    document["queue"]["jobs"][0]["status"] = "verified"
    repo.store.compare_and_swap("nz", leased.version, document)
    with pytest.raises(ValueError, match="invalid job"):
        repo.read()
