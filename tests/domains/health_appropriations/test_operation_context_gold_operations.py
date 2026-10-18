"""Typed input specification and read-only CLI/MCP operation Gold contracts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError
from tests.domains.health_appropriations.test_context_operation_canonical import CASES
from tests.domains.health_appropriations.test_operation_context_gold import _inputs

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import operation_context_gold as gold
from archive_govt_nz.mcp_server import call_tool, list_tools


def _spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    inputs, sources = _inputs(tmp_path, monkeypatch)
    spec = tmp_path / "inputs.json"
    spec.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-operation-context-inputs/v1",
                "inputs": [
                    {
                        "profile": item.profile,
                        "package_dir": str(item.package_dir),
                        "manifest_sha256": item.manifest_sha256,
                    }
                    for item in inputs
                ],
            }
        )
    )
    return spec, sources


def test_spec_is_closed_and_preserves_caller_pins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _spec(tmp_path, monkeypatch)
    parsed = gold.read_input_spec(spec)
    value = json.loads(spec.read_text())
    assert {item.manifest_sha256 for item in parsed} == {
        item["manifest_sha256"] for item in value["inputs"]
    }
    value["inputs"][0]["unexpected"] = "ignored?"
    spec.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="operation_context_gold_invalid"):
        gold.read_input_spec(spec)


def test_cli_build_verify_and_mcp_are_read_only_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec, sources = _spec(tmp_path, monkeypatch)
    output = tmp_path / "gold"
    common = ["--input-spec", str(spec), "--source-root", str(sources)]
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-build-operation-context-gold",
                *common,
                "--output-dir",
                str(output),
            ]
        )
    assert result.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "planned"
    assert not output.exists()
    receipt = call_tool(
        "health_appropriations_preflight_operation_context_gold",
        {
            "input_spec": str(spec),
            "source_root": str(sources),
            "output_dir": str(output),
        },
    )
    assert receipt["status"] == "planned"
    assert not output.exists()
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-build-operation-context-gold",
                *common,
                "--output-dir",
                str(output),
                "--write",
            ]
        )
    assert result.value.code == 0
    written = json.loads(capsys.readouterr().out)
    assert written["status"] == "complete"
    pin = written["manifest_sha256"]
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-verify-operation-context-gold",
                *common,
                "--package-dir",
                str(output),
                "--manifest-sha256",
                pin,
            ]
        )
    assert result.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "verified"
    query = call_tool(
        "health_appropriations_query_operation_context_gold",
        {
            "input_spec": str(spec),
            "source_root": str(sources),
            "package_dir": str(output),
            "manifest_sha256": pin,
            "limit": 2,
        },
    )
    assert query["status"] == "verified"
    assert len(query["rows"]) == 2
    for name in gold.MCP_OPERATIONS:
        definition = next(item for item in list_tools() if item["name"] == name)
        assert definition["annotations"]["readOnlyHint"] is True
        assert definition["annotations"]["destructiveHint"] is False
        assert "write" not in definition["inputSchema"]["properties"]


def test_spec_inspection_does_not_require_plotting_runtime(tmp_path: Path) -> None:
    path = tmp_path / "inputs.json"
    value = {
        "schema_version": "archive-govt-nz.health-operation-context-inputs/v1",
        "inputs": [
            {
                "profile": case.profile,
                "package_dir": f"package-{index}",
                "manifest_sha256": "a" * 64,
            }
            for index, case in enumerate(CASES)
        ],
    }
    path.write_text(json.dumps(value))
    before = path.read_bytes()
    code = """import importlib.abc
import json
import sys
from pathlib import Path
class NoPlotting(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'matplotlib' or fullname.startswith('matplotlib.'):
            raise ModuleNotFoundError('plotting_not_part_of_input_inspection')
sys.meta_path.insert(0, NoPlotting())
from archive_govt_nz.domains.health_appropriations.operation_context_gold import read_input_spec
items = read_input_spec(Path(sys.argv[1]))
print(json.dumps({item.profile: item.manifest_sha256 for item in items}, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {case.profile: "a" * 64 for case in CASES}
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_input_spec_refuses_fifo_without_blocking(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("POSIX FIFO is unavailable")
    path = tmp_path / "inputs.fifo"
    os.mkfifo(path)
    code = """import sys
from pathlib import Path
from typing import Any
from archive_govt_nz.domains.health_appropriations.operation_context_gold import read_input_spec
try:
    read_input_spec(Path(sys.argv[1]))
except ValueError:
    print('rejected')
else:
    raise SystemExit(2)
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    finally:
        path.unlink()
    assert result.returncode == 0
    assert result.stdout.strip() == "rejected"


@pytest.mark.parametrize(
    "invalid",
    [
        "duplicate_key",
        "oversize",
        "directory",
        "missing_profile",
        "duplicate_profile",
        "invalid_pin",
    ],
)
def test_input_spec_refuses_malformed_or_nonregular_config(
    tmp_path: Path, invalid: str
) -> None:
    path = tmp_path / "inputs.json"
    value: dict[str, Any] = {
        "schema_version": "archive-govt-nz.health-operation-context-inputs/v1",
        "inputs": [
            {
                "profile": case.profile,
                "package_dir": f"package-{index}",
                "manifest_sha256": "a" * 64,
            }
            for index, case in enumerate(CASES)
        ],
    }
    if invalid == "directory":
        path.mkdir()
    else:
        if invalid == "missing_profile":
            value["inputs"].pop()
        elif invalid == "duplicate_profile":
            value["inputs"][-1] = value["inputs"][0]
        elif invalid == "invalid_pin":
            value["inputs"][0]["manifest_sha256"] = "not-a-pin"
        payload = json.dumps(value)
        if invalid == "duplicate_key":
            payload = '{"schema_version":"wrong",' + payload[1:]
        elif invalid == "oversize":
            payload = payload.ljust(65537)
        path.write_text(payload)
    with pytest.raises(ValueError, match="operation_context_gold_invalid"):
        gold.read_input_spec(path)


def test_cli_and_mcp_reject_untyped_flags_before_source_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(_path: Path) -> None:
        pytest.fail("invalid typed inputs reached the source reader")

    monkeypatch.setattr(gold, "read_input_spec", forbidden)
    args: dict[str, Any] = {
        "input_spec": str(tmp_path / "missing-inputs"),
        "source_root": str(tmp_path / "missing-source"),
        "output_dir": str(tmp_path / "output"),
        "write": True,
    }
    with pytest.raises(ValidationError):
        call_tool("health_appropriations_preflight_operation_context_gold", args)
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-query-operation-context-gold",
                "--input-spec",
                args["input_spec"],
                "--source-root",
                args["source_root"],
                "--package-dir",
                args["output_dir"],
                "--manifest-sha256",
                "a" * 64,
                "--limit",
                "201",
            ]
        )
    assert result.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
