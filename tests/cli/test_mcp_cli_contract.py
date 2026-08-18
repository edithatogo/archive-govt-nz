"""Contract tests verifying parity between CLI outputs and MCP server tools."""

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.cli import capabilities, doctor, sources
from archive_govt_nz.mcp_server import (
    Server,
    StdioServerTransport,
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
    assert len(tools) >= 4
    tool_names = {t["name"] for t in tools}
    assert "archive_doctor" in tool_names
    assert "archive_capabilities" in tool_names
    assert "archive_sources" in tool_names
    assert "archive_status" in tool_names

    resources = list_resources()
    assert len(resources) >= 3
    uris = {r["uri"] for r in resources}
    assert "archive://capabilities" in uris
    assert "archive://sources" in uris


def test_stdio_server_transport() -> None:
    """Verify StdioServerTransport reads and writes JSON-RPC messages."""
    fake_in = io.StringIO('{"jsonrpc": "2.0", "method": "initialize"}\n')
    fake_out = io.StringIO()
    transport = StdioServerTransport(stdin=fake_in, stdout=fake_out)

    msg = transport.read_message()
    assert msg == {"jsonrpc": "2.0", "method": "initialize"}

    transport.write_message({"jsonrpc": "2.0", "id": 1, "result": {}})
    assert '"jsonrpc": "2.0"' in fake_out.getvalue()

    # Empty read
    assert transport.read_message() is None


def test_mcp_server_json_rpc_dispatch() -> None:
    """Verify MCP Server handles JSON-RPC 2.0 protocol requests."""
    server = Server()

    # 1. initialize
    init_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }
    )
    assert init_res["id"] == 1
    assert init_res["result"]["serverInfo"]["name"] == "archive-govt-nz-mcp"

    # 2. tools/list
    list_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
        }
    )
    assert "tools" in list_res["result"]

    # 3. resources/list
    res_list = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
        }
    )
    assert "resources" in res_list["result"]

    # 4. tools/call success
    call_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "archive_capabilities", "arguments": {}},
        }
    )
    assert "content" in call_res["result"]

    # 5. tools/call failure
    call_fail = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "invalid_tool", "arguments": {}},
        }
    )
    assert "error" in call_fail
    assert call_fail["error"]["code"] == -32000

    # 6. Unknown method
    err_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "unknown/method",
        }
    )
    assert err_res["error"]["code"] == -32601


def test_doctor_parity_cli_and_mcp(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify archive doctor outputs identical schema in CLI and MCP."""
    doctor(format="json")
    captured = capsys.readouterr()
    cli_out = json.loads(captured.out)

    mcp_out = call_tool("archive_doctor")
    assert cli_out["python_version"] == mcp_out["python_version"]
    assert "python_min_satisfied" in mcp_out


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


def test_archive_status_tool(tmp_path: Path) -> None:
    """Verify archive status tool dynamically inspects directory."""
    status_out = call_tool("archive_status", {"cas_path": str(tmp_path)})
    assert status_out["objects_stored"] == 0
    assert status_out["active"] is True


def test_unknown_mcp_tool_raises_error() -> None:
    """Verify calling an unknown tool raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool: invalid_tool"):
        call_tool("invalid_tool")
