# SPDX-License-Identifier: Apache-2.0
"""Pinned read-only CLI/MCP source-layout reconciliation contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations.source_layout_operations import (
    MAX_INPUT_BYTES,
)
from archive_govt_nz.mcp_server import call_tool, list_tools

TRACK = (
    Path(__file__).resolve().parents[3]
    / "conductor"
    / "tracks"
    / "health_appropriations_medallion_assimilation_20260829"
)
TOOL = "health_appropriations_reconcile_source_layout"


def _inputs(tmp_path: Path, *, include_text: bool = False) -> dict[str, str]:
    sources = {
        "census": TRACK / "source-census.json",
        "workbook_baseline": TRACK / "source-layout-baseline-20261003.json",
        "pdf_baseline": TRACK / "source-pdf-layout-baseline-20261018.json",
        "workbook_recheck": TRACK / "source-layout-baseline-20261003.json",
        "pdf_recheck": TRACK / "source-pdf-layout-baseline-20261018.json",
    }
    if include_text:
        sources.update(
            {
                "text_baseline": TRACK / "source-text-layout-baseline-20261026.json",
                "text_recheck": TRACK / "source-text-layout-baseline-20261026.json",
            }
        )
    arguments: dict[str, str] = {}
    for name, source in sources.items():
        target = tmp_path / f"{name}.json"
        payload = source.read_bytes()
        target.write_bytes(payload)
        arguments[name] = str(target)
        arguments[f"{name}_sha256"] = hashlib.sha256(payload).hexdigest()
    return arguments


def test_cli_and_mcp_return_the_same_compact_read_only_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    arguments = _inputs(tmp_path)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    mcp = call_tool(TOOL, arguments)
    command = ["health-appropriations-reconcile-source-layout"]
    for key, value in arguments.items():
        command.extend(["--" + key.replace("_", "-"), value])
    assert app(command, exit_on_error=False, result_action="return_value") == 0
    cli = json.loads(capsys.readouterr().out)

    assert mcp == cli
    assert mcp["schema_version"] == "archive-govt-nz.health-source-layout-operation/v1"
    assert mcp["status"] == "reconciled"
    assert mcp["summary"]["captured_source_count"] == 75
    assert mcp["summary"]["sources_without_structural_baseline"] == 10
    assert len(mcp["unassessed_sources"]) == 10
    assert len(mcp["source_ids"]) == 75
    assert mcp["source_ids"] == sorted(mcp["source_ids"])
    assert all("url" not in row for row in mcp["unassessed_sources"])
    assert all("sha256" in row for row in mcp["inputs"].values())
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_tool_is_declared_read_only_with_closed_typed_arguments() -> None:
    tool = next(item for item in list_tools() if item["name"] == TOOL)
    assert tool["annotations"]["readOnlyHint"] is True
    assert tool["inputSchema"]["additionalProperties"] is False
    assert {"census", "census_sha256", "pdf_recheck", "pdf_recheck_sha256"} <= set(
        tool["inputSchema"]["required"]
    )
    assert tool["outputSchema"]["properties"]["status"] == {"const": "reconciled"}


def test_bad_pin_and_unpaired_text_report_fail_without_disclosing_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    arguments = _inputs(tmp_path)
    arguments["census_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="input_digest_mismatch"):
        call_tool(TOOL, arguments)

    arguments = _inputs(tmp_path)
    arguments["text_baseline"] = str(tmp_path / "private path.json")
    arguments["text_baseline_sha256"] = "a" * 64
    command = ["health-appropriations-reconcile-source-layout"]
    for key, value in arguments.items():
        command.extend(["--" + key.replace("_", "-"), value])
    assert app(command, exit_on_error=False, result_action="return_value") == 2
    output = capsys.readouterr().out
    receipt = json.loads(output)
    assert receipt["status"] == "failed"
    assert receipt["error"] == "text_layout_recheck_required"
    assert "private path" not in output


def test_optional_text_layout_pair_is_pinned_and_reconciled(tmp_path: Path) -> None:
    arguments = _inputs(tmp_path, include_text=True)
    receipt = call_tool(TOOL, arguments)

    assert receipt["summary"]["text_layout_source_count"] == 4
    assert (
        receipt["inputs"]["text_baseline"]["sha256"]
        == arguments["text_baseline_sha256"]
    )
    assert "text" in receipt["pinned_reports"]


def test_non_regular_and_oversized_inputs_fail_without_path_disclosure(
    tmp_path: Path,
) -> None:
    arguments = _inputs(tmp_path)
    source = tmp_path / "private source.json"
    source.write_text("{}", encoding="utf-8")
    link = tmp_path / "linked-census.json"
    link.symlink_to(source)
    arguments["census"] = str(link)

    with pytest.raises(ValueError, match="input_not_regular_file") as symlink_error:
        call_tool(TOOL, arguments)
    assert str(link) not in str(symlink_error.value)

    oversized = tmp_path / "oversized.json"
    with oversized.open("wb") as stream:
        stream.truncate(MAX_INPUT_BYTES + 1)
    arguments["census"] = str(oversized)
    arguments["census_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="input_size_invalid") as size_error:
        call_tool(TOOL, arguments)
    assert str(oversized) not in str(size_error.value)


def test_unpaired_optional_digest_is_rejected(tmp_path: Path) -> None:
    arguments = _inputs(tmp_path)
    arguments["text_baseline_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="input_pin_pair_required"):
        call_tool(TOOL, arguments)
