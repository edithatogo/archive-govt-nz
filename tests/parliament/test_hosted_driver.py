"""The finite controller preserves rights gates, accounting and native proof binding."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament import hosted
from archive_govt_nz.parliament.hosted import retry_transport_once, run
from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_transport import HostedError
from archive_govt_nz.parliament.pipeline import Bounds
from archive_govt_nz.parliament.publication import publish_batch

from .test_hosted_checkpoint import Remote, initial
from .test_hosted_state import SID, seeded

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
    from huggingface_hub import CommitOperationAdd


class Batches:
    """Connect the existing independent publisher to the fictional remote."""

    def __init__(self, remote: Remote) -> None:
        """Share the fixture's exact immutable revisions."""
        self.remote = remote

    def head(self, repo: str) -> str:
        """Return the current parent."""
        assert repo == "edithatogo/archive-govt-nz-global"
        return self.remote.head()

    def commit(
        self, repo: str, operations: list[CommitOperationAdd], parent: str
    ) -> str:
        """Upload immutable publication files once."""
        assert repo == "edithatogo/archive-govt-nz-global"
        return self.remote.commit(
            {op.path_in_repo: Path(str(op.path_or_fileobj)) for op in operations},
            parent,
        )

    def download(self, repo: str, filename: str, revision: str, cache: Path) -> Path:
        """Serve a distinct pinned readback path."""
        assert repo == "edithatogo/archive-govt-nz-global"
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / "pinned"
        target.write_bytes(self.remote.read(filename, revision))
        return target


def test_pilot_full_metadata_cycle_and_retirement(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Cold state, discovery, publication, checkpoint and retirement compose."""
    manager, remote = initial(tmp_path)
    manager.release()
    real_client = httpx.AsyncClient

    def request(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        assert req.method == "POST"
        body = json.loads(req.content)
        results = [
            {
                "id": f"00000000-0000-0000-0000-{n:012d}",
                "title": f"Example {n}",
                "documentType": "SelectCommitteeReport",
                "parliamentNumber": 54,
            }
            for n in range(1, 11)
        ]
        return httpx.Response(
            200,
            json={
                "results": results,
                "page": body["page"],
                "pageSize": 10,
                "totalResults": 10,
            },
        )

    monkeypatch.setattr(
        hosted.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(request), **kwargs),
    )
    batches = Batches(remote)
    monkeypatch.setattr(
        hosted, "publish_batch", lambda a, b: publish_batch(a, b, hub=batches)
    )
    result = run(tmp_path / "hosted", mode="pilot", transport=remote)
    assert result["summary"]["metadata_only"] == 10
    assert result["summary"]["published"] == 1
    assert result["attempts"][0]["work"]["observed"] == 10
    assert not list((tmp_path / "hosted/cas/sha256").glob("*/*"))
    cold = run(tmp_path / "cold", mode="verify", transport=remote)
    assert cold["status"] == "cold_restore_verified"
    assert cold["objects"] == 2


@pytest.mark.parametrize(
    "error", ["robots_denied", "source_forbidden", "size_limit", "unsafe_url"]
)
def test_denials_never_requeued(tmp_path: Path, error: str) -> None:
    """No restrictive or policy failure is turned into a transport retry."""
    archive = seeded(tmp_path)
    with archive._connection() as c:  # noqa: SLF001 - isolated fixture
        c.execute("UPDATE records SET status='failed',last_error=?", (error,))
    assert not retry_transport_once(archive, SID)


def test_exact_transient_has_only_one_retry(tmp_path: Path) -> None:
    """A second transport failure retains the first request and is not looped."""
    archive = seeded(tmp_path)
    with archive._connection() as c:  # noqa: SLF001
        c.execute("UPDATE records SET status='failed',last_error='ReadTimeout'")
    assert retry_transport_once(archive, SID)
    with archive._connection() as c:  # noqa: SLF001
        c.execute("UPDATE records SET status='failed',last_error='ReadTimeout'")
    assert not retry_transport_once(archive, SID)


def test_disabled_schedule_and_pilot_bounds(tmp_path: Path) -> None:
    """An absent/disabled authority never starts collection implicitly."""
    assert (
        run(tmp_path / "empty", mode="run", transport=Remote())["status"]
        == "not_bootstrapped"
    )
    manager, remote = initial(tmp_path)
    manager.release()
    assert (
        run(tmp_path / "inactive", mode="run", transport=remote)["status"] == "disabled"
    )
    with pytest.raises(HostedError, match="pilot_requires_one"):
        run(tmp_path / "unbounded", mode="pilot", max_batches=1000, transport=remote)


def test_pause_allows_durable_flush_but_stops_source(tmp_path: Path) -> None:
    """An in-flight accepted body may flush without starting another request."""
    manager, _remote = initial(tmp_path)
    manager.pointer["paused"] = "operator"
    manager.write_pointer()
    manager.guard()
    with pytest.raises(HostedError, match="source_paused"):
        manager.source_guard()
    manager.save()
    manager.release()


def test_retirement_requires_isolated_restore(tmp_path: Path) -> None:
    """The original authoritative SSD never becomes disposable hosted scratch."""
    manager, remote = initial(tmp_path)
    with pytest.raises(HostedError, match="retirement_requires_restored"):
        manager.retire()
    worker = Checkpoints(remote, tmp_path / "worker")
    worker.load()
    worker.claim("worker", previous_terminal=True)
    worker.accept()
    archive = worker.restore()
    archive.store.put_bytes(b"unqualified scratch")
    with pytest.raises(HostedError, match="retirement_object_unqualified"):
        worker.retire()
    assert list(archive.store.objects.glob("*/*"))
    worker.release()


def test_prepared_publication_cold_restore(tmp_path: Path) -> None:
    """A prepared batch survives runner loss and publishes its exact originals."""
    _manager, remote = initial(tmp_path, pending=True)
    worker = Checkpoints(remote, tmp_path / "prepared")
    worker.load()
    worker.claim("prepared", previous_terminal=True)
    worker.accept()
    archive = worker.restore()

    def request(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, content=b"%PDF-1.7\nexact original")

    async def capture() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(request)) as http:
            await archive.capture(http, Bounds(max_records=1))

    asyncio.run(capture())
    batch = archive.package(archive.report_decisions())
    worker.release()
    cold = Checkpoints(remote, tmp_path / "restored-batch")
    cold.load()
    cold.claim("restored")
    cold.accept(all_objects=True)
    restored = cold.restore()
    assert restored.pending_report_batch() == batch["batch"]
    result = publish_batch(restored, str(batch["batch"]), hub=Batches(remote))
    assert result["status"] == "verified"
    assert restored.pending_report_batch() is None
    cold.release()


def test_enable_proofs_bind_exact_cancelled_checkpoint(
    monkeypatch: MonkeyPatch,
) -> None:
    """Three green/native runs alone cannot qualify an unrelated recovery."""
    revision = "a" * 40
    values = {
        "1": {"conclusion": "success", "head_sha": revision, "run_attempt": 1},
        "2": {"conclusion": "cancelled", "head_sha": revision, "run_attempt": 2},
        "3": {"conclusion": "success", "head_sha": revision, "run_attempt": 1},
    }
    monkeypatch.setattr(hosted, "github_run", values.__getitem__)
    monkeypatch.setattr(
        hosted.subprocess,
        "run",
        lambda *_a, **_kw: type(
            "Result", (), {"stdout": json.dumps({"commit": {"sha": revision}})}
        )(),
    )
    recovery = {"status": "completed_bounded_invocation", "attempts": []}
    monkeypatch.setattr(
        hosted,
        "github_receipt",
        lambda run_id: (
            {"status": "cold_restore_verified", "objects": 1}
            if run_id == "1"
            else recovery
        ),
    )
    with pytest.raises(HostedError, match="native_interruption_restore_required"):
        hosted.validate_enable_proofs("1", "2", "3")
    recovery["attempts"] = [{"work": {"interrupted": True, "invocation": "gha_2_1"}}]
    with pytest.raises(HostedError, match="native_interruption_restore_required"):
        hosted.validate_enable_proofs("1", "2", "3")
    recovery["attempts"] = [{"work": {"interrupted": True, "invocation": "gha_2_2"}}]
    hosted.validate_enable_proofs("1", "2", "3")
