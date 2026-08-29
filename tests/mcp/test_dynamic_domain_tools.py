"""Tests for dynamic FastMCP domain dataset tools."""

from __future__ import annotations

from archive_govt_nz.mcp_server import call_tool, list_tools


def test_list_tools_includes_domain_tools() -> None:
    """Verify list_tools exposes archive_domain_list and archive_domain_schema."""
    tools = list_tools()
    tool_names = {t["name"] for t in tools}
    assert "archive_domain_list" in tool_names
    assert "archive_domain_schema" in tool_names


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
