"""User-facing resume operations reuse pinned native contracts without promotion."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.test_resume_execution import _files, _inputs

from archive_govt_nz import mcp_server
from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import (
    rebuild_resume,
    resume_execution,
)
from archive_govt_nz.domains.health_appropriations import resume_operations as ops


def arguments(tmp_path: Path) -> dict:
    """Reuse the existing four-original synthetic recovery fixture."""
    return {
        key: str(value) if isinstance(value, Path) else value
        for key, value in _inputs(tmp_path).items()
    }


def planning(args: dict) -> dict:
    """Select only planner inputs, without an executor output or plan pin."""
    return {
        key: value
        for key, value in args.items()
        if key not in {"resume_plan", "resume_plan_sha256"}
    }


def cli_args(operation: str, args: dict) -> list[str]:
    """Build actual CLI tokens rather than bypassing argument parsing."""
    tokens = ["health-appropriations-" + operation]
    for key, value in args.items():
        if key == "stage_manifest_sha256":
            for stage, digest in value.items():
                tokens.extend(["--stage-pin", stage + "=" + digest])
        else:
            tokens.extend(["--" + key.replace("_", "-"), str(value)])
    return tokens


def test_plan_cli_mcp_api_parity_no_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Native plan bytes remain saveable and do not start execution."""
    args = planning(arguments(tmp_path))
    before = _files(tmp_path)
    native: dict[str, Any] = {
        key: Path(value) if key in ops.PATH_FIELDS else value
        for key, value in args.items()
    }
    expected = rebuild_resume.plan_resume(**native)
    assert (
        app(
            cli_args("plan-resume", args),
            exit_on_error=False,
            result_action="return_value",
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result == expected
    assert mcp_server.call_tool("health_appropriations_plan_resume", args) == result
    assert result["execution"] == "not_performed"
    assert _files(tmp_path) == before


def test_explicit_cli_execution_and_readonly_verifier(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default is no-write; explicit execution yields a separately verified envelope."""
    args = {**arguments(tmp_path), "output_dir": str(tmp_path / "attempt")}
    before = _files(tmp_path)
    assert (
        app(cli_args("resume", args), exit_on_error=False, result_action="return_value")
        == 0
    )
    assert json.loads(capsys.readouterr().out)["execution"] == "not_performed"
    assert _files(tmp_path) == before
    assert not (tmp_path / "attempt").exists()
    assert (
        app(
            [*cli_args("resume", args), "--no-dry-run"],
            exit_on_error=False,
            result_action="return_value",
        )
        == 0
    )
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "passed"
    for name, payload in before.items():
        assert (tmp_path / name).read_bytes() == payload
    verify = {
        "attempt": args["output_dir"],
        "store_root": args["store_root"],
        "receipt_sha256": hashlib.sha256(
            (tmp_path / "attempt/RESUME_RECEIPT.json").read_bytes()
        ).hexdigest(),
    }

    def forbidden(**_kwargs: object) -> dict:
        pytest.fail("verification invoked planning or execution")

    monkeypatch.setattr(ops, "execute_resume", forbidden)
    monkeypatch.setattr(ops, "plan_resume", forbidden)
    completed = _files(tmp_path)
    assert (
        app(
            cli_args("verify-resume", verify),
            exit_on_error=False,
            result_action="return_value",
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == receipt
    assert (
        mcp_server.call_tool("health_appropriations_verify_resume", verify) == receipt
    )
    assert _files(tmp_path) == completed


@pytest.mark.parametrize(
    "fault",
    [
        "donor_manifest_sha256",
        "previous_plan_sha256",
        "resume_plan_sha256",
        "output_collision",
    ],
)
def test_bad_execution_inputs_preserve_state(tmp_path: Path, fault: str) -> None:
    """Bad pins or an occupied destination never authorize replacing state."""
    args = {
        **arguments(tmp_path),
        "output_dir": str(tmp_path / "attempt"),
        "dry_run": False,
    }
    if fault == "output_collision":
        (tmp_path / "attempt").mkdir()
        (tmp_path / "attempt/keep").write_bytes(b"original")
    else:
        args[fault] = "0" * 64
    before = _files(tmp_path)
    result = ops.invoke("resume", args)
    assert result == ops.FAILURE
    assert _files(tmp_path) == before


@pytest.mark.parametrize(
    "tokens",
    [
        ["budget=" + "a" * 64] * 2,
        ["unknown=" + "a" * 64],
        ["budget=private"],
        ["private"],
        ["x"] * 5,
    ],
)
def test_bad_stage_arguments_fail_closed(tokens: list[str]) -> None:
    """Explicit stage pins are bounded and duplicate-rejecting, never last-wins."""
    with pytest.raises(ValueError, match="invalid_resume_operation"):
        ops.stage_pins(tuple(tokens))


def test_no_mcp_executor_and_no_write_flags(tmp_path: Path) -> None:
    """MCP registrations cannot turn plan inspection into execution."""
    assert "health_appropriations_resume" not in {
        t["name"] for t in mcp_server.list_tools()
    }
    args = {**planning(arguments(tmp_path)), "dry_run": False}
    with pytest.raises(ValueError, match="invalid_resume_operation"):
        mcp_server.call_tool("health_appropriations_plan_resume", args)


def rpc(name: str, args: dict) -> dict:
    """Use initialized MCP protocol, not only direct dispatch."""
    server = mcp_server.Server()
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": mcp_server.PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "fixture", "version": "1"},
            },
        }
    )
    server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    result = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": args},
        }
    )
    assert result is not None
    return result


def test_mcp_protocol_preserves_plan_and_redacts_failures(tmp_path: Path) -> None:
    """Protocol results distinguish bad arguments and failed local verification."""
    args = planning(arguments(tmp_path))
    response = rpc("health_appropriations_plan_resume", args)["result"]
    assert response["isError"] is False
    assert json.loads(response["content"][0]["text"]) == response["structuredContent"]
    assert response["structuredContent"] == ops.invoke("plan-resume", args)
    response = rpc(
        "health_appropriations_plan_resume", {**args, "private-extra": "private-value"}
    )
    assert response["error"]["code"] == -32602
    assert response["error"]["message"] == "Invalid resume operation arguments"
    bad = {
        "attempt": str(tmp_path / "private-missing"),
        "store_root": args["store_root"],
        "receipt_sha256": "0" * 64,
    }
    response = rpc("health_appropriations_verify_resume", bad)["result"]
    assert response["isError"] is True
    assert response["content"] == [{"type": "text", "text": "invalid_resume_operation"}]


def test_repeated_stage_flags_and_failure_exit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI preserves unique stage pins and rejects duplicate flags with JSON exit 2."""
    args = planning(arguments(tmp_path))
    args["stage_manifest_sha256"] = {"budget": "a" * 64, "historical": "b" * 64}
    tokens = cli_args("plan-resume", args)
    assert app(tokens, exit_on_error=False, result_action="return_value") == 0
    assert (
        json.loads(capsys.readouterr().out)["stage_manifest_sha256"]
        == args["stage_manifest_sha256"]
    )
    before = _files(tmp_path)
    assert (
        app(
            [*tokens, "--stage-pin", "budget=" + "a" * 64],
            exit_on_error=False,
            result_action="return_value",
        )
        == 2
    )
    assert json.loads(capsys.readouterr().out) == ops.FAILURE
    assert _files(tmp_path) == before


def test_cli_plan_bytes_are_consumable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Saving stdout and pinning its exact bytes works without stripping an envelope."""
    args = arguments(tmp_path)
    assert (
        app(
            cli_args("plan-resume", planning(args)),
            exit_on_error=False,
            result_action="return_value",
        )
        == 0
    )
    payload = capsys.readouterr().out.encode()
    path = tmp_path / "saved-plan.json"
    path.write_bytes(payload)
    args.update(
        resume_plan=str(path),
        resume_plan_sha256=hashlib.sha256(payload).hexdigest(),
        output_dir=str(tmp_path / "new"),
    )
    assert ops.invoke("resume", args)["status"] == "planned"
    assert not (tmp_path / "new").exists()
    path.write_bytes(payload + b" ")
    assert ops.invoke("resume", args) == ops.FAILURE
    assert not (tmp_path / "new").exists()


def test_partial_attempt_and_interrupt_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLI boundary retains failure evidence and never converts interruption to success."""
    args = {
        **arguments(tmp_path),
        "output_dir": str(tmp_path / "attempt"),
        "dry_run": False,
    }

    def fail(name: str, run: Path, *_args: object) -> None:
        (run / name).mkdir()
        (run / name / "partial").write_bytes(b"retained")
        message = "private"
        raise KeyboardInterrupt(message)

    monkeypatch.setattr(resume_execution, "_extract", fail)
    with pytest.raises(KeyboardInterrupt):
        ops.invoke("resume", args)
    assert (tmp_path / "attempt/run/budget/partial").read_bytes() == b"retained"
    assert (tmp_path / "attempt/FAILURE.json").is_file()
    assert not (tmp_path / "attempt/RESUME_RECEIPT.json").exists()
    assert "private" not in (tmp_path / "attempt/FAILURE.json").read_text()


@pytest.mark.parametrize("dry_run", [0, 1, "false", None])
def test_nonboolean_execution_flag(tmp_path: Path, dry_run: object) -> None:
    """Only an actual false flag may authorize local execution."""
    args = {
        **arguments(tmp_path),
        "output_dir": str(tmp_path / "attempt"),
        "dry_run": dry_run,
    }
    before = _files(tmp_path)
    assert ops.invoke("resume", args) == ops.FAILURE
    assert _files(tmp_path) == before


def test_exact_stage_bound() -> None:
    """All four explicitly pinned stages are accepted at the exact CLI limit."""
    expected = dict.fromkeys(ops.PROFILES, "a" * 64)
    assert (
        ops.stage_pins(tuple(name + "=" + digest for name, digest in expected.items()))
        == expected
    )


def test_input_shape_checked_before_native_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid arguments cannot reach the native reader even if it accepts kwargs."""
    calls = []

    def observed(**kwargs: object) -> dict:
        calls.append(kwargs)
        return {}

    args = {**planning(arguments(tmp_path)), "output_dir": "private-unexpected"}
    monkeypatch.setattr(ops, "plan_resume", observed)
    assert ops.invoke("plan-resume", args) == ops.FAILURE
    assert calls == []
