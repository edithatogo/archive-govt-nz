# SPDX-License-Identifier: Apache-2.0
"""Read-only preflight for a hash-pinned capture schedule."""

import json
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.capture_selection import (
    _select_sources,
)
from archive_govt_nz.domains.health_appropriations.source_layout_operations import (
    _read_pinned,
)

MAX_RESOURCE_BYTES = 64 * 1024 * 1024
MAX_SOURCES = 1000


def preflight_plan(
    plan: Path, plan_sha256: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate pinned plan and census without network or writes."""
    payload, digest = _read_pinned(str(plan), plan_sha256)
    try:
        config = json.loads(payload)
        if (
            not isinstance(config, dict)
            or set(config)
            != {"schema_version", "census", "census_sha256", "max_resource_bytes"}
            or config["schema_version"] != "archive-govt-nz.health-capture-schedule/v1"
            or not isinstance(config["census"], str)
            or not config["census"]
            or not isinstance(config["census_sha256"], str)
            or type(config["max_resource_bytes"]) is not int
            or not 0 < config["max_resource_bytes"] <= MAX_RESOURCE_BYTES
        ):
            msg = "capture_schedule_invalid"
            raise ValueError(msg)
        census_bytes, census_digest = _read_pinned(
            config["census"], config["census_sha256"]
        )
        census = json.loads(census_bytes)
        selected = _select_sources(census, preservation_only=True)
        if not 0 < len(selected) <= MAX_SOURCES:
            msg = "capture_schedule_source_count_invalid"
            raise ValueError(msg)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
        msg = "capture_schedule_invalid"
        raise ValueError(msg) from error
    receipt: dict[str, Any] = {
        "schema_version": "archive-govt-nz.health-capture-schedule-receipt/v1",
        "plan_sha256": digest,
        "census_sha256": census_digest,
        "selected": len(selected),
        "status": "planned",
    }
    return config, receipt


def mcp_preflight(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate a plan using the read-only MCP contract."""
    if set(arguments) != {"plan", "plan_sha256"} or not all(
        isinstance(value, str) and value for value in arguments.values()
    ):
        msg = "capture_schedule_arguments_invalid"
        raise ValueError(msg)
    return preflight_plan(Path(arguments["plan"]), arguments["plan_sha256"])[1]


_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
MCP_TOOL = {
    "name": "health_appropriations_preflight_capture_plan",
    "description": "Verify a pinned capture plan without network or writes.",
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "inputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "plan": {"type": "string", "minLength": 1},
            "plan_sha256": _DIGEST,
        },
        "required": ["plan", "plan_sha256"],
        "additionalProperties": False,
    },
    "outputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "archive-govt-nz.health-capture-schedule-receipt/v1"
            },
            "plan_sha256": _DIGEST,
            "census_sha256": _DIGEST,
            "selected": {"type": "integer", "minimum": 1, "maximum": MAX_SOURCES},
            "status": {"const": "planned"},
        },
        "required": [
            "schema_version",
            "plan_sha256",
            "census_sha256",
            "selected",
            "status",
        ],
        "additionalProperties": False,
    },
}
