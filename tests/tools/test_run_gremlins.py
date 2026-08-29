"""Tests for the bounded pytest-gremlins runner."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "run_gremlins.py"
_SPEC = importlib.util.spec_from_file_location("run_gremlins", _TOOL_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
gremlins: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gremlins)


def _configure_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gremlins, "ROOT", tmp_path)
    monkeypatch.setattr(gremlins, "PLUGIN_REPORT", tmp_path / "plugin.json")
    monkeypatch.setattr(gremlins, "REPORT_OUTPUT", tmp_path / "build" / "receipt.json")
    for target in gremlins.TARGETS:
        path = tmp_path / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pass\n", encoding="utf-8")


def _write_plugin_report(
    *, survived: int = 0, error: int = 0, timeout: int = 0, pardoned: int = 0
) -> None:
    zapped = 1 - survived
    gremlins.PLUGIN_REPORT.write_text(
        json.dumps(
            {
                "summary": {
                    "total": 1,
                    "zapped": zapped,
                    "survived": survived,
                    "timeout": timeout,
                    "error": error,
                    "pardoned": pardoned,
                    "percentage": 100.0 if zapped == 1 else 0.0,
                },
                "files": {},
                "results": [{"status": "zapped" if zapped == 1 else "survived"}],
            }
        ),
        encoding="utf-8",
    )


def _write_raw_plugin_report(payload: object) -> None:
    gremlins.PLUGIN_REPORT.write_text(json.dumps(payload), encoding="utf-8")


def test_targets_exist() -> None:
    """Every bounded mutation target must exist in the repository."""
    for target in gremlins.TARGETS:
        assert (gremlins.ROOT / target).is_file()
    for test_path in gremlins.TEST_PATHS:
        assert (gremlins.ROOT / test_path).is_file()


def test_success_writes_bounded_atomic_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid clean mutation report becomes a passing bounded receipt."""
    _configure_paths(tmp_path, monkeypatch)

    def fake_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        _write_plugin_report()
        assert "--gremlin-clear-cache" in command
        assert "addopts=" not in command
        assert all(test_path in command for test_path in gremlins.TEST_PATHS)
        return subprocess.CompletedProcess(command, 0, "sensitive output", "")

    monkeypatch.setattr(gremlins.subprocess, "run", fake_run)

    receipt = gremlins.run_gremlins_suite(timeout_seconds=17, clear_cache=True)

    assert receipt["status"] == "passed"
    assert receipt["returncode"] == 0
    assert receipt["cache_mode"] == "cleared"
    assert receipt["stdout_sha256"] == hashlib.sha256(b"sensitive output").hexdigest()
    assert "sensitive output" not in gremlins.REPORT_OUTPUT.read_text(encoding="utf-8")
    assert not gremlins.REPORT_OUTPUT.with_suffix(".json.tmp").exists()


def test_missing_target_emits_failed_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing configured source must fail closed with a structured receipt."""
    _configure_paths(tmp_path, monkeypatch)
    (tmp_path / gremlins.TARGETS[0]).unlink()

    receipt = gremlins.run_gremlins_suite()

    assert receipt["status"] == "failed"
    assert receipt["returncode"] == 1
    assert receipt["failure_kind"] == "missing_target"
    assert json.loads(gremlins.REPORT_OUTPUT.read_text(encoding="utf-8")) == receipt


def test_missing_plugin_report_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A zero pytest exit cannot pass without the plugin's JSON evidence."""
    _configure_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        gremlins.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )

    receipt = gremlins.run_gremlins_suite()

    assert receipt["status"] == "failed"
    assert receipt["returncode"] == 1
    assert receipt["failure_kind"] == "invalid_plugin_report"


def test_surviving_mutant_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A survivor must fail even if pytest incorrectly exits zero."""
    _configure_paths(tmp_path, monkeypatch)

    def fake_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        _write_plugin_report(survived=1)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(gremlins.subprocess, "run", fake_run)

    receipt = gremlins.run_gremlins_suite()

    assert receipt["status"] == "failed"
    assert receipt["returncode"] == 1
    assert receipt["failure_kind"] == "mutation_gate_failed"


def test_timeout_emits_code_124(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An over-budget subprocess must emit a receipt and return code 124."""
    _configure_paths(tmp_path, monkeypatch)

    def fake_run(command: list[str], **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(command, 3, output="partial", stderr="late")

    monkeypatch.setattr(gremlins.subprocess, "run", fake_run)

    receipt = gremlins.run_gremlins_suite(timeout_seconds=3)

    assert receipt["status"] == "failed"
    assert receipt["returncode"] == 124
    assert receipt["failure_kind"] == "timeout"
    assert "partial" not in gremlins.REPORT_OUTPUT.read_text(encoding="utf-8")


def test_runner_rejects_nonpositive_timeout() -> None:
    """Programmatic callers cannot disable the timeout boundary."""
    with pytest.raises(ValueError, match="must be positive"):
        gremlins.run_gremlins_suite(timeout_seconds=0)


def test_argument_timeout_parser_and_byte_digest() -> None:
    """CLI timeout parsing and byte-output hashing preserve their contracts."""
    assert gremlins._positive_integer("7") == 7
    with pytest.raises(gremlins.argparse.ArgumentTypeError):
        gremlins._positive_integer("-1")
    assert gremlins._output_digest(b"bytes") == hashlib.sha256(b"bytes").hexdigest()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "must be an object"),
        ({"files": {}, "results": []}, "lacks summary or results"),
        (
            {"summary": {}, "results": [], "files": []},
            "lacks its file breakdown",
        ),
    ],
)
def test_plugin_report_rejects_invalid_envelopes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
    message: str,
) -> None:
    """Wrong JSON envelope types fail before producing mutation evidence."""
    _configure_paths(tmp_path, monkeypatch)
    _write_raw_plugin_report(payload)

    with pytest.raises(TypeError, match=message):
        gremlins._load_plugin_summary()


def test_plugin_report_rejects_malformed_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Malformed plugin JSON is never treated as an empty clean report."""
    _configure_paths(tmp_path, monkeypatch)
    gremlins.PLUGIN_REPORT.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed JSON"):
        gremlins._load_plugin_summary()


@pytest.mark.parametrize("percentage", [True, "100", -1, 101])
def test_plugin_report_rejects_invalid_percentage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    percentage: object,
) -> None:
    """Percentage must be numeric, non-boolean, and within its domain."""
    _configure_paths(tmp_path, monkeypatch)
    _write_raw_plugin_report(
        {
            "summary": {
                "total": 0,
                "zapped": 0,
                "survived": 0,
                "timeout": 0,
                "error": 0,
                "pardoned": 0,
                "percentage": percentage,
            },
            "files": {},
            "results": [],
        }
    )

    with pytest.raises(ValueError, match="percentage is invalid"):
        gremlins._load_plugin_summary()


@pytest.mark.parametrize("count", [True, "1", -1])
def test_plugin_report_rejects_invalid_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: object
) -> None:
    """Aggregate counts must be nonnegative integers and never booleans."""
    _configure_paths(tmp_path, monkeypatch)
    _write_raw_plugin_report(
        {
            "summary": {
                "total": count,
                "zapped": 0,
                "survived": 0,
                "timeout": 0,
                "error": 0,
                "pardoned": 0,
                "percentage": 0,
            },
            "files": {},
            "results": [],
        }
    )

    with pytest.raises(ValueError, match="field 'total' is invalid"):
        gremlins._load_plugin_summary()


def test_plugin_report_rejects_total_result_disagreement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aggregate totals must reconcile to the detailed result count."""
    _configure_paths(tmp_path, monkeypatch)
    _write_raw_plugin_report(
        {
            "summary": {
                "total": 1,
                "zapped": 1,
                "survived": 0,
                "timeout": 0,
                "error": 0,
                "pardoned": 0,
                "percentage": 100,
            },
            "files": {},
            "results": [],
        }
    )

    with pytest.raises(ValueError, match="total disagrees"):
        gremlins._load_plugin_summary()


@pytest.mark.parametrize(
    ("summary_changes", "process_returncode"),
    [
        ({"total": 0, "zapped": 0, "percentage": 100.0}, 0),
        ({"timeout": 1}, 0),
        ({"error": 1}, 0),
        ({"pardoned": 1}, 0),
        ({}, 2),
    ],
)
def test_mutation_gate_rejects_every_nonclean_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    summary_changes: dict[str, object],
    process_returncode: int,
) -> None:
    """Every incomplete mutation outcome and nonzero process status fails."""
    _configure_paths(tmp_path, monkeypatch)

    def fake_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        report = {
            "summary": {
                "total": 1,
                "zapped": 1,
                "survived": 0,
                "timeout": 0,
                "error": 0,
                "pardoned": 0,
                "percentage": 100.0,
            },
            "files": {},
            "results": [{"status": "zapped"}],
        }
        report["summary"].update(summary_changes)
        if report["summary"]["total"] == 0:
            report["results"] = []
        _write_raw_plugin_report(report)
        return subprocess.CompletedProcess(command, process_returncode, "", "")

    monkeypatch.setattr(gremlins.subprocess, "run", fake_run)

    receipt = gremlins.run_gremlins_suite()

    assert receipt["status"] == "failed"
    assert receipt["returncode"] != 0
    assert receipt["failure_kind"] == "mutation_gate_failed"


def test_nonzero_process_with_invalid_report_preserves_returncode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid evidence must not hide the underlying pytest failure code."""
    _configure_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        gremlins.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 2, "", ""),
    )

    receipt = gremlins.run_gremlins_suite()

    assert receipt["returncode"] == 2
    assert receipt["failure_kind"] == "invalid_plugin_report"


def test_main_prints_receipt_and_returns_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI main path forwards arguments and emits its bounded receipt."""
    receipt = gremlins.GremlinReceipt(
        schema_version=gremlins.SCHEMA_VERSION,
        status="failed",
        returncode=23,
        targets=list(gremlins.TARGETS),
        timeout_seconds=9,
        cache_mode="cleared",
        stdout_sha256=gremlins._output_digest(None),
        stderr_sha256=gremlins._output_digest(None),
    )
    monkeypatch.setattr(
        sys, "argv", ["run_gremlins.py", "--timeout-seconds", "9", "--clear-cache"]
    )
    monkeypatch.setattr(gremlins, "run_gremlins_suite", lambda **_kwargs: receipt)

    assert gremlins.main() == 23
    assert json.loads(capsys.readouterr().out) == receipt


def test_cli_help_does_not_start_mutation() -> None:
    """The help path must terminate before invoking the mutation engine."""
    result = subprocess.run(
        [sys.executable, "tools/run_gremlins.py", "--help"],
        cwd=gremlins.ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--timeout-seconds" in result.stdout
    assert "--clear-cache" in result.stdout
