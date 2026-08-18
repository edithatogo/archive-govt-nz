"""Contract tests verifying parity between CLI outputs and MCP server tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.cli import capabilities, doctor, legislation, sources
from archive_govt_nz.mcp_server import (
    call_tool,
    get_server_metadata,
    list_resources,
    list_tools,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_mcp_metadata_and_capabilities() -> None:
    """Verify MCP metadata conforms to specification."""
    meta = get_server_metadata()
    assert meta["name"] == "archive-govt-nz-mcp"
    assert meta["protocol_version"] == "2024-11-05"
    assert "tools" in meta["capabilities"]
    assert "resources" in meta["capabilities"]

    tools = list_tools()
    assert len(tools) >= 5
    tool_names = {t["name"] for t in tools}
    assert "archive_doctor" in tool_names
    assert "archive_capabilities" in tool_names
    assert "archive_sources" in tool_names

    resources = list_resources()
    assert len(resources) >= 3
    uris = {r["uri"] for r in resources}
    assert "archive://capabilities" in uris
    assert "archive://sources" in uris


def test_doctor_parity_cli_and_mcp(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify archive doctor outputs identical schema in CLI and MCP."""
    doctor(format="json")
    captured = capsys.readouterr()
    cli_out = json.loads(captured.out)

    mcp_out = call_tool("archive_doctor")
    assert cli_out["status"] == mcp_out["status"]
    assert cli_out["python_version"] == mcp_out["python_version"]


def test_capabilities_parity_cli_and_mcp(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify capabilities outputs identical list in CLI and MCP."""
    capabilities(format="json")
    captured = capsys.readouterr()
    cli_out = json.loads(captured.out)

    mcp_out = call_tool("archive_capabilities")
    assert cli_out["capabilities"] == mcp_out["capabilities"]
    assert cli_out["count"] == mcp_out["count"]


def test_sources_parity_cli_and_mcp(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify registered sources count parity in CLI and MCP."""
    sources(format="json", registry_path=str(tmp_path))
    captured = capsys.readouterr()
    cli_out = json.loads(captured.out)

    mcp_out = call_tool("archive_sources", {"registry_path": str(tmp_path)})
    assert cli_out["registered_sources_count"] == mcp_out["registered_sources_count"]


def test_verify_and_provenance_mcp_tool() -> None:
    """Verify verify and provenance tool calls."""
    verify_out = call_tool("archive_verify")
    assert verify_out["status"] == "passed"
    assert verify_out["integrity_checks_passed"] == 19

    prov_out = call_tool("archive_provenance")
    assert prov_out["ledger_status"] == "synced"
    assert prov_out["entities_tracked"] == 350


def test_legislation_parity_cli_and_mcp(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify legislation parity in CLI and MCP."""
    legislation(action="coverage", format="json")
    captured = capsys.readouterr()
    cli_out = json.loads(captured.out)

    mcp_out = call_tool("archive_legislation")
    assert cli_out["coverage_percent"] == mcp_out["coverage_percent"]
    assert cli_out["candidate_works_count"] == mcp_out["candidate_works_count"]


def test_unknown_mcp_tool_raises_error() -> None:
    """Verify calling an unknown tool raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool: invalid_tool"):
        call_tool("invalid_tool")
