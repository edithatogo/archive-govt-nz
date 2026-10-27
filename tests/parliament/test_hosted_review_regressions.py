"""Hosted review regressions enforce exact ownership, time and local handover."""

from __future__ import annotations

import asyncio
import hashlib
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament import hosted, hosted_checkpoint
from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_transport import HostedError

from .test_hosted_checkpoint import Remote, initial
from .test_hosted_state import seeded

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

    from archive_govt_nz.parliament.pipeline import Bounds


def test_terminal_proof_cannot_replace_a_different_live_owner(tmp_path: Path) -> None:
    """A fresh read cannot transfer an earlier owner's terminal proof to a rival."""
    manager, remote = initial(tmp_path)
    observer = Checkpoints(remote, tmp_path / "observer")
    observer.load()
    proved_owner = observer.pointer["owner"]
    manager.pointer["owner"] = "new_live_owner"
    manager.write_pointer()
    with pytest.raises(HostedError, match="parliament_writer_busy"):
        observer.claim("observer", previous_terminal_owner=proved_owner)
    assert observer.current()["owner"] == "new_live_owner"


def test_bootstrap_does_not_freeze_an_inflight_local_writer(tmp_path: Path) -> None:
    """Handover fails before mutation while a local writer holds its lock."""
    archive = seeded(tmp_path / "source")
    index = tmp_path / "index.json"
    index.write_text("{}")
    remote = Remote()
    with archive.lease(), pytest.raises(HostedError, match="bootstrap_writer_busy"):
        hosted.bootstrap(archive.root, index, remote)
    assert not (archive.root / "hosted-authority.json").exists()
    assert remote.head() == "0" * 40
    assert (
        hosted.bootstrap(archive.root, index, remote)["status"]
        == "bootstrapped_disabled"
    )


class Trickle(httpx.AsyncByteStream):
    """A server whose response can exceed a total budget without an idle timeout."""

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Delay the first body fragment past this fixture's remaining budget."""
        await asyncio.sleep(1)
        yield b"{}"


def test_discovery_enforces_total_remaining_deadline(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """A trickling catalogue cannot advance its cursor beyond the time budget."""
    manager, _remote = initial(tmp_path)
    hosted.begin(manager)
    assert manager.work is not None
    manager.work["seconds"] = 899.9
    manager.save()
    real_client = httpx.AsyncClient

    def request(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, stream=Trickle())

    monkeypatch.setattr(
        hosted.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(request), **kw),
    )
    with pytest.raises(TimeoutError):
        asyncio.run(hosted.acquire(manager))
    assert manager.archive is not None
    assert hosted.controls(manager.archive) == {}
    assert manager.archive.summary()["metadata_only"] == 1
    manager.release()


def test_unqualified_attachment_never_reaches_public_checkpoint(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """The existing PDF qualification gate applies before public object staging."""
    manager, remote = initial(tmp_path, pending=True)
    manager.release()
    body = b"unqualified non-PDF attachment"
    real_client = httpx.AsyncClient

    def request(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(
            200, content=body, headers={"content-type": "application/octet-stream"}
        )

    monkeypatch.setattr(
        hosted.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(request), **kw),
    )
    with pytest.raises(HostedError, match="report_capture_failed"):
        hosted.run(tmp_path / "runner", mode="pilot", transport=remote)
    assert all(
        body != payload
        for files in remote.revisions.values()
        for payload in files.values()
    )
    inspection = Checkpoints(remote, tmp_path / "inspection")
    inspection.load()
    sha = hashlib.sha256(body).hexdigest()
    assert any(
        row["status"] == "unqualified_payload" and row["detail"] == sha
        for row in inspection.state["tables"]["events"]
    )
    assert (tmp_path / "runner/cas/sha256" / sha[:2] / sha).read_bytes() == body


def test_failed_read_time_reduces_the_retry_budget(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """One transient failure cannot reset elapsed acquisition time before retry."""
    manager, _remote = initial(tmp_path, pending=True)
    hosted.begin(manager)
    assert manager.archive is not None
    assert manager.work is not None
    clock = [10.0]
    fake_time = SimpleNamespace(
        monotonic=lambda: clock[0], time=time.time, sleep=time.sleep
    )
    monkeypatch.setattr(hosted, "time", fake_time)
    monkeypatch.setattr(hosted_checkpoint, "time", fake_time)
    manager.last_tick = clock[0]
    manager.work["seconds"] = 899
    manager.save()
    limits = []

    async def capture(_http: httpx.AsyncClient, bounds: Bounds) -> dict[str, int]:
        limits.append(bounds.max_seconds)
        clock[0] += 0.8 if len(limits) == 1 else 0.1
        if len(limits) == 1:
            assert manager.archive is not None
            with manager.archive._connection() as connection:  # noqa: SLF001 - fixture source failure
                connection.execute(
                    "UPDATE records SET status='failed',last_error='ReadError'"
                )
            return {"captured": 0, "failed": 1, "bytes": 0}
        assert bounds.max_seconds == pytest.approx(0.2)
        return {"captured": 0, "failed": 0, "bytes": 0}

    monkeypatch.setattr(manager.archive, "capture", capture)
    asyncio.run(hosted.acquire(manager))
    assert len(limits) == 2
    assert manager.work["seconds"] == pytest.approx(899.9)
    manager.release()
