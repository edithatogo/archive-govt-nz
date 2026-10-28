"""Native failure identities qualify exclusions without fetching source bytes."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest

from archive_govt_nz.parliament import hosted, hosted_holds
from archive_govt_nz.parliament.hosted import begin
from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_holds import approve_access_hold
from archive_govt_nz.parliament.hosted_state import canonical, digest
from archive_govt_nz.parliament.hosted_transport import HostedError
from archive_govt_nz.parliament.publication import publish_batch
from archive_govt_nz.parliament.report_holds import reviewed_holds

from .test_hosted_checkpoint import Remote, initial
from .test_hosted_driver import Batches
from .test_hosted_state import SID
from .test_report_holds import failed

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def fixture(
    tmp_path: Path, monkeypatch: MonkeyPatch, http_status: int | None = None
) -> tuple[Remote, dict[str, Any]]:
    """Prepare immutable original failure and later publication-clear pause."""
    manager, remote = initial(tmp_path)
    manager.archive, _ = failed(tmp_path / "failure")
    manager.archive.guard = manager.guard
    if http_status is not None:
        with manager.archive._connection() as connection:  # noqa: SLF001
            text = connection.execute("SELECT record FROM records").fetchone()[0]
            url = json.loads(text)["attachments"][0]
            connection.execute(
                "INSERT INTO events VALUES(?,?,?,?)",
                (
                    SID,
                    "source_http_failure",
                    canonical(
                        {
                            "error_class": "terminal_status",
                            "http_status": http_status,
                            "record_sha256": digest(text.encode()),
                            "url_sha256": digest(url.encode()),
                        }
                    ).decode(),
                    1.0,
                ),
            )
    manager.owner = "gha_1_1"
    manager.pointer["owner"] = manager.owner
    manager.write_pointer()
    begin(manager)
    assert manager.work is not None
    manager.work["phase"] = "publish"
    manager.save()
    checkpoint = manager.pointer["checkpoint"].copy()
    manager.work = None
    manager.save()
    manager.pointer["paused"] = "failure"
    manager.write_pointer()
    manager.release()
    monkeypatch.setenv("GITHUB_RUN_ID", "2")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_SHA", "3" * 40)

    def native(run: str, attempt: str) -> dict[str, Any]:
        assert attempt == "1"
        return {
            "status": "in_progress" if run == "2" else "completed",
            "conclusion": "failure",
            "event": "workflow_dispatch",
            "head_sha": "3" * 40,
            "run_started_at": "1970-01-01T00:00:00+00:00",
            "updated_at": "1970-01-01T00:01:00+00:00",
        }

    monkeypatch.setattr(hosted_holds, "github_run", native)
    monkeypatch.setattr(
        hosted_holds,
        "github_receipt",
        lambda _run, _attempt: {
            "status": "failed",
            "operation": "run",
            "error_class": "HostedError",
            "reason": "report_capture_failed",
        },
    )
    return remote, {
        "source_id": SID,
        "failed_run": "1",
        "failure_sha": checkpoint["sha256"],
        "failure_revision": checkpoint["revision"],
    }


@pytest.mark.parametrize("status", [403, 500])
def test_new_failure_must_have_exact_access_status(
    tmp_path: Path, monkeypatch: MonkeyPatch, status: int
) -> None:
    """Known unavailable statuses qualify; a server fault remains unreviewed."""
    remote, args = fixture(tmp_path, monkeypatch, http_status=status)
    if status == 500:
        revision = remote.head()
        with pytest.raises(HostedError, match="http_evidence_unqualified"):
            approve_access_hold(tmp_path / "reject", transport=remote, **args)
        assert remote.head() == revision
    else:
        result = approve_access_hold(tmp_path / "approve", transport=remote, **args)
        assert result["original_http_status"] == status


def test_native_hold_preserves_pause_failure_and_cold_proof(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Approval mutates only reviewed metadata and is idempotent on repeat."""
    remote, args = fixture(tmp_path, monkeypatch)
    result = approve_access_hold(tmp_path / "approve", transport=remote, **args)
    assert result["status"] == "report_access_hold_qualified"
    assert result["source_acquisition"] is False
    assert result["original_http_status"] is None
    cold = Checkpoints(remote, tmp_path / "cold")
    cold.load()
    assert cold.pointer["owner"] is None
    assert cold.pointer["paused"] == "failure"
    assert cold.state["schema"] == "parliament-hosted-state/v2"
    cold.claim("reader")
    cold.accept(all_objects=True)
    archive = cold.restore()
    proof = reviewed_holds(archive)[SID]
    assert proof["failure_snapshot_sha256"] == args["failure_sha"]
    assert proof["source_probed_during_approval"] is False
    assert archive.summary()["failed"] == 1
    cold.release()
    revision = remote.head()
    again = approve_access_hold(tmp_path / "again", transport=remote, **args)
    assert again["status"] == "report_access_hold_already_qualified"
    assert remote.head() == revision


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("source_id", None, "evidence_required"),
        ("failed_run", "77", "failure_invocation"),
        ("source_id", "report-00000000-0000-0000-0000-000000000000", "source_missing"),
    ],
)
def test_wrong_exact_failure_never_claims(
    tmp_path: Path, monkeypatch: MonkeyPatch, field: str, value: str | None, reason: str
) -> None:
    """Missing or unrelated evidence cannot mutate public control."""
    remote, args = fixture(tmp_path, monkeypatch)
    args[field] = value
    revision = remote.head()
    with pytest.raises(HostedError, match=reason):
        approve_access_hold(tmp_path / "reject", transport=remote, **args)
    assert remote.head() == revision


def test_native_failure_receipt_must_match_exact_reason(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """A rights, integrity or arbitrary workflow failure cannot clear a row."""
    remote, args = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(hosted_holds, "github_receipt", lambda *_args: {})
    revision = remote.head()
    with pytest.raises(HostedError, match="native_failure_unqualified"):
        approve_access_hold(tmp_path / "reject", transport=remote, **args)
    assert remote.head() == revision


def test_schedule_and_live_writer_cannot_approve(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Only an explicit trusted manual Actions approval may create a hold."""
    remote, args = fixture(tmp_path, monkeypatch)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    with pytest.raises(HostedError, match="manual_actions"):
        approve_access_hold(tmp_path / "reject", transport=remote, **args)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    manager = Checkpoints(remote, tmp_path / "owner")
    manager.load()
    manager.claim("live")
    revision = remote.head()
    with pytest.raises(HostedError, match="quiescent_pause"):
        approve_access_hold(tmp_path / "reject", transport=remote, **args)
    assert remote.head() == revision


def test_changed_record_cannot_borrow_old_failure(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Changed source metadata requires a new explicit qualification."""
    remote, args = fixture(tmp_path, monkeypatch)
    manager = Checkpoints(remote, tmp_path / "change")
    manager.load()
    manager.claim("editor")
    manager.accept()
    archive = manager.restore()
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        record = json.loads(
            connection.execute("SELECT record FROM records").fetchone()[0]
        )
        record["title"] = "Changed after failure"
        connection.execute("UPDATE records SET record=?", (json.dumps(record),))
    manager.save()
    manager.release()
    revision = remote.head()
    with pytest.raises(HostedError, match="target_changed"):
        approve_access_hold(tmp_path / "reject", transport=remote, **args)
    assert remote.head() == revision


def test_reviewed_missing_original_does_not_block_other_pending_report(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """The actual driver captures/publishes another original without probing hold."""
    remote, args = fixture(tmp_path, monkeypatch)
    approve_access_hold(tmp_path / "approve", transport=remote, **args)
    manager = Checkpoints(remote, tmp_path / "queue")
    manager.load()
    manager.claim("editor")
    manager.accept()
    archive = manager.restore()
    guid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        original = connection.execute("SELECT record FROM records").fetchone()[0]
        record = json.loads(original)
        record.update(
            source_id="report-" + guid,
            url="https://selectcommittees.parliament.nz/v/6/" + guid,
            attachments=[
                "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
                + guid
            ],
        )
        connection.execute(
            "INSERT INTO records VALUES(?,?,?,?,?)",
            (record["source_id"], json.dumps(record), "historical", "pending", None),
        )
    manager.save()
    manager.pointer["paused"] = None
    manager.write_pointer()
    manager.release()
    requests = []
    real_client = httpx.AsyncClient

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        assert request.method == "GET"
        assert request.url.path.endswith(guid)
        return httpx.Response(
            200,
            content=b"%PDF-1.7\nseparate eligible report original",
            headers={"Content-Type": "application/pdf"},
        )

    monkeypatch.setattr(
        hosted.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    batches = Batches(remote)
    monkeypatch.setattr(
        hosted, "publish_batch", lambda a, b: publish_batch(a, b, hub=batches)
    )
    result = hosted.run(tmp_path / "pilot", mode="pilot", transport=remote)
    assert result["summary"]["captured"] == 1
    assert result["summary"]["failed"] == 1
    assert result["summary"]["published"] == 1
    assert result["reviewed_access_holds"] == 1
    assert result["unreviewed_failures"] == 0
    assert all(SID[7:] not in url for url in requests)
