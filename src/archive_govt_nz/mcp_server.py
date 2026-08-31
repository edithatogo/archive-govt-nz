"""Fail-closed Model Context Protocol stdio server for archive-govt-nz."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jsonschema import Draft202012Validator

from archive_govt_nz import __version__
from archive_govt_nz.core.registry import AgencyRegistry
from archive_govt_nz.domains.health_appropriations.budget_operations import (
    BUDGET_VERIFICATION_SCHEMA,
    verify_budget_package,
)
from archive_govt_nz.domains.health_appropriations.operations import (
    inspect_archive_status,
)
from archive_govt_nz.domains.health_appropriations.rebuild import verify_rebuild
from archive_govt_nz.domains.health_appropriations.source_operations import (
    SOURCE_OPERATION_SCHEMA,
    SOURCE_PREFLIGHT_INPUT_SCHEMA,
    preflight_source,
)
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError
from archive_govt_nz.schemas.medallion import (
    DOMAIN_REGISTRY,
    get_domain_schema_definition,
)

if TYPE_CHECKING:
    from typing import TextIO

PROTOCOL_VERSION = "2025-11-25"
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603
MCP_RESOURCE_NOT_FOUND = -32002

_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_CAS_LAYOUT_PARTS = 2
_CAS_PREFIX_LENGTH = 2
_INVALID_STORE_LAYOUT = "invalid_store_layout"
_CAPABILITIES = (
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
)


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "$schema": _SCHEMA_URI,
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_NO_ARGUMENTS = _object_schema({}, [])
_TOOL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "health_appropriations_preflight_source",
        "description": (
            "Read-only preflight of approved source profiles; "
            "no rows, source acquisition or output writes."
        ),
        "inputSchema": SOURCE_PREFLIGHT_INPUT_SCHEMA,
        "outputSchema": SOURCE_OPERATION_SCHEMA,
        "annotations": {
            "title": "Preflight an approved health source profile",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "archive_doctor",
        "description": (
            "Check runtime compatibility without claiming archive integrity."
        ),
        "inputSchema": _NO_ARGUMENTS,
        "outputSchema": _object_schema(
            {
                "integrity_status": {"const": "not_checked"},
                "python_min_satisfied": {"type": "boolean"},
                "python_version": {"type": "string"},
                "required_python": {"const": ">=3.14"},
                "runtime_state": {
                    "enum": ["runtime_compatible", "runtime_incompatible"]
                },
            },
            [
                "integrity_status",
                "python_min_satisfied",
                "python_version",
                "required_python",
                "runtime_state",
            ],
        ),
        "annotations": {
            "title": "Inspect runtime compatibility",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "archive_capabilities",
        "description": "List compiled archive capabilities without readiness claims.",
        "inputSchema": _NO_ARGUMENTS,
        "outputSchema": _object_schema(
            {
                "capabilities": {"type": "array", "items": {"type": "string"}},
                "count": {"type": "integer", "minimum": 0},
                "status": {"const": "compiled"},
            },
            ["capabilities", "count", "status"],
        ),
        "annotations": {
            "title": "List compiled capabilities",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "archive_sources",
        "description": "Inspect the configured government-source seed registry.",
        "inputSchema": _object_schema(
            {
                "registry_path": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Path to the seed directory",
                    "default": "registry/seeds",
                }
            },
            [],
        ),
        "outputSchema": _object_schema(
            {
                "registered_sources_count": {"type": "integer", "minimum": 0},
                "registry_path": {"type": "string"},
                "status": {"enum": ["configured", "empty", "not_configured"]},
            },
            ["registered_sources_count", "registry_path", "status"],
        ),
        "annotations": {
            "title": "Inspect source registry",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "archive_status",
        "description": "Stream-verify canonical objects in a local sharded CAS.",
        "inputSchema": _object_schema(
            {
                "cas_path": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Path to the local CAS root",
                    "default": "build/cas",
                }
            },
            [],
        ),
        "outputSchema": _object_schema(
            {
                "bytes_verified": {"type": "integer", "minimum": 0},
                "cas_directory": {"type": "string"},
                "objects_discovered": {"type": "integer", "minimum": 0},
                "objects_verified": {"type": "integer", "minimum": 0},
                "status": {"enum": ["verified", "no_state"]},
            },
            [
                "bytes_verified",
                "cas_directory",
                "objects_discovered",
                "objects_verified",
                "status",
            ],
        ),
        "annotations": {
            "title": "Verify local CAS state",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "archive_domain_list",
        "description": (
            "List all registered open dataset domains and their "
            "Hugging Face repositories."
        ),
        "inputSchema": _NO_ARGUMENTS,
        "outputSchema": _object_schema(
            {
                "domains": {"type": "array", "items": {"type": "string"}},
                "count": {"type": "integer", "minimum": 0},
                "datasets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string"},
                            "title": {"type": "string"},
                            "hf_repo_id": {"type": "string"},
                            "field_count": {"type": "integer"},
                        },
                        "required": ["domain", "title", "hf_repo_id", "field_count"],
                        "additionalProperties": False,
                    },
                },
            },
            ["domains", "count", "datasets"],
        ),
        "annotations": {
            "title": "List registered archive domains",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "archive_domain_schema",
        "description": (
            "Get the formal schema, PyArrow types, Croissant field mappings, "
            "and ontological links for a domain."
        ),
        "inputSchema": _object_schema(
            {
                "domain": {
                    "type": "string",
                    "description": "Registered domain name",
                }
            },
            ["domain"],
        ),
        "outputSchema": _object_schema(
            {
                "domain": {"type": "string"},
                "title": {"type": "string"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "croissant_type": {"type": "string"},
                            "description": {"type": "string"},
                            "nullable": {"type": "boolean"},
                        },
                        "required": [
                            "name",
                            "croissant_type",
                            "description",
                            "nullable",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            ["domain", "title", "fields"],
        ),
        "annotations": {
            "title": "Get domain schema definition",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "health_appropriations_verify_budget",
        "description": (
            "Verify a pinned standalone Budget package and return compact counts "
            "and provenance without creating state or asserting source rights."
        ),
        "inputSchema": _object_schema(
            {
                "package_dir": {"type": "string", "minLength": 1},
                "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
            ["package_dir", "manifest_sha256"],
        ),
        "outputSchema": BUDGET_VERIFICATION_SCHEMA,
        "annotations": {
            "title": "Verify standalone Budget package",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "health_appropriations_verify_rebuild",
        "description": (
            "Verify a hash-pinned completed raw run and its Bronze sources "
            "without writing any state."
        ),
        "inputSchema": _object_schema(
            {
                "output_dir": {"type": "string", "minLength": 1},
                "store_root": {"type": "string", "minLength": 1},
                "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
            ["output_dir", "store_root", "manifest_sha256"],
        ),
        "outputSchema": _object_schema(
            {
                "schema_version": {"const": "archive-govt-nz.health-raw-rebuild/v1"},
                "status": {"const": "passed"},
                "plan_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "publication_state": {"const": "local_validation_only"},
                "stages": _object_schema(
                    {
                        name: {"type": "string", "pattern": "^[0-9a-f]{64}$"}
                        for name in ("budget", "befu", "hyefu", "historical")
                    },
                    ["budget", "befu", "hyefu", "historical"],
                ),
            },
            ["schema_version", "status", "plan_sha256", "publication_state", "stages"],
        ),
        "annotations": {
            "title": "Verify original-workbook rebuild fixity",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "health_appropriations_status",
        "description": (
            "Inspect local health-appropriations medallion manifests without "
            "capturing, transforming, publishing, or retiring sources."
        ),
        "inputSchema": _object_schema(
            {
                "archive_root": {
                    "type": "string",
                    "minLength": 1,
                    "default": "build/health-appropriations",
                }
            },
            [],
        ),
        "outputSchema": _object_schema(
            {
                "archive_root": {"type": "string"},
                "status": {"enum": ["no_state", "partial", "ready"]},
                "layers": {
                    "type": "object",
                    "properties": {
                        "bronze": {"type": "boolean"},
                        "silver": {"type": "boolean"},
                        "gold": {"type": "boolean"},
                        "platinum": {"type": "boolean"},
                    },
                    "required": ["bronze", "silver", "gold", "platinum"],
                    "additionalProperties": False,
                },
                "manifest_count": {"type": "integer", "minimum": 0},
                "donor_file_count": {"type": "integer", "minimum": 0},
                "captured_resources": {"type": "integer", "minimum": 0},
                "silver_records": {"type": "integer", "minimum": 0},
                "candidate_manifest_sha256": {"type": "string"},
                "dataset": {"type": "string"},
            },
            [
                "archive_root",
                "status",
                "layers",
                "manifest_count",
                "donor_file_count",
                "captured_resources",
                "silver_records",
                "candidate_manifest_sha256",
                "dataset",
            ],
        ),
        "annotations": {
            "title": "Inspect health appropriations archive state",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
)
_TOOLS_BY_NAME = {tool["name"]: tool for tool in _TOOL_DEFINITIONS}


class StdioServerTransport:
    """UTF-8 line-delimited JSON-RPC transport for MCP stdio."""

    def __init__(
        self, stdin: TextIO | None = None, stdout: TextIO | None = None
    ) -> None:
        """Bind the MCP transport to input and output text streams."""
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout

    def read_message(self) -> dict[str, Any] | None:
        """Read the next non-empty JSON-RPC object, or return None at EOF."""
        while True:
            line = self._stdin.readline()
            if not line:
                return None
            if line.strip():
                break
        data = json.loads(line)
        if not isinstance(data, dict):
            msg = "Expected a JSON object"
            raise TypeError(msg)
        return data

    def write_message(self, message: dict[str, Any]) -> None:
        """Write exactly one JSON object and newline to stdout."""
        self._stdout.write(
            json.dumps(
                message, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            )
            + "\n"
        )
        self._stdout.flush()


def _error(req_id: object, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _result(req_id: object, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _valid_initialize_params(params: dict[str, Any]) -> bool:
    info = params.get("clientInfo")
    return bool(
        isinstance(params.get("protocolVersion"), str)
        and isinstance(params.get("capabilities"), dict)
        and isinstance(info, dict)
        and isinstance(info.get("name"), str)
        and info["name"]
        and isinstance(info.get("version"), str)
        and info["version"]
    )


def _validate_one_page_cursor(params: dict[str, Any]) -> str | None:
    if params.get("cursor") is not None:
        return "Invalid or expired cursor"
    return None


class Server:
    """Stateful stable-MCP JSON-RPC request dispatcher."""

    def __init__(self, name: str = "archive-govt-nz-mcp") -> None:
        """Create an uninitialized MCP server."""
        self.name = name
        self.version = __version__
        self.protocol_version = PROTOCOL_VERSION
        self._state = "new"

    @property
    def initialized(self) -> bool:
        """Whether the initialized lifecycle notification was received."""
        return self._state == "ready"

    def handle_request(  # noqa: C901, PLR0911, PLR0912
        self, request: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Validate and route one MCP JSON-RPC message."""
        req_id = request.get("id")
        if request.get("jsonrpc") != "2.0":
            return _error(
                req_id,
                JSONRPC_INVALID_REQUEST,
                "Invalid JSON-RPC version, expected '2.0'",
            )
        method = request.get("method")
        if not isinstance(method, str) or not method:
            return _error(req_id, JSONRPC_INVALID_REQUEST, "Missing string method")

        is_notification = "id" not in request
        raw_params = request.get("params", {})
        if not isinstance(raw_params, dict):
            if is_notification:
                return None
            return _error(req_id, JSONRPC_INVALID_PARAMS, "Expected params object")
        params: dict[str, Any] = raw_params

        if is_notification:
            if method == "notifications/initialized" and self._state == "initializing":
                self._state = "ready"
            return None

        if method == "notifications/initialized":
            return _error(
                req_id,
                JSONRPC_INVALID_REQUEST,
                "notifications/initialized must be a notification",
            )
        if method == "initialize":
            return self._initialize(req_id, params)
        if method == "ping":
            return _result(req_id, {})
        if method == "initialized":
            return _error(
                req_id, JSONRPC_METHOD_NOT_FOUND, "Method not found: initialized"
            )
        if self._state != "ready":
            return _error(
                req_id,
                JSONRPC_INVALID_REQUEST,
                "Server initialization is not complete",
            )
        if method == "tools/list":
            cursor_error = _validate_one_page_cursor(params)
            if cursor_error:
                return _error(req_id, JSONRPC_INVALID_PARAMS, cursor_error)
            return _result(req_id, {"tools": list_tools()})
        if method == "resources/list":
            cursor_error = _validate_one_page_cursor(params)
            if cursor_error:
                return _error(req_id, JSONRPC_INVALID_PARAMS, cursor_error)
            return _result(req_id, {"resources": list_resources()})
        if method == "resources/read":
            return self._read_resource(req_id, params)
        if method == "tools/call":
            return self._call_tool(req_id, params)
        return _error(req_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}")

    def _initialize(self, req_id: object, params: dict[str, Any]) -> dict[str, Any]:
        if self._state != "new":
            return _error(
                req_id, JSONRPC_INVALID_REQUEST, "Server is already initialized"
            )
        if not _valid_initialize_params(params):
            return _error(
                req_id,
                JSONRPC_INVALID_PARAMS,
                "Initialize requires protocolVersion, capabilities, and clientInfo",
            )
        self._state = "initializing"
        return _result(
            req_id,
            {
                "protocolVersion": self.protocol_version,
                "serverInfo": {"name": self.name, "version": self.version},
                "capabilities": get_server_metadata()["capabilities"],
                "instructions": (
                    "Read-only evidence inspection. No publication, rights, "
                    "mutation, or cutover authority is exposed."
                ),
            },
        )

    def _read_resource(self, req_id: object, params: dict[str, Any]) -> dict[str, Any]:
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri:
            return _error(
                req_id,
                JSONRPC_INVALID_PARAMS,
                "Missing required string parameter 'uri'",
            )
        try:
            content = read_resource(uri)
        except KeyError:
            return _error(req_id, MCP_RESOURCE_NOT_FOUND, f"Resource not found: {uri}")
        except Exception:  # noqa: BLE001 - resource implementations are extensible
            return _error(req_id, JSONRPC_INTERNAL_ERROR, "Resource read failed")
        return _result(req_id, {"contents": [content]})

    def _call_tool(self, req_id: object, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            return _error(
                req_id,
                JSONRPC_INVALID_PARAMS,
                "Missing required string parameter 'name'",
            )
        definition = _TOOLS_BY_NAME.get(name)
        if definition is None:
            return _error(req_id, JSONRPC_INVALID_PARAMS, f"Unknown tool: {name}")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            return _error(req_id, JSONRPC_INVALID_PARAMS, "Expected arguments object")
        errors = sorted(
            Draft202012Validator(definition["inputSchema"]).iter_errors(arguments),
            key=lambda error: list(error.path),
        )
        if errors:
            message = (
                "Invalid source operation arguments"
                if name == "health_appropriations_preflight_source"
                else errors[0].message
            )
            return _error(req_id, JSONRPC_INVALID_PARAMS, message)
        try:
            structured = call_tool(name, arguments)
        except Exception as exc:  # noqa: BLE001 - MCP requires domain error results
            return _result(
                req_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
        return _result(
            req_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            structured,
                            ensure_ascii=False,
                            separators=(",", ":"),
                            sort_keys=True,
                        ),
                    }
                ],
                "structuredContent": structured,
                "isError": (
                    name == "health_appropriations_verify_budget"
                    and structured["status"] == "failed"
                ),
            },
        )


def get_server_metadata() -> dict[str, Any]:
    """Return the stable protocol and declared read-only capabilities."""
    return {
        "name": "archive-govt-nz-mcp",
        "version": __version__,
        "protocol_version": PROTOCOL_VERSION,
        "description": "Evidence-first archival tooling for New Zealand data.",
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
        },
    }


def list_tools() -> list[dict[str, Any]]:
    """Return isolated copies of stable read-only tool definitions."""
    return json.loads(json.dumps(_TOOL_DEFINITIONS))


def list_resources() -> list[dict[str, Any]]:
    """List the finite read-only archive resources."""
    return [
        {
            "uri": "archive://capabilities",
            "name": "Archival Capabilities",
            "mimeType": "application/json",
            "description": "Compiled capabilities without readiness claims.",
        },
        {
            "uri": "archive://sources",
            "name": "Registered Sources",
            "mimeType": "application/json",
            "description": "Configured New Zealand government source seeds.",
        },
        {
            "uri": "archive://status",
            "name": "Archive Store Status",
            "mimeType": "application/json",
            "description": "Verified local CAS evidence, or explicit no state.",
        },
    ]


def read_resource(uri: str) -> dict[str, Any]:
    """Read one finite archive resource by exact URI."""
    tool_by_uri = {
        "archive://capabilities": "archive_capabilities",
        "archive://sources": "archive_sources",
        "archive://status": "archive_status",
    }
    name = tool_by_uri.get(uri)
    if name is None:
        message = f"Resource not found: {uri}"
        raise KeyError(message)
    data = call_tool(name)
    return {
        "uri": uri,
        "mimeType": "application/json",
        "text": json.dumps(
            data, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ),
    }


def _archive_sources(arguments: dict[str, Any]) -> dict[str, Any]:
    requested = str(arguments.get("registry_path", "registry/seeds"))
    path = Path(requested)
    fallback = Path("seeds/sources")
    if not path.is_dir() and requested == "registry/seeds" and fallback.is_dir():
        path = fallback
    if not path.is_dir():
        return {
            "registered_sources_count": 0,
            "registry_path": requested,
            "status": "not_configured",
        }
    count = len(AgencyRegistry.load_from_seeds(path))
    return {
        "registered_sources_count": count,
        "registry_path": str(path),
        "status": "configured" if count else "empty",
    }


def _discover_cas_objects(cas_path: Path) -> list[str]:
    sha_dir = cas_path / "sha256"
    if not sha_dir.is_dir():
        return []
    object_ids: list[str] = []
    for path in sorted(sha_dir.rglob("*")):
        if path.is_symlink():
            raise ObjectStoreError(_INVALID_STORE_LAYOUT)
        if not path.is_file():
            continue
        parts = path.relative_to(sha_dir).parts
        if (
            len(parts) != _CAS_LAYOUT_PARTS
            or len(parts[0]) != _CAS_PREFIX_LENGTH
            or not _DIGEST.fullmatch(parts[1])
            or parts[0] != parts[1][:_CAS_PREFIX_LENGTH]
        ):
            raise ObjectStoreError(_INVALID_STORE_LAYOUT)
        object_ids.append(f"sha256:{parts[1]}")
    return object_ids


def _archive_status(arguments: dict[str, Any]) -> dict[str, Any]:
    path_text = str(arguments.get("cas_path", "build/cas"))
    path = Path(path_text)
    object_ids = _discover_cas_objects(path)
    store = ContentAddressedStore(path, create=False)
    total_bytes = sum(store.verify(object_id).byte_count for object_id in object_ids)
    count = len(object_ids)
    return {
        "bytes_verified": total_bytes,
        "cas_directory": path_text,
        "objects_discovered": count,
        "objects_verified": count,
        "status": "verified" if count else "no_state",
    }


def _health_read_only_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "health_appropriations_preflight_source":
        return preflight_source(args)
    if name == "health_appropriations_verify_budget":
        return verify_budget_package(
            Path(str(args["package_dir"])), str(args["manifest_sha256"])
        )
    if name == "health_appropriations_verify_rebuild":
        return verify_rebuild(
            Path(str(args["output_dir"])),
            Path(str(args["store_root"])),
            str(args["manifest_sha256"]),
        )
    return inspect_archive_status(
        Path(str(args.get("archive_root", "build/health-appropriations")))
    )


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute one known read-only tool and validate its output schema."""
    definition = _TOOLS_BY_NAME.get(name)
    if definition is None:
        message = f"Unknown tool: {name}"
        raise ValueError(message)
    args = arguments or {}
    if name == "archive_doctor":
        satisfied = sys.version_info >= (3, 14)
        result = {
            "integrity_status": "not_checked",
            "python_min_satisfied": satisfied,
            "python_version": sys.version.split()[0],
            "required_python": ">=3.14",
            "runtime_state": (
                "runtime_compatible" if satisfied else "runtime_incompatible"
            ),
        }
    elif name == "archive_capabilities":
        result = {
            "capabilities": list(_CAPABILITIES),
            "count": len(_CAPABILITIES),
            "status": "compiled",
        }
    elif name == "archive_sources":
        result = _archive_sources(args)
    elif name == "archive_domain_list":
        datasets_list = [
            {
                "domain": s.domain,
                "title": s.title,
                "hf_repo_id": s.hf_repo_id,
                "field_count": len(s.fields),
            }
            for s in DOMAIN_REGISTRY.values()
        ]
        result = {
            "domains": list(DOMAIN_REGISTRY.keys()),
            "count": len(DOMAIN_REGISTRY),
            "datasets": datasets_list,
        }
    elif name == "archive_domain_schema":
        domain_name = str(args.get("domain", "legislation"))
        schema_def = get_domain_schema_definition(domain_name)
        fields_list = [
            {
                "name": f.name,
                "croissant_type": f.croissant_type,
                "description": f.description,
                "nullable": f.nullable,
            }
            for f in schema_def.fields
        ]
        result = {
            "domain": schema_def.domain,
            "title": schema_def.title,
            "fields": fields_list,
        }
    elif name in (
        "health_appropriations_preflight_source",
        "health_appropriations_verify_budget",
        "health_appropriations_verify_rebuild",
        "health_appropriations_status",
    ):
        result = _health_read_only_tool(name, args)
    else:
        result = _archive_status(args)
    Draft202012Validator(definition["outputSchema"]).validate(result)
    return result


def run_stdio_server(stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
    """Run the stdio MCP server until EOF without non-protocol stdout output."""
    transport = StdioServerTransport(stdin=stdin, stdout=stdout)
    server = Server()
    while True:
        try:
            request = transport.read_message()
        except json.JSONDecodeError as exc:
            transport.write_message(
                _error(None, JSONRPC_PARSE_ERROR, f"Parse error: {exc.msg}")
            )
            continue
        except TypeError as exc:
            transport.write_message(_error(None, JSONRPC_INVALID_REQUEST, str(exc)))
            continue
        if request is None:
            break
        response = server.handle_request(request)
        if response is not None:
            transport.write_message(response)


def main() -> None:
    """Execute the stdio MCP server entrypoint."""
    run_stdio_server()


if __name__ == "__main__":  # pragma: no cover
    main()
