"""Durability, stale-writer fencing and interruption recover without refetching."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament import hosted_transport
from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_state import digest
from archive_govt_nz.parliament.hosted_transport import (
    POINTER,
    HostedError,
    NativeTransport,
    abort,
)
from archive_govt_nz.parliament.pipeline import Bounds

from .test_hosted_state import GUID, SID, seeded

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class Remote(NativeTransport):
    """Fictional immutable revisions and true parent compare-and-swap."""

    def __init__(self) -> None:
        """Initialize isolated fictional revisions."""
        self.revision = "0" * 40
        self.revisions = {self.revision: {"README.md": b"maintained card"}}
        self.corrupt = False
        self.unknown = False

    def head(self) -> str:
        """Return the fictional current head."""
        return self.revision

    def exists(self, path: str, revision: str) -> bool:
        """Inspect an exact immutable revision."""
        return path in self.revisions[revision]

    def read(self, path: str, revision: str) -> bytes:
        """Return pinned fixture bytes, optionally corrupting object data."""
        if self.corrupt and "/checkpoint-objects/" in path:
            return b"corrupt"
        return self.revisions[revision][path]

    def commit(self, files: dict[str, bytes | Path], parent: str) -> str:
        """Commit once against the exact observed parent."""
        if parent != self.revision:
            abort("test_parent_conflict")
        current = dict(self.revisions[parent])
        current.update(
            {p: v.read_bytes() if isinstance(v, Path) else v for p, v in files.items()}
        )
        self.revision = f"{len(self.revisions):040x}"
        self.revisions[self.revision] = current
        if self.unknown and any("/checkpoints/" in p for p in files):
            self.unknown = False
            abort("test_unknown_after_commit")
        return self.revision


def initial(tmp_path: Path, *, pending: bool = False) -> tuple[Checkpoints, Remote]:
    """Bootstrap a report-only fixture, without native credentials."""
    remote = Remote()
    manager = Checkpoints(remote, tmp_path / "source")
    archive = seeded(manager.root)
    if pending:
        with archive._connection() as connection:  # noqa: SLF001
            rec = json.loads(
                connection.execute("SELECT record FROM records").fetchone()[0]
            )
            rec.update(
                metadata_only=False,
                attachments=[
                    "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
                    + GUID
                ],
            )
            connection.execute(
                "UPDATE records SET record=?,status='pending'", (json.dumps(rec),)
            )
    manager.parent = remote.head()
    manager.pointer = {
        "schema": "parliament-continuation/v1",
        "generation": 0,
        "owner": "first",
        "lease_until": 99999999999,
        "authority": "local",
        "enabled": False,
        "paused": None,
        "checkpoint": None,
        "card_sha256": digest(b"maintained card"),
    }
    manager.owner = "first"
    manager.archive = archive
    manager.write_pointer()
    manager.save()
    return manager, remote


def test_cold_restore_and_stale_writer(tmp_path: Path) -> None:
    """Reject a live rival and preserve cold-restored metadata."""
    manager, remote = initial(tmp_path)
    fresh = Checkpoints(remote, tmp_path / "fresh")
    fresh.load()
    with pytest.raises(HostedError, match="writer_busy"):
        fresh.claim("second")
    fresh.claim("second", previous_terminal=True)
    with pytest.raises(HostedError, match="writer_fenced"):
        manager.guard()
    fresh.accept(all_objects=True)
    restored = fresh.restore()
    assert restored.summary()["metadata_only"] == 1
    fresh.release()


def test_unknown_staging_outcome_never_promotes_cursor(tmp_path: Path) -> None:
    """An unknown staging commit cannot promote the accepted pointer."""
    manager, remote = initial(tmp_path)
    before = manager.pointer["checkpoint"].copy()
    remote.unknown = True
    with pytest.raises(HostedError, match="unknown_after_commit"):
        manager.save()
    pointer = json.loads(remote.read(POINTER, remote.head()))
    assert pointer["checkpoint"]["status"] == "uploaded"
    assert before["status"] == "verified"
    assert manager.failed
    manager.release()


def test_interrupt_after_durable_object_resumes_without_source(tmp_path: Path) -> None:
    """A stopped writer resumes its accepted original without source traffic."""
    _manager, remote = initial(tmp_path, pending=True)
    resumed = Checkpoints(remote, tmp_path / "worker1")
    resumed.load()
    resumed.claim("worker1", previous_terminal=True)
    resumed.accept()
    archive = resumed.restore()
    checkpoint = resumed.checkpoint

    def interrupt(stage: str, detail: dict[str, object]) -> None:
        checkpoint(stage, detail)
        if stage == "capture_object":
            raise KeyboardInterrupt

    archive.checkpoint = interrupt

    def request(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(
            200,
            content=b"immutable original",
            headers={"Content-Type": "application/pdf"},
        )

    async def capture(http: httpx.AsyncClient) -> dict[str, object]:
        return await archive.capture(http, Bounds(max_records=1))

    async def first() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(request)) as http:
            await capture(http)

    with pytest.raises(KeyboardInterrupt):
        asyncio.run(first())
    saved = Checkpoints(remote, tmp_path / "worker2")
    saved.load()
    saved.claim("worker2", previous_terminal=True)
    saved.accept()
    archive = saved.restore()
    assert archive.summary()["pending"] == 1

    def never_request(_req: httpx.Request) -> httpx.Response:
        message = "accepted original must not be fetched again"
        raise AssertionError(message)

    async def second() -> dict[str, object]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(never_request)
        ) as http:
            return await archive.capture(http, Bounds(max_records=1))

    assert asyncio.run(second())["captured"] == 1
    assert archive.summary()["captured"] == 1
    saved.release()


def test_corrupt_staged_object_blocks_acceptance(tmp_path: Path) -> None:
    """Remote corruption leaves the checkpoint uploaded until verified."""
    manager, remote = initial(tmp_path, pending=True)
    archive = manager.archive
    assert archive is not None
    payload = archive.store.put_bytes(b"example")
    with archive._connection() as connection:  # noqa: SLF001
        connection.execute(
            "INSERT INTO captures VALUES(?,?,?,?,?,?)",
            (
                SID,
                "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
                + GUID,
                payload.sha256,
                payload.byte_count,
                "application/pdf",
                1,
            ),
        )
    remote.corrupt = True
    with pytest.raises(HostedError, match="remote_object_integrity"):
        manager.save()
    assert (
        json.loads(remote.read(POINTER, remote.head()))["checkpoint"]["status"]
        == "uploaded"
    )
    manager.release()
    remote.corrupt = False
    recovery = Checkpoints(remote, tmp_path / "recovery")
    recovery.load()
    recovery.claim("recovery")
    recovery.accept()
    assert recovery.pointer["checkpoint"]["status"] == "verified"
    recovery.release()


def test_legacy_acquisition_and_publication_are_fenced(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Alternate local CLI roots cannot compete with the public control owner."""
    manager, remote = initial(tmp_path)
    monkeypatch.setattr(hosted_transport, "NativeTransport", lambda: remote)
    with pytest.raises(HostedError, match="source_requires_fenced"):
        hosted_transport.legacy_source_guard()
    with pytest.raises(HostedError, match="parliament_writer_fenced"):
        hosted_transport.assert_publication_authority(
            "edithatogo/archive-govt-nz-global", remote.head()
        )
    monkeypatch.setenv("PARLIAMENT_WRITER_ID", "first")
    hosted_transport.assert_publication_authority(
        "edithatogo/archive-govt-nz-global", remote.head()
    )
    manager.pointer.update(owner=None, authority="hosted")
    manager.write_pointer()
    with pytest.raises(HostedError, match="parliament_writer_lease_required"):
        hosted_transport.assert_publication_authority(
            "edithatogo/archive-govt-nz-global", remote.head()
        )
