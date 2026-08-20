"""Contract tests verifying parity between CLI outputs and MCP server tools."""

from __future__ import annotations

import io
import json
import sys
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
    read_resource,
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
    assert "archive://status" in uris


def test_stdio_server_transport() -> None:
    """Verify StdioServerTransport reads and writes JSON-RPC messages."""
    fake_in = io.StringIO('{"jsonrpc": "2.0", "method": "initialize"}\n   \n[1, 2]\n')
    fake_out = io.StringIO()
    transport = StdioServerTransport(stdin=fake_in, stdout=fake_out)

    msg = transport.read_message()
    assert msg == {"jsonrpc": "2.0", "method": "initialize"}

    # Whitespace line
    assert transport.read_message() is None

    # Non-dict JSON raises TypeError
    with pytest.raises(TypeError, match="Expected a JSON object"):
        transport.read_message()

    transport.write_message({"jsonrpc": "2.0", "id": 1, "result": {}})
    assert '"jsonrpc": "2.0"' in fake_out.getvalue()


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
    assert init_res is not None
    assert init_res["id"] == 1
    assert init_res["result"]["serverInfo"]["name"] == "archive-govt-nz-mcp"

    # 2. notifications/initialized
    notif_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
    )
    assert notif_res is None
    assert server.initialized is True

    # initialized with id
    init_id_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "initialized",
        }
    )
    assert init_id_res is not None
    assert init_id_res["id"] == 99

    # 3. tools/list
    list_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
        }
    )
    assert list_res is not None
    assert "tools" in list_res["result"]

    # 4. resources/list
    res_list = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
        }
    )
    assert res_list is not None
    assert "resources" in res_list["result"]

    # 5. resources/read
    res_read = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": "archive://capabilities"},
        }
    )
    assert res_read is not None
    assert "contents" in res_read["result"]

    # 6. tools/call success
    call_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "archive_capabilities", "arguments": {}},
        }
    )
    assert call_res is not None
    assert "content" in call_res["result"]
    assert call_res["result"]["isError"] is False

    # 7. tools/call failure
    call_fail = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "invalid_tool", "arguments": {}},
        }
    )
    assert call_fail is not None
    assert call_fail["result"]["isError"] is True


def test_mcp_server_error_handling() -> None:
    """Verify MCP Server edge-case protocol error returns."""
    server = Server()

    # Invalid JSON-RPC version
    inv_ver = server.handle_request({"jsonrpc": "1.0", "id": 1, "method": "ping"})
    assert inv_ver is not None
    assert inv_ver["error"]["code"] == -32600

    # Non-dict params
    inv_params = server.handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "ping", "params": "string"}
    )
    assert inv_params is not None
    assert inv_params["error"]["code"] == -32602

    # resources/read missing uri
    inv_res = server.handle_request(
        {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {}}
    )
    assert inv_res is not None
    assert inv_res["error"]["code"] == -32602

    # tools/call missing name
    inv_tool_name = server.handle_request(
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {}}
    )
    assert inv_tool_name is not None
    assert inv_tool_name["error"]["code"] == -32602

    # tools/call invalid arguments type
    inv_tool_args = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "archive_doctor", "arguments": "invalid"},
        }
    )
    assert inv_tool_args is not None
    assert inv_tool_args["error"]["code"] == -32602

    # Unknown method
    err_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "unknown/method",
        }
    )
    assert err_res is not None
    assert err_res["error"]["code"] == -32601


def test_doctor_parity_cli_and_mcp(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify archive doctor outputs identical schema in CLI and MCP."""
    doctor(format="json")
    captured = capsys.readouterr()
    cli_out = json.loads(captured.out)

    mcp_out = call_tool("archive_doctor")
    assert cli_out["python_version"] == mcp_out["python_version"]
    assert "python_min_satisfied" in mcp_out

    # Degraded doctor in MCP
    monkeypatch.setattr(sys, "version_info", (3, 10, 0))
    mcp_deg = call_tool("archive_doctor")
    assert mcp_deg["runtime_state"] == "degraded"
    assert mcp_deg["python_min_satisfied"] is False


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
    assert status_out["status"] == "operational"
    assert "active" not in status_out


def test_read_resource_and_errors() -> None:
    """Verify read_resource retrieves standard resources and raises on unknown URI."""
    cap_res = read_resource("archive://capabilities")
    assert cap_res["mimeType"] == "application/json"
    assert "capabilities" in cap_res["text"]

    src_res = read_resource("archive://sources")
    assert "registered_sources_count" in src_res["text"]

    stat_res = read_resource("archive://status")
    assert "objects_stored" in stat_res["text"]

    with pytest.raises(KeyError, match="Resource not found"):
        read_resource("archive://unknown")


def test_unknown_mcp_tool_raises_error() -> None:
    """Verify calling an unknown tool raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool: invalid_tool"):
        call_tool("invalid_tool")


def test_default_transport_and_ping_resource_error() -> None:
    """Verify default transport streams, ping method, and resource read error."""
    transport = StdioServerTransport()
    assert isinstance(transport, StdioServerTransport)

    server = Server()
    ping_res = server.handle_request({"jsonrpc": "2.0", "id": 100, "method": "ping"})
    assert ping_res is not None
    assert ping_res["result"] == {}

    res_err = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "resources/read",
            "params": {"uri": "archive://unknown"},
        }
    )
    assert res_err is not None
    assert res_err["error"]["code"] == -32602

    src_missing = call_tool(
        "archive_sources", {"registry_path": "/path/does/not/exist"}
    )
    assert src_missing["registered_sources_count"] == 0
