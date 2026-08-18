"""Model Context Protocol (MCP) Server for archive-govt-nz."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from archive_govt_nz import __version__
from archive_govt_nz.core.registry import AgencyRegistry

PROTOCOL_VERSION = "2024-11-05"


class StdioServerTransport:
    """Standard IO transport for JSON-RPC 2.0 MCP protocol."""

    def __init__(
        self,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
    ) -> None:
        """Initialize standard IO transport streams."""
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout

    def read_message(self) -> dict[str, Any] | None:
        """Read a single line-delimited JSON-RPC message from stdin."""
        line = self._stdin.readline()
        if not line:
            return None
        return json.loads(line.strip())

    def write_message(self, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to stdout."""
        self._stdout.write(json.dumps(message) + "\n")
        self._stdout.flush()


class Server:
    """Operational MCP Server implementing JSON-RPC 2.0 request handling."""

    def __init__(self, name: str = "archive-govt-nz-mcp") -> None:
        """Initialize MCP Server instance with name and version."""
        self.name = name
        self.version = __version__
        self.protocol_version = PROTOCOL_VERSION

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Route and process an MCP JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": self.protocol_version,
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version,
                    },
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                },
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": list_tools()},
            }

        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"resources": list_resources()},
            }

        if method == "tools/call":
            tool_name = str(params.get("name"))
            tool_args = params.get("arguments", {})
            try:
                res = call_tool(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res, indent=2)}]
                    },
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32000,
                        "message": str(exc),
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }


def get_server_metadata() -> dict[str, Any]:
    """Return MCP server metadata and protocol specification."""
    return {
        "name": "archive-govt-nz-mcp",
        "version": __version__,
        "protocol_version": PROTOCOL_VERSION,
        "description": "Evidence-first archival tooling for New Zealand data.",
        "capabilities": {
            "tools": {
                "listChanged": False,
            },
            "resources": {
                "subscribe": False,
                "listChanged": False,
            },
        },
    }


def list_tools() -> list[dict[str, Any]]:
    """List available read-only MCP tools."""
    return [
        {
            "name": "archive_doctor",
            "description": "Check runtime Python and storage health.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "archive_capabilities",
            "description": "List operational and archival capabilities.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "archive_sources",
            "description": "List registered government sources from seed registry.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "registry_path": {
                        "type": "string",
                        "description": "Path to the seed directory",
                        "default": "seeds/sources",
                    }
                },
            },
        },
        {
            "name": "archive_status",
            "description": "Inspect archive storage and local CAS object statistics.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cas_path": {
                        "type": "string",
                        "description": "Path to local CAS store",
                        "default": "build/cas",
                    }
                },
            },
        },
    ]


def list_resources() -> list[dict[str, Any]]:
    """List available MCP resources."""
    return [
        {
            "uri": "archive://capabilities",
            "name": "Archival Capabilities",
            "mimeType": "application/json",
            "description": "JSON descriptor of active archival capabilities.",
        },
        {
            "uri": "archive://sources",
            "name": "Registered Sources",
            "mimeType": "application/json",
            "description": "JSON descriptor of all registered NZ government seeds.",
        },
        {
            "uri": "archive://status",
            "name": "Archive System Status",
            "mimeType": "application/json",
            "description": "Current system health, assurance, and fixity status.",
        },
    ]


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a registered MCP tool call safely."""
    args = arguments or {}
    if name == "archive_doctor":
        py_ver = sys.version.split()[0]
        sat = sys.version_info >= (3, 11)
        return {
            "python_version": py_ver,
            "python_min_satisfied": sat,
            "runtime_state": "operational" if sat else "degraded",
        }
    if name == "archive_capabilities":
        caps = [
            "cas_dual_hash",
            "warc_iso28500",
            "wacz_bundle",
            "huggingface_distribution",
            "zenodo_doi",
            "croissant_jsonld",
            "ro_crate_1_1",
            "offline_replay",
            "mcp_server",
            "multi_source_adapters",
        ]
        return {
            "capabilities": caps,
            "count": len(caps),
        }
    if name == "archive_sources":
        path_str = str(args.get("registry_path", "seeds/sources"))
        path = Path(path_str)
        count = 0
        if path.is_dir():
            count = len(AgencyRegistry.load_from_seeds(path))
        elif Path("registry/seeds").is_dir():
            count = len(AgencyRegistry.load_from_seeds(Path("registry/seeds")))
        return {
            "registered_sources_count": count,
            "registry_path": path_str,
        }
    if name == "archive_status":
        cas_dir = Path(str(args.get("cas_path", "build/cas")))
        obj_count = len(list(cas_dir.glob("sha256/*"))) if cas_dir.is_dir() else 0
        return {
            "cas_directory": str(cas_dir),
            "objects_stored": obj_count,
            "active": True,
        }
    msg = f"Unknown tool: {name}"
    raise ValueError(msg)
