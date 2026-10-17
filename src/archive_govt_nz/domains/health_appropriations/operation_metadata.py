"""Typed operations for the existing source-regenerated Platinum v5 profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import (
    gold_metadata,
    operation_context_gold,
)

TOOL_NAME = "health_appropriations_verify_operation_context_metadata"
_PATH = {"type": "string", "minLength": 1, "maxLength": 4096}
_PIN = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_INPUT_PROPERTIES = {
    "input_spec": _PATH,
    "source_root": _PATH,
    "gold_package": _PATH,
    "gold_manifest_sha256": _PIN,
    "output_dir": _PATH,
    "manifest_sha256": _PIN,
}
_OUTPUT_PROPERTIES = {
    "schema_version": {"const": "archive-govt-nz.health-gold-metadata/v5"},
    "status": {"const": "verified"},
    "manifest_sha256": _PIN,
    "packages": {"const": 1},
    "rights": {"const": "not_evaluated"},
    "publication": {"const": "not_performed"},
    "verification_scope": {"const": "source_regenerated_gold_metadata_reconstructed"},
}
MCP_TOOL: dict[str, Any] = {
    "name": TOOL_NAME,
    "description": (
        "Read-only verification of local operation-context Platinum v5 metadata "
        "by reconstructing Gold and metadata from pinned Bronze inputs."
    ),
    "inputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": _INPUT_PROPERTIES,
        "required": list(_INPUT_PROPERTIES),
        "additionalProperties": False,
    },
    "outputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": _OUTPUT_PROPERTIES,
        "required": list(_OUTPUT_PROPERTIES),
        "additionalProperties": False,
    },
    "annotations": {
        "title": "Verify source-regenerated operation-context metadata",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def read_metadata_inputs(
    input_spec: Path, source_root: Path, gold_package: Path, gold_manifest_sha256: str
) -> tuple[gold_metadata.OperationContextGoldInput]:
    """Reuse the closed operation spec and retain the independent Gold pin."""
    return (
        gold_metadata.OperationContextGoldInput(
            gold_package,
            gold_manifest_sha256,
            operation_context_gold.read_input_spec(input_spec),
            source_root,
        ),
    )


def mcp_call(arguments: dict[str, Any]) -> dict[str, Any]:
    """Regenerate expected products and verify both pins without writing state."""
    if not Draft202012Validator(MCP_TOOL["inputSchema"]).is_valid(arguments):
        message = "operation_metadata_arguments_invalid"
        raise ValueError(message)
    inputs = read_metadata_inputs(
        Path(arguments["input_spec"]),
        Path(arguments["source_root"]),
        Path(arguments["gold_package"]),
        arguments["gold_manifest_sha256"],
    )
    return gold_metadata.verify_gold_metadata(
        inputs, Path(arguments["output_dir"]), arguments["manifest_sha256"]
    )
