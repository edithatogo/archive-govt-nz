"""Operator boundaries retain exact authority and sanitize invocation receipts."""

from __future__ import annotations

import json
import os
import stat
import sys
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.parliament import hosted, hosted_cli
from archive_govt_nz.parliament.hosted_transport import POINTER, HostedError

from .test_hosted_checkpoint import Remote, initial
from .test_hosted_state import seeded

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def remote(tmp_path: Path, monkeypatch: MonkeyPatch) -> Remote:
    """Bind both CLI and controller to a fictional, disabled public authority."""
    manager, server = initial(tmp_path)
    manager.release()
    monkeypatch.setattr(hosted_cli, "NativeTransport", lambda: server)
    monkeypatch.setattr(hosted, "NativeTransport", lambda: server)
    monkeypatch.setattr(hosted_cli, "install_signals", lambda: None)
    monkeypatch.setattr(hosted_cli.logging, "disable", lambda _level: None)
    return server


def arguments(
    tmp_path: Path, monkeypatch: MonkeyPatch, operation: str, *extra: str
) -> Path:
    """Select a fresh working directory and sanitized receipt for one invocation."""
    receipt = tmp_path / (operation + ".json")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "parliament_hosted",
            operation,
            "--state-dir",
            str(tmp_path / operation),
            "--receipt",
            str(receipt),
            *extra,
        ],
    )
    return receipt


def test_verify_cli_receipt(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    remote: Remote,
    capsys: CaptureFixture[str],
) -> None:
    """Actual cold verification returns the same sanitized persisted/stdout result."""
    receipt = arguments(tmp_path, monkeypatch, "verify")
    assert hosted_cli.main() == 0
    result = json.loads(receipt.read_text())
    assert result["status"] == "cold_restore_verified"
    assert json.loads(capsys.readouterr().out) == result
    assert json.loads(remote.read(POINTER, remote.head()))["enabled"] is False


@pytest.mark.parametrize(
    "operation",
    ["run", "pilot", "verify", "hold", "pause", "resume", "enable", "bootstrap"],
)
def test_all_cli_writes_defer_without_claim_during_known_cooldown(
    tmp_path: Path, monkeypatch: MonkeyPatch, remote: Remote, operation: str
) -> None:
    """Even operator control/approval must not write before the known reset."""
    blocked = {
        "status": "deferred_hub_write",
        "hf_control_mutation": False,
        "cooldown_origin": {"run_id": "1", "attempt": "1"},
    }
    monkeypatch.setattr(remote, "write_cooldown", lambda _owner=None: blocked)
    before = remote.head()
    receipt = arguments(tmp_path, monkeypatch, operation)
    assert hosted_cli.main() == 0
    assert json.loads(receipt.read_text())["status"] == "deferred_hub_write"
    assert remote.head() == before


@pytest.mark.parametrize("qualified", [False, True])
def test_cli_retains_first429_without_replaying_mutation(
    tmp_path: Path, monkeypatch: MonkeyPatch, remote: Remote, *, qualified: bool
) -> None:
    """A deferred outcome preserves the actual failure and partial-work uncertainty."""
    calls = []

    def fail(*_args: object, **_kwargs: object) -> dict[str, object]:
        calls.append(True)
        reason = (
            "checkpoint_commit_outcome_unknown"
            if qualified
            else "report_capture_failed"
        )
        raise HostedError(reason, http_status=429, retry_after_seconds=500)

    monkeypatch.setattr(hosted_cli, "run", fail)
    before = remote.head()
    receipt = arguments(tmp_path, monkeypatch, "pilot")
    assert hosted_cli.main() == (0 if qualified else 1)
    result = json.loads(receipt.read_text())
    assert len(calls) == 1
    assert remote.head() == before
    if qualified:
        assert result["status"] == "deferred_hub_write"
        assert result["first_failure"]["status"] == "failed"
        assert result["first_failure"]["retry_after_seconds"] == 500
        assert result["source_acquisition_stopped"] is True
        assert "source_acquisition" not in result
    else:
        assert result["status"] == "failed"


@pytest.mark.parametrize("interrupted", [False, True])
def test_cli_does_not_disclose_sdk_exception_text(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    remote: Remote,
    capsys: CaptureFixture[str],
    *,
    interrupted: bool,
) -> None:
    """Unknown mutations and cancellation retain only stable evidence."""
    receipt = arguments(tmp_path, monkeypatch, "pilot")

    def fail(*_args: object, **_kwargs: object) -> dict[str, object]:
        message = "https://example.invalid/?signed=DO_NOT_DISCLOSE"
        sys.stdout.write(message + "\n")
        sys.stderr.write(message + "\n")
        if interrupted:
            raise KeyboardInterrupt
        raise OSError(message)

    monkeypatch.setattr(hosted_cli, "run", fail)
    assert hosted_cli.main() == (130 if interrupted else 1)
    captured = capsys.readouterr()
    output = captured.out
    assert "signed" not in captured.err
    assert "signed" not in output
    assert "signed" not in receipt.read_text()
    assert json.loads(output)["status"] == ("interrupted" if interrupted else "failed")
    logs = list((tmp_path / "pilot").glob(".private-sdk-*.log"))
    assert len(logs) == 1
    assert "signed" in logs[0].read_text()
    if os.name == "posix":
        assert stat.S_IMODE(logs[0].stat().st_mode) == 0o600
    assert len(remote.revisions) > 1


def test_hold_cli_requires_exact_evidence_and_keeps_private_boundary(
    tmp_path: Path, monkeypatch: MonkeyPatch, remote: Remote
) -> None:
    """The real parser forwards immutable proof fields to its own operation."""
    seen = []

    def approve(root: Path, **kwargs: object) -> dict[str, object]:
        seen.append((root, kwargs))
        return {"status": "report_access_hold_qualified", "source_acquisition": False}

    monkeypatch.setattr(hosted_cli, "approve_access_hold", approve)
    receipt = arguments(
        tmp_path,
        monkeypatch,
        "hold",
        "--hold-source-id",
        "report-example",
        "--failed-run",
        "1",
        "--failure-sha",
        "a" * 64,
        "--failure-revision",
        "b" * 40,
    )
    assert hosted_cli.main() == 0
    assert json.loads(receipt.read_text())["source_acquisition"] is False
    assert seen[0][1] == {
        "source_id": "report-example",
        "failed_run": "1",
        "failure_sha": "a" * 64,
        "failure_revision": "b" * 40,
        "transport": remote,
    }


def test_pause_resume_and_enable_preserve_authority(
    tmp_path: Path, monkeypatch: MonkeyPatch, remote: Remote
) -> None:
    """Resume cannot enable a bootstrap or replace native initial proof."""
    arguments(tmp_path, monkeypatch, "pause")
    assert hosted_cli.main() == 0
    pointer = json.loads(remote.read(POINTER, remote.head()))
    assert pointer["paused"] == "operator"
    arguments(tmp_path, monkeypatch, "resume")
    assert hosted_cli.main() == 0
    pointer = json.loads(remote.read(POINTER, remote.head()))
    assert pointer["paused"] is None
    assert pointer["enabled"] is False
    assert pointer["authority"] == "local"
    receipt = arguments(tmp_path, monkeypatch, "enable")
    assert hosted_cli.main() == 1
    assert json.loads(receipt.read_text())["reason"] == "native_proof_identity"
    proof = []
    monkeypatch.setattr(
        hosted_cli, "validate_enable_proofs", lambda *ids: proof.extend(ids)
    )
    arguments(
        tmp_path,
        monkeypatch,
        "enable",
        "--pilot-run",
        "1",
        "--cancelled-run",
        "2",
        "--restored-run",
        "3",
    )
    assert hosted_cli.main() == 0
    assert proof == ["1", "2", "3"]
    pointer = json.loads(remote.read(POINTER, remote.head()))
    assert pointer["enabled"] is True
    assert pointer["authority"] == "hosted"


def test_bootstrap_cli_requires_index_then_accepts_reviewed_seed(
    tmp_path: Path, monkeypatch: MonkeyPatch, remote: Remote
) -> None:
    """No bootstrap mutation occurs until its report index is explicit."""
    receipt = arguments(tmp_path, monkeypatch, "bootstrap")
    assert hosted_cli.main() == 1
    assert json.loads(receipt.read_text())["reason"] == "bootstrap_index_required"
    fresh = Remote()
    monkeypatch.setattr(hosted_cli, "NativeTransport", lambda: fresh)
    seeded(tmp_path / "bootstrap")
    index = tmp_path / "index.json"
    index.write_text("{}")
    arguments(tmp_path, monkeypatch, "bootstrap", "--index", str(index))
    assert hosted_cli.main() == 0
    assert json.loads(receipt.read_text())["status"] == "bootstrapped_disabled"
    assert len(remote.revisions) > 1


def test_real_signal_handlers_are_cancellation_only(monkeypatch: MonkeyPatch) -> None:
    """Native cancellation registers both signals without fabricating completion."""
    registered = []
    monkeypatch.setattr(hosted.signal, "signal", lambda *args: registered.append(args))
    hosted.install_signals()
    assert [row[0] for row in registered] == [
        hosted.signal.SIGINT,
        hosted.signal.SIGTERM,
    ]
    with pytest.raises(KeyboardInterrupt):
        hosted.stop_signal(0, None)


@pytest.mark.parametrize(
    ("case", "reason"),
    [("owner", "handover_not_quiescent"), ("card", "maintained_card_changed")],
)
def test_resume_refuses_live_owner_or_changed_card(
    tmp_path: Path, monkeypatch: MonkeyPatch, remote: Remote, case: str, reason: str
) -> None:
    """Operator resume cannot overwrite another writer or silently adopt card drift."""
    pointer = json.loads(remote.read(POINTER, remote.head()))
    if case == "owner":
        pointer["owner"] = "other_live_writer"
        remote.commit({POINTER: json.dumps(pointer).encode()}, remote.head())
    else:
        remote.commit({"README.md": b"changed maintained card"}, remote.head())
    before = remote.head()
    receipt = arguments(tmp_path, monkeypatch, "resume")
    assert hosted_cli.main() == 1
    assert json.loads(receipt.read_text())["reason"] == reason
    assert remote.head() == before
