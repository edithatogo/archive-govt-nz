"""Hosted review regressions enforce exact ownership, time and local handover."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament import hosted
from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_transport import HostedError

from .test_hosted_checkpoint import Remote, initial
from .test_hosted_state import seeded

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


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
