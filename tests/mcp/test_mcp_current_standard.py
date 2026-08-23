"""Adversarial controls for the stable MCP 2025-11-25 server surface."""

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING, Any

import pytest

from archive_govt_nz.mcp_server import (
    JSONRPC_INVALID_PARAMS,
    JSONRPC_INVALID_REQUEST,
    MCP_RESOURCE_NOT_FOUND,
    PROTOCOL_VERSION,
    Server,
    call_tool,
    list_tools,
    run_stdio_server,
)
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError

if TYPE_CHECKING:
    from pathlib import Path


def _initialize(server: Server) -> dict[str, Any]:
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "adversarial-client", "version": "1.0"},
            },
        }
    )
    assert response is not None
    return response


def _ready_server() -> Server:
    server = Server()
    assert "result" in _initialize(server)
    assert (
        server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )
    return server


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}},
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": [],
            "clientInfo": {"name": "x", "version": "1"},
        },
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "x"},
        },
    ],
)
def test_initialize_requires_current_handshake(params: dict[str, Any]) -> None:
    """Reject missing or malformed required initialize fields."""
    response = Server().handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params}
    )
    assert response is not None
    assert response["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_current_protocol_and_fail_closed_lifecycle() -> None:
    """Require the current handshake and initialized lifecycle notification."""
    server = Server()
    assert PROTOCOL_VERSION == "2025-11-25"

    early = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert early is not None
    assert early["error"]["code"] == JSONRPC_INVALID_REQUEST

    initialized = _initialize(server)
    assert initialized["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert initialized["result"]["instructions"]

    duplicate = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "again", "version": "1"},
            },
        }
    )
    assert duplicate is not None
    assert duplicate["error"]["code"] == JSONRPC_INVALID_REQUEST

    assert (
        server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )
    assert server.initialized is True


def test_notifications_never_receive_responses() -> None:
    """Never emit JSON-RPC responses for valid notification-shaped messages."""
    server = Server()
    assert (
        server.handle_request(
            {"jsonrpc": "2.0", "method": "notifications/unknown", "params": {}}
        )
        is None
    )

    _initialize(server)
    request_shaped = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "notifications/initialized",
        }
    )
    assert request_shaped is not None
    assert request_shaped["error"]["code"] == JSONRPC_INVALID_REQUEST

    alias = server.handle_request({"jsonrpc": "2.0", "id": 8, "method": "initialized"})
    assert alias is not None
    assert alias["error"]["code"] == -32601

    assert (
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "method": "notifications/unknown",
                "params": "invalid",
            }
        )
        is None
    )


def test_request_requires_method() -> None:
    """Reject an object that is not a JSON-RPC request or notification."""
    response = Server().handle_request({"jsonrpc": "2.0", "id": 4})
    assert response is not None
    assert response["error"]["code"] == JSONRPC_INVALID_REQUEST


@pytest.mark.parametrize("method", ["tools/list", "resources/list"])
def test_one_page_lists_reject_unknown_cursor(method: str) -> None:
    """Reject cursors because these finite lists have no subsequent page."""
    server = _ready_server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": method,
            "params": {"cursor": "invented-cursor"},
        }
    )
    assert response is not None
    assert response["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_tool_schemas_and_structured_content_agree() -> None:
    """Declare current schemas and keep dual tool result forms equivalent."""
    tools = list_tools()
    assert tools
    for tool in tools:
        assert tool["inputSchema"]["$schema"].endswith("2020-12/schema")
        assert tool["outputSchema"]["$schema"].endswith("2020-12/schema")
        assert tool["annotations"]["readOnlyHint"] is True

    server = _ready_server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "archive_capabilities", "arguments": {}},
        }
    )
    assert response is not None
    result = response["result"]
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"]) == result["structuredContent"]


def test_unknown_tool_and_invalid_arguments_are_protocol_errors() -> None:
    """Map malformed tool calls to invalid-params protocol errors."""
    server = _ready_server()
    unknown = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "unknown", "arguments": {}},
        }
    )
    assert unknown is not None
    assert unknown["error"]["code"] == JSONRPC_INVALID_PARAMS

    extra = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "archive_doctor", "arguments": {"unsafe": True}},
        }
    )
    assert extra is not None
    assert extra["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_known_tool_execution_failure_is_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Map a valid known-tool domain failure to an MCP tool error result."""
    server = _ready_server()

    def _fail(_name: str, _arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        message = "bounded domain failure"
        raise RuntimeError(message)

    monkeypatch.setattr("archive_govt_nz.mcp_server.call_tool", _fail)
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {"name": "archive_doctor", "arguments": {}},
        }
    )
    assert response is not None
    assert response["result"]["isError"] is True
    assert "structuredContent" not in response["result"]


def test_missing_resource_uses_mcp_resource_error() -> None:
    """Use the MCP resource-not-found code for an absent exact URI."""
    server = _ready_server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "resources/read",
            "params": {"uri": "archive://missing"},
        }
    )
    assert response is not None
    assert response["error"]["code"] == MCP_RESOURCE_NOT_FOUND


def test_resource_domain_failure_is_internal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not expose unexpected resource implementation failures as success."""
    server = _ready_server()

    def _fail(_uri: str) -> dict[str, Any]:
        message = "unexpected resource failure"
        raise RuntimeError(message)

    monkeypatch.setattr("archive_govt_nz.mcp_server.read_resource", _fail)
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "resources/read",
            "params": {"uri": "archive://status"},
        }
    )
    assert response is not None
    assert response["error"]["code"] == -32603


def test_archive_status_verifies_real_sharded_cas(tmp_path: Path) -> None:
    """Discover and stream-verify the repository's canonical CAS layout."""
    store = ContentAddressedStore(tmp_path)
    receipt = store.put_bytes(b"real MCP CAS evidence")

    status = call_tool("archive_status", {"cas_path": str(tmp_path)})
    assert status == {
        "bytes_verified": receipt.byte_count,
        "cas_directory": str(tmp_path),
        "objects_discovered": 1,
        "objects_verified": 1,
        "status": "verified",
    }

    receipt.path.write_bytes(b"corrupt")
    with pytest.raises(ObjectStoreError, match="object_corrupt"):
        call_tool("archive_status", {"cas_path": str(tmp_path)})


def test_empty_or_missing_cas_is_not_operational(tmp_path: Path) -> None:
    """Report no state rather than health for empty or absent storage."""
    empty = call_tool("archive_status", {"cas_path": str(tmp_path)})
    missing = call_tool("archive_status", {"cas_path": str(tmp_path / "missing")})
    assert empty["status"] == "no_state"
    assert missing["status"] == "no_state"
    assert empty["objects_verified"] == 0


def test_source_fallback_and_invalid_cas_layouts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the documented seed fallback and reject non-canonical CAS entries."""
    monkeypatch.chdir(tmp_path)
    fallback = tmp_path / "seeds" / "sources"
    fallback.mkdir(parents=True)
    sources = call_tool("archive_sources")
    assert sources["registry_path"] == "seeds/sources"
    assert sources["status"] == "empty"

    cas_root = tmp_path / "invalid-cas"
    flat = cas_root / "sha256" / "not-a-canonical-object"
    flat.parent.mkdir(parents=True)
    flat.write_bytes(b"invalid")
    with pytest.raises(ObjectStoreError, match="invalid_store_layout"):
        call_tool("archive_status", {"cas_path": str(cas_root)})

    flat.unlink()
    target = tmp_path / "target"
    target.write_bytes(b"external")
    (cas_root / "sha256" / "link").symlink_to(target)
    with pytest.raises(ObjectStoreError, match="invalid_store_layout"):
        call_tool("archive_status", {"cas_path": str(cas_root)})


def test_stdio_emits_only_single_line_jsonrpc_messages() -> None:
    """Keep stdout restricted to one compact JSON-RPC message per line."""
    stdin = io.StringIO(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "stdio", "version": "1"},
                },
            }
        )
        + "\n"
    )
    stdout = io.StringIO()
    run_stdio_server(stdin=stdin, stdout=stdout)
    lines = stdout.getvalue().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["result"]["protocolVersion"] == PROTOCOL_VERSION
