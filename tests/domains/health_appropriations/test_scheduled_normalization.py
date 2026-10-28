# SPDX-License-Identifier: Apache-2.0
"""Scheduler normalization replay and interruption contracts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_cpi import HEADER, META

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import scheduled_normalization
from archive_govt_nz.domains.health_appropriations.source_operations import (
    SourceRequest,
)


@pytest.fixture
def source_request(tmp_path: Path) -> SourceRequest:
    source = tmp_path / "source.csv"
    source.write_text(HEADER + "CPIQ.SE9A,1914.06,1.25" + META, encoding="utf-8")
    return SourceRequest(
        source,
        tmp_path / "unused",
        "cpiq-se9a/v1",
        hashlib.sha256(source.read_bytes()).hexdigest(),
        "2026-Q2",
        "https://example.invalid/source",
        "2026-08-31T00:00:00Z",
    )


def test_dry_run_write_replay_and_tamper_rejection(
    source_request: SourceRequest, tmp_path: Path
) -> None:
    root = tmp_path / "scheduler"
    original = source_request.source.read_bytes()
    planned = scheduled_normalization.run_scheduled_normalization(source_request, root)
    assert planned["operation"]["status"] == "preflight_passed"
    assert not root.exists()
    written = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    assert written["status"] == "written_local"
    reused = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    assert reused["status"] == "reused"
    assert reused["attempt"] == written["attempt"]
    assert source_request.source.read_bytes() == original
    output = root / written["job_id"] / written["attempt"] / "output"
    target = next(output.iterdir())
    target.write_bytes(b"altered")
    with pytest.raises(ValueError, match="scheduled_receipt_or_output_invalid"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )


def test_interrupted_attempt_is_preserved_and_next_attempt_can_complete(
    source_request: SourceRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "scheduler"
    real_operation = scheduled_normalization.operate_source

    def interrupted(*_args: object, **_kwargs: object) -> dict:
        raise KeyboardInterrupt

    monkeypatch.setattr(scheduled_normalization, "operate_source", interrupted)
    with pytest.raises(KeyboardInterrupt):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )
    job = next(path for path in root.iterdir() if path.is_dir())
    first_attempt = next(job.iterdir())
    monkeypatch.setattr(scheduled_normalization, "operate_source", real_operation)
    result = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    assert result["status"] == "written_local"
    assert first_attempt.exists()
    assert result["attempt"] != first_attempt.name


def test_locked_job_refuses_concurrent_execution(
    source_request: SourceRequest, tmp_path: Path
) -> None:
    root = tmp_path / "scheduler"
    root.mkdir()
    with closing(sqlite3.connect(root / ".scheduled-normalization.lock")) as owner:
        owner.execute("BEGIN EXCLUSIVE")
        with pytest.raises(ValueError, match="scheduled_lock_unavailable"):
            scheduled_normalization.run_scheduled_normalization(
                source_request, root, dry_run=False
            )
        assert not any(path.is_dir() for path in root.iterdir())


def test_failed_attempt_retains_receipt_and_can_be_retried(
    source_request: SourceRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "scheduler"
    original = scheduled_normalization.operate_source
    monkeypatch.setattr(
        scheduled_normalization,
        "operate_source",
        lambda *_args, **_kwargs: {
            "status": "failed",
            "error": "invalid_source_operation",
        },
    )
    failed = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    failure = root / failed["job_id"] / failed["attempt"] / "failure.json"
    assert json.loads(failure.read_text())["error"] == "invalid_source_operation"
    monkeypatch.setattr(scheduled_normalization, "operate_source", original)
    completed = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    assert completed["status"] == "written_local"
    assert failure.exists()


def test_source_size_and_attempt_limits_fail_closed(
    source_request: SourceRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "scheduler"
    monkeypatch.setattr(scheduled_normalization, "MAX_SOURCE_BYTES", 1)
    with pytest.raises(ValueError, match="scheduled_input_size_invalid"):
        scheduled_normalization.run_scheduled_normalization(source_request, root)
    assert not root.exists()
    monkeypatch.setattr(scheduled_normalization, "MAX_SOURCE_BYTES", 1024 * 1024)
    monkeypatch.setattr(scheduled_normalization, "MAX_ATTEMPTS", 1)
    job_id = scheduled_normalization.run_scheduled_normalization(source_request, root)[
        "job_id"
    ]
    job = root / job_id
    (job / "attempt-incomplete").mkdir(parents=True)
    with pytest.raises(ValueError, match="scheduled_attempt_limit_exceeded"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )
    assert (job / "attempt-incomplete").exists()


def test_runtime_change_does_not_reuse_old_output(
    source_request: SourceRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "scheduler"
    first = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    monkeypatch.setattr(
        scheduled_normalization, "_runtime_fingerprint", lambda: "different-runtime"
    )
    second = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    assert first["status"] == second["status"] == "written_local"
    assert first["job_id"] != second["job_id"]


def test_replay_rejects_changed_receipt_and_output_inventory(
    source_request: SourceRequest, tmp_path: Path
) -> None:
    root = tmp_path / "scheduler"
    result = scheduled_normalization.run_scheduled_normalization(
        source_request, root, dry_run=False
    )
    attempt = root / result["job_id"] / result["attempt"]
    receipt_path = attempt / "receipt.json"
    original = receipt_path.read_bytes()
    receipt_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="scheduled_receipt_or_output_invalid"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )
    receipt_path.write_bytes(original)
    extra = attempt / "output" / "unexpected"
    extra.write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="scheduled_receipt_or_output_invalid"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )


def test_invalid_state_and_lock_paths_are_rejected(
    source_request: SourceRequest, tmp_path: Path
) -> None:
    root = tmp_path / "scheduler"
    with pytest.raises(ValueError, match="scheduled_arguments_invalid"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=1
        )  # type: ignore[arg-type]
    root.mkdir()
    (root / ".scheduled-normalization.lock").mkdir()
    with pytest.raises(ValueError, match="scheduled_lock_invalid"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )


def test_replay_rejects_non_directory_attempt(
    source_request: SourceRequest, tmp_path: Path
) -> None:
    root = tmp_path / "scheduler"
    job_id = scheduled_normalization.run_scheduled_normalization(source_request, root)[
        "job_id"
    ]
    job = root / job_id
    job.mkdir(parents=True)
    (job / "invalid-attempt").write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="scheduled_attempt_invalid"):
        scheduled_normalization.run_scheduled_normalization(
            source_request, root, dry_run=False
        )


def test_cli_defaults_to_read_only_and_redacts_failures(
    source_request: SourceRequest, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "scheduler"
    args = [
        "health-appropriations-scheduled-normalize",
        "--source",
        str(source_request.source),
        "--job-root",
        str(root),
        "--profile",
        source_request.profile,
        "--expected-sha256",
        source_request.expected_sha256,
        "--source-vintage",
        source_request.source_vintage,
        "--source-locator",
        source_request.source_locator,
        "--observed-at",
        source_request.observed_at,
    ]
    assert app(args, exit_on_error=False, result_action="return_value") == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "dry_run"
    assert str(tmp_path) not in json.dumps(result)
    assert not root.exists()
    assert (
        app([*args, "--no-dry-run"], exit_on_error=False, result_action="return_value")
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "written_local"
    assert (
        app([*args, "--no-dry-run"], exit_on_error=False, result_action="return_value")
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "reused"
    args[args.index("--expected-sha256") + 1] = "0" * 64
    assert app(args, exit_on_error=False, result_action="return_value") == 2
    assert str(tmp_path) not in capsys.readouterr().out
