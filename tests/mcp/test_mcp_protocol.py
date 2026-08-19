"""Comprehensive protocol tests for the MCP stdio server via subprocess client."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from typing import TYPE_CHECKING, Any

from archive_govt_nz.mcp_server import main, run_stdio_server

if TYPE_CHECKING:
    import pytest


def _send_rpc(
    proc: subprocess.Popen[str], request: dict[str, Any]
) -> dict[str, Any] | None:
    """Send one JSON-RPC line to subprocess and parse response."""
    assert proc.stdin is not None
    assert proc.stdout is not None
    payload = json.dumps(request) + "\n"
    proc.stdin.write(payload)
    proc.stdin.flush()

    if request.get("id") is None and "notifications/" in request.get("method", ""):
        return None

    line = proc.stdout.readline()
    if not line:
        return None
    return json.loads(line.strip())


def test_mcp_subprocess_initialization_and_tools() -> None:
    """Validate stdio lifecycle initialization handshake and tool execution."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "archive_govt_nz.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # 1. initialize
        init_res = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            },
        )
        assert init_res is not None
        assert init_res["id"] == 1
        result = init_res["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "archive-govt-nz-mcp"
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]

        # 2. initialized notification
        _send_rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 3. ping
        ping_res = _send_rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "ping"})
        assert ping_res is not None
        assert ping_res["result"] == {}

        # 4. tools/list
        tools_res = _send_rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        assert tools_res is not None
        tools = tools_res["result"]["tools"]
        assert len(tools) == 4

        # 5. tools/call - archive_doctor
        doc_res = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "archive_doctor", "arguments": {}},
            },
        )
        assert doc_res is not None
        assert doc_res["result"]["isError"] is False
        assert doc_res["result"]["structuredContent"]["python_min_satisfied"] is True

        # 6. tools/call - archive_capabilities
        caps_res = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "archive_capabilities", "arguments": {}},
            },
        )
        assert caps_res is not None
        assert caps_res["result"]["isError"] is False
        assert caps_res["result"]["structuredContent"]["count"] > 0

        # 7. tools/call - archive_sources
        sources_res = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "archive_sources",
                    "arguments": {"registry_path": "registry/seeds"},
                },
            },
        )
        assert sources_res is not None
        assert sources_res["result"]["isError"] is False
        assert (
            sources_res["result"]["structuredContent"]["registered_sources_count"] > 0
        )

        # 8. tools/call - archive_status
        status_res = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "archive_status",
                    "arguments": {"cas_path": "build/cas"},
                },
            },
        )
        assert status_res is not None
        assert status_res["result"]["isError"] is False
        assert "status" in status_res["result"]["structuredContent"]
        assert "active" not in status_res["result"]["structuredContent"]

        # 9. tools/call - unknown tool (execution error)
        fail_res = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {"name": "unknown_tool", "arguments": {}},
            },
        )
        assert fail_res is not None
        assert fail_res["result"]["isError"] is True
        assert "Unknown tool" in fail_res["result"]["content"][0]["text"]

    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=5)
        assert proc.returncode == 0


def test_mcp_subprocess_resources_and_errors() -> None:
    """Validate resource inspection and structured JSON-RPC protocol error codes."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "archive_govt_nz.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # 1. resources/list and resources/read
        res_list = _send_rpc(
            proc, {"jsonrpc": "2.0", "id": 1, "method": "resources/list"}
        )
        assert res_list is not None
        assert len(res_list["result"]["resources"]) == 3

        res_read = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": {"uri": "archive://capabilities"},
            },
        )
        assert res_read is not None
        assert len(res_read["result"]["contents"]) == 1
        assert res_read["result"]["contents"][0]["mimeType"] == "application/json"

        # 2. Invalid JSON-RPC version
        inv_ver = _send_rpc(
            proc,
            {"jsonrpc": "1.0", "id": 3, "method": "ping"},
        )
        assert inv_ver is not None
        assert inv_ver["error"]["code"] == -32600

        # 3. Method not found
        inv_method = _send_rpc(
            proc,
            {"jsonrpc": "2.0", "id": 4, "method": "non_existent_method"},
        )
        assert inv_method is not None
        assert inv_method["error"]["code"] == -32601

        # 4. Invalid params (non-object)
        inv_params = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "ping",
                "params": "not-an-object",
            },
        )
        assert inv_params is not None
        assert inv_params["error"]["code"] == -32602

        # 5. tools/call missing name
        inv_call_params = _send_rpc(
            proc,
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {}},
        )
        assert inv_call_params is not None
        assert inv_call_params["error"]["code"] == -32602

        # 6. tools/call arguments not an object
        inv_args = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "archive_doctor", "arguments": "invalid"},
            },
        )
        assert inv_args is not None
        assert inv_args["error"]["code"] == -32602

        # 7. resources/read missing uri
        inv_res_read = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "resources/read",
                "params": {},
            },
        )
        assert inv_res_read is not None
        assert inv_res_read["error"]["code"] == -32602

        # 8. resources/read non-existent uri
        inv_res_missing = _send_rpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "resources/read",
                "params": {"uri": "archive://non_existent"},
            },
        )
        assert inv_res_missing is not None
        assert inv_res_missing["error"]["code"] == -32602

    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=5)
        assert proc.returncode == 0


def test_mcp_parse_error_and_type_error_handling() -> None:
    """Validate JSON parse errors and type errors in transport loop."""
    fake_in = io.StringIO(
        '{\n{"jsonrpc": "2.0", "method": "notifications/initialized"}\n[1, 2, 3]\n'
    )
    fake_out = io.StringIO()

    run_stdio_server(stdin=fake_in, stdout=fake_out)

    output_lines = [
        json.loads(line) for line in fake_out.getvalue().splitlines() if line.strip()
    ]
    assert len(output_lines) == 2
    assert output_lines[0]["error"]["code"] == -32700
    assert output_lines[1]["error"]["code"] == -32600


def test_mcp_main_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate main entrypoint invokes run_stdio_server."""
    called = []
    monkeypatch.setattr(
        "archive_govt_nz.mcp_server.run_stdio_server",
        lambda: called.append(True),
    )
    main()
    assert called == [True]
