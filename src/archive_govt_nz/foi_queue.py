"""Strict local queue snapshots binding ownership and work under one CAS write."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from typing import TYPE_CHECKING, Any, NoReturn, Protocol

from archive_govt_nz.foi_ownership import OwnerFence, propose_transfer, require_owner
from archive_govt_nz.foi_scheduler import Job, Queue

if TYPE_CHECKING:
    from collections.abc import Callable

    from archive_govt_nz.foi_ownership import TransferEvidence
    from archive_govt_nz.foi_state import StoredState

SCHEMA = "archive-govt-nz.foi-queue/v1"


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _record(value: object, model: type[Any], strings: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        field.name for field in fields(model)
    }:
        _fail("queue_schema")
    for name, item in value.items():
        expected = str if name in strings else int
        if type(item) is not expected:
            _fail("queue_field_type")
    return value


def _decode(document: dict[str, Any]) -> tuple[OwnerFence, Queue]:
    if (
        set(document) != {"schema_version", "owner", "queue"}
        or document["schema_version"] != SCHEMA
    ):
        _fail("queue_schema")
    owner = OwnerFence(
        **_record(document["owner"], OwnerFence, {"source_id", "owner", "lease_id"})
    )
    require_owner(owner, owner.owner, owner.epoch, owner.lease_id, 0)
    value = document["queue"]
    if not isinstance(value, dict) or set(value) != {
        "jobs",
        "sequence",
        "lease_history",
    }:
        _fail("queue_schema")
    if (
        type(value["sequence"]) is not int
        or not isinstance(value["jobs"], list)
        or not isinstance(value["lease_history"], list)
    ):
        _fail("queue_field_type")
    if not all(type(token) is str for token in value["lease_history"]):
        _fail("queue_field_type")
    strings = {
        "id",
        "source_id",
        "status",
        "lease_id",
        "manifest_sha256",
        "publication_revision",
    }
    jobs = tuple(Job(**_record(row, Job, strings)) for row in value["jobs"])
    if any(job.source_id != owner.source_id for job in jobs):
        _fail("queue_source_scope")
    return owner, Queue(jobs, value["sequence"], tuple(value["lease_history"]))


def _encode(owner: OwnerFence, queue: Queue) -> dict[str, Any]:
    document = json.loads(
        json.dumps(
            {"schema_version": SCHEMA, "owner": asdict(owner), "queue": asdict(queue)},
            allow_nan=False,
        )
    )
    _decode(document)
    return document


@dataclass(frozen=True)
class QueueSnapshot:
    """Version-bound local ownership and scheduling state."""

    version: int
    owner: OwnerFence
    queue: Queue


def _snapshot(stored: StoredState) -> QueueSnapshot:
    owner, queue = _decode(stored.document)
    return QueueSnapshot(stored.version, owner, queue)


class QueueStore(Protocol):
    """Local or shared store with expected-version conditional persistence."""

    def read(self, key: str) -> StoredState | None:
        """Return a validated snapshot or an absent key."""
        ...

    def compare_and_swap(
        self,
        key: str,
        expected_version: int | None,
        document: dict[str, Any],
    ) -> StoredState:
        """Reject conflicting state without overwriting it."""
        ...


class QueueRepository:
    """Persist pure proposals atomically; never execute work inside a transition."""

    def __init__(self, store: QueueStore, key: str) -> None:
        """Bind a local store key; this does not establish remote authority."""
        self.store = store
        self.key = key

    def read(self) -> QueueSnapshot | None:
        """Return a strictly reconstructed snapshot without requiring a live lease."""
        stored = self.store.read(self.key)
        return None if stored is None else _snapshot(stored)

    def initialize(self, owner: OwnerFence, queue: Queue, now: int) -> QueueSnapshot:
        """Create only an unseen source queue under a live exact owner fence."""
        require_owner(owner, owner.owner, owner.epoch, owner.lease_id, now)
        return _snapshot(
            self.store.compare_and_swap(self.key, None, _encode(owner, queue))
        )

    def _current(self, version: int, owner: OwnerFence, now: int) -> QueueSnapshot:
        current = self.read()
        if current is None or type(version) is not int or current.version != version:
            _fail("queue_version_conflict")
        if current.owner != owner:
            _fail("queue_owner_conflict")
        require_owner(current.owner, owner.owner, owner.epoch, owner.lease_id, now)
        return current

    def transact(
        self,
        version: int,
        owner: OwnerFence,
        now: int,
        transition: Callable[[Queue], Queue],
    ) -> QueueSnapshot:
        """Persist a trusted PURE scheduler transition before dispatch is considered."""
        current = self._current(version, owner, now)
        candidate = transition(current.queue)
        return _snapshot(
            self.store.compare_and_swap(self.key, version, _encode(owner, candidate))
        )

    def transfer(
        self,
        version: int,
        owner: OwnerFence,
        proposed: OwnerFence,
        now: int,
        evidence: TransferEvidence,
    ) -> QueueSnapshot:
        """Atomically preserve queued work while applying a validated owner proposal."""
        current = self._current(version, owner, now)
        if any(job.status == "leased" for job in current.queue.jobs):
            _fail("queue_not_quiescent")
        accepted = propose_transfer(current.owner, owner, proposed, now, evidence)
        return _snapshot(
            self.store.compare_and_swap(
                self.key, version, _encode(accepted, current.queue)
            )
        )
