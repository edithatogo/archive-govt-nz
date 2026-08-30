"""Tests for dynamic FastMCP domain dataset tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.mcp_server import call_tool, list_tools

if TYPE_CHECKING:
    from pathlib import Path


def test_list_tools_includes_domain_tools() -> None:
    """Verify list_tools exposes archive_domain_list and archive_domain_schema."""
    tools = list_tools()
    tool_names = {t["name"] for t in tools}
    assert "archive_domain_list" in tool_names
    assert "archive_domain_schema" in tool_names
    assert "health_appropriations_status" in tool_names


def test_call_archive_domain_list() -> None:
    """Verify archive_domain_list returns every registered domain."""
    res = call_tool("archive_domain_list")
    assert res["count"] == 8
    assert len(res["domains"]) == 8
    assert "legislation" in res["domains"]
    assert "gazette" in res["domains"]
    assert "hansard" in res["domains"]
    assert len(res["datasets"]) == 8


def test_call_archive_domain_schema() -> None:
    """Verify archive_domain_schema returns field metadata for a requested domain."""
    res = call_tool("archive_domain_schema", {"domain": "gazette"})
    assert res["domain"] == "gazette"
    assert res["title"] == "New Zealand Gazette Official Notices"
    field_names = {f["name"] for f in res["fields"]}
    assert "notice_id" in field_names
    assert "record_urn" in field_names


def test_call_health_appropriations_status(tmp_path: Path) -> None:
    """Expose bounded local state through a read-only MCP tool."""
    result = call_tool("health_appropriations_status", {"archive_root": str(tmp_path)})
    assert result["status"] == "no_state"
    assert result["archive_root"] == str(tmp_path)

    manifest = tmp_path / "manifests" / "donor-abcdef0.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"schema_version": "donor/v1", "file_count": 23, "total_bytes": 10}),
        encoding="utf-8",
    )
    assert (
        call_tool("health_appropriations_status", {"archive_root": str(tmp_path)})[
            "status"
        ]
        == "partial"
    )
