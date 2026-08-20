"""Model Context Protocol (MCP) stdio server for archive-govt-nz."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from archive_govt_nz import __version__
from archive_govt_nz.core.registry import AgencyRegistry

if TYPE_CHECKING:
    from typing import TextIO

PROTOCOL_VERSION = "2024-11-05"

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


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
        stripped = line.strip()
        if not stripped:
            return None
        data = json.loads(stripped)
        if not isinstance(data, dict):
            msg = "Expected a JSON object"
            raise TypeError(msg)
        return data

    def write_message(self, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to stdout."""
        self._stdout.write(json.dumps(message, sort_keys=True) + "\n")
        self._stdout.flush()


class Server:
    """Operational MCP Server implementing JSON-RPC 2.0 request handling."""

    def __init__(self, name: str = "archive-govt-nz-mcp") -> None:
        """Initialize MCP Server instance with name and version."""
        self.name = name
        self.version = __version__
        self.protocol_version = PROTOCOL_VERSION
        self.initialized = False

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:  # noqa: C901, PLR0911, PLR0912
        """Route and process an MCP JSON-RPC 2.0 request."""
        if request.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": JSONRPC_INVALID_REQUEST,
                    "message": "Invalid JSON-RPC version, expected '2.0'",
                },
            }

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}
        if not isinstance(params, dict):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": JSONRPC_INVALID_PARAMS,
                    "message": "Expected params to be an object",
                },
            }

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

        if method in ("notifications/initialized", "initialized"):
            self.initialized = True
            if req_id is None:
                return None
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

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

        if method == "resources/read":
            uri = params.get("uri")
            if not uri or not isinstance(uri, str):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Missing required string parameter 'uri'",
                    },
                }
            try:
                res_content = read_resource(uri)
            except KeyError as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": str(exc),
                    },
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"contents": [res_content]},
                }

        if method == "tools/call":
            tool_name = params.get("name")
            if not tool_name or not isinstance(tool_name, str):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Missing required string parameter 'name'",
                    },
                }
            tool_args = params.get("arguments") or {}
            if not isinstance(tool_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Expected arguments to be an object",
                    },
                }
            try:
                res = call_tool(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(res, indent=2)}
                        ],
                        "structuredContent": res,
                        "isError": False,
                    },
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": str(exc)}],
                        "isError": True,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": JSONRPC_METHOD_NOT_FOUND,
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
    """List available read-only MCP tools with JSON Schema input definitions."""
    return [
        {
            "name": "archive_doctor",
            "description": "Check runtime Python and storage health.",
            "inputSchema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "archive_capabilities",
            "description": "List operational and archival capabilities.",
            "inputSchema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "archive_sources",
            "description": "List registered government sources from seed registry.",
            "inputSchema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "registry_path": {
                        "type": "string",
                        "description": "Path to the seed directory",
                        "default": "registry/seeds",
                    }
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "archive_status",
            "description": "Inspect archive storage and local CAS object statistics.",
            "inputSchema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "cas_path": {
                        "type": "string",
                        "description": "Path to local CAS store",
                        "default": "build/cas",
                    }
                },
                "additionalProperties": False,
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


def read_resource(uri: str) -> dict[str, Any]:
    """Read resource content by URI."""
    if uri == "archive://capabilities":
        data = call_tool("archive_capabilities")
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(data, sort_keys=True, indent=2),
        }
    if uri == "archive://sources":
        data = call_tool("archive_sources")
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(data, sort_keys=True, indent=2),
        }
    if uri == "archive://status":
        data = call_tool("archive_status")
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(data, sort_keys=True, indent=2),
        }

    msg = f"Resource not found: {uri}"
    raise KeyError(msg)


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a registered MCP tool call safely with dynamic evidence."""
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
        path_str = str(args.get("registry_path", "registry/seeds"))
        path = Path(path_str)
        count = len(AgencyRegistry.load_from_seeds(path)) if path.is_dir() else 0
        return {
            "registered_sources_count": count,
            "registry_path": str(path),
        }
    if name == "archive_status":
        cas_path_str = str(args.get("cas_path", "build/cas"))
        cas_dir = Path(cas_path_str)
        sha_dir = cas_dir / "sha256"
        obj_count = (
            len([f for f in sha_dir.glob("*") if f.is_file()])
            if sha_dir.is_dir()
            else 0
        )
        status = "operational" if (obj_count > 0 or cas_dir.is_dir()) else "no_state"
        return {
            "cas_directory": cas_path_str,
            "objects_stored": obj_count,
            "status": status,
        }
    msg = f"Unknown tool: {name}"
    raise ValueError(msg)


def run_stdio_server(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> None:
    """Run standard IO MCP server loop until stream close or termination."""
    transport = StdioServerTransport(stdin=stdin, stdout=stdout)
    server = Server()

    while True:
        try:
            req = transport.read_message()
        except json.JSONDecodeError as exc:
            transport.write_message(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": JSONRPC_PARSE_ERROR,
                        "message": f"Parse error: {exc}",
                    },
                }
            )
            continue
        except TypeError as exc:
            transport.write_message(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": JSONRPC_INVALID_REQUEST,
                        "message": str(exc),
                    },
                }
            )
            continue

        if req is None:
            break

        resp = server.handle_request(req)
        if resp is not None:
            transport.write_message(resp)


def main() -> None:
    """Execute stdio MCP server process entrypoint."""
    run_stdio_server()


if __name__ == "__main__":  # pragma: no cover
    main()
