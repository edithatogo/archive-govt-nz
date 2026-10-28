# SPDX-License-Identifier: Apache-2.0
"""Read-only reconciliation of pinned capture inventory evidence."""

from __future__ import annotations

import json
import re
from typing import Any

from archive_govt_nz.domains.health_appropriations.capture_inventory import (
    CaptureSnapshot,
    InventorySnapshot,
    build_capture_inventory,
)
from archive_govt_nz.domains.health_appropriations.source_layout_operations import (
    MAX_TOTAL_INPUT_BYTES,
    _read_pinned,
)

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_INPUTS = 256
_MAX_TOTAL_ROWS = 10000
_MAX_REQUEST_COMPARISONS = 5000000


def reconcile_capture_inventory(  # noqa: C901, PLR0915 - explicit bounded input boundary
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Reconcile only explicitly pinned inputs and return a redacted summary.

    This summarizes recorded metadata; it does not replay source objects or
    verify rights, completeness, normalization, or publication.
    """
    if set(arguments) != {"censuses", "captures"}:
        msg = "inventory_arguments_invalid"
        raise ValueError(msg)
    censuses, captures = arguments["censuses"], arguments["captures"]
    if (
        not isinstance(censuses, list)
        or not censuses
        or not isinstance(captures, list)
        or len(censuses) + 2 * len(captures) > _MAX_INPUTS
    ):
        msg = "inventory_input_count_invalid"
        raise ValueError(msg)

    total_bytes = 0
    total_rows = 0
    row_counts: dict[str, tuple[int, int]] = {}
    names: set[str] = set()

    def snapshot(pin: object) -> InventorySnapshot:
        nonlocal total_bytes, total_rows
        if (
            not isinstance(pin, dict)
            or set(pin) != {"name", "path", "sha256"}
            or not all(isinstance(pin[key], str) for key in pin)
            or not _NAME.fullmatch(pin["name"])
            or pin["name"] in names
        ):
            msg = "inventory_input_pin_invalid"
            raise ValueError(msg)
        names.add(pin["name"])
        payload, _ = _read_pinned(pin["path"], pin["sha256"])
        total_bytes += len(payload)
        if total_bytes > MAX_TOTAL_INPUT_BYTES:
            msg = "input_total_size_invalid"
            raise ValueError(msg)
        try:
            document = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            msg = "inventory_input_invalid"
            raise ValueError(msg) from error
        records = document.get("records") if isinstance(document, dict) else None
        results = document.get("results") if isinstance(document, dict) else None
        counts = (
            len(records) if isinstance(records, list) else 0,
            len(results) if isinstance(results, list) else 0,
        )
        total_rows += sum(counts)
        if total_rows > _MAX_TOTAL_ROWS:
            msg = "inventory_row_limit_exceeded"
            raise ValueError(msg)
        row_counts[pin["name"]] = counts
        return InventorySnapshot(pin["name"], payload)

    census_snapshots = tuple(snapshot(pin) for pin in censuses)
    capture_snapshots = []
    comparisons = 0
    for capture in captures:
        if not isinstance(capture, dict) or set(capture) - {"manifest", "request"}:
            msg = "inventory_capture_pin_invalid"
            raise ValueError(msg)
        if "manifest" not in capture:
            msg = "inventory_capture_pin_invalid"
            raise ValueError(msg)
        manifest = snapshot(capture["manifest"])
        request = snapshot(capture["request"]) if "request" in capture else None
        if request is not None:
            comparisons += row_counts[request.name][0] * row_counts[manifest.name][1]
            if comparisons > _MAX_REQUEST_COMPARISONS:
                msg = "inventory_request_work_limit_exceeded"
                raise ValueError(msg)
        capture_snapshots.append(CaptureSnapshot(manifest, request))
    try:
        inventory = build_capture_inventory(census_snapshots, tuple(capture_snapshots))
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
        msg = "inventory_input_invalid"
        raise ValueError(msg) from error
    return {
        "schema_version": "archive-govt-nz.health-capture-inventory-operation/v1",
        "status": "reconciled",
        "scope": inventory["scope"],
        "inputs": inventory["inputs"],
        "summary": inventory["summary"],
        "limitations": [
            "source_fixity_not_replayed",
            "rights_not_evaluated",
            "normalization_not_performed",
            "publication_not_performed",
        ],
    }


_PIN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "pattern": r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"},
        "path": {"type": "string", "minLength": 1},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
    "required": ["name", "path", "sha256"],
    "additionalProperties": False,
}
MCP_TOOL: dict[str, Any] = {
    "name": "health_appropriations_reconcile_capture_inventory",
    "description": (
        "Reconcile pinned census and capture receipts without writes or source replay."
    ),
    "inputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "censuses": {
                "type": "array",
                "minItems": 1,
                "maxItems": 256,
                "items": _PIN_SCHEMA,
            },
            "captures": {
                "type": "array",
                "maxItems": 128,
                "items": {
                    "type": "object",
                    "properties": {"manifest": _PIN_SCHEMA, "request": _PIN_SCHEMA},
                    "required": ["manifest"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["censuses", "captures"],
        "additionalProperties": False,
    },
    "outputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "archive-govt-nz.health-capture-inventory-operation/v1"
            },
            "status": {"const": "reconciled"},
            "scope": {
                "const": (
                    "supplied_cohorts_only_not_whole_corpus_or_publication_completeness"
                )
            },
            "inputs": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "bytes": {"type": "integer", "minimum": 1},
                    },
                    "required": ["sha256", "bytes"],
                    "additionalProperties": False,
                },
            },
            "summary": {
                "type": "object",
                "properties": {
                    name: {"type": "integer", "minimum": 0}
                    for name in (
                        "resource_count",
                        "recorded_captured_resource_count",
                        "census_observation_count",
                        "capture_observation_count",
                    )
                },
                "required": [
                    "resource_count",
                    "recorded_captured_resource_count",
                    "census_observation_count",
                    "capture_observation_count",
                ],
                "additionalProperties": False,
            },
            "limitations": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "schema_version",
            "status",
            "scope",
            "inputs",
            "summary",
            "limitations",
        ],
        "additionalProperties": False,
    },
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
}
