# SPDX-License-Identifier: Apache-2.0
"""Bounded, hash-pinned, read-only source-layout reconciliation operation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, NoReturn

from archive_govt_nz.domains.health_appropriations.source_layout_reconciliation import (
    reconcile_source_layout_reports,
)

MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_TOTAL_INPUT_BYTES = 48 * 1024 * 1024
MAX_SOURCE_IDENTITIES = 10000
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_INPUT_NAMES = (
    "census",
    "workbook_baseline",
    "pdf_baseline",
    "workbook_recheck",
    "pdf_recheck",
)
_TEXT_INPUT_NAMES = ("text_baseline", "text_recheck")


def _fail(code: str) -> NoReturn:
    error = ValueError(code)
    raise error


def _read_pinned(path_text: str, expected_sha256: str) -> tuple[bytes, str]:
    if not _DIGEST.fullmatch(expected_sha256):
        _fail("input_digest_invalid")
    descriptor: int | None = None
    try:
        path = Path(path_text)
        path_metadata = path.lstat()
        if not stat.S_ISREG(path_metadata.st_mode):
            _fail("input_not_regular_file")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_dev != path_metadata.st_dev
            or metadata.st_ino != path_metadata.st_ino
        ):
            _fail("input_not_regular_file")
        if metadata.st_size <= 0 or metadata.st_size > MAX_INPUT_BYTES:
            _fail("input_size_invalid")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            payload = stream.read(MAX_INPUT_BYTES + 1)
        if not payload or len(payload) > MAX_INPUT_BYTES:
            _fail("input_size_invalid")
    except ValueError:
        raise
    except OSError:
        _fail("input_unreadable")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        _fail("input_digest_mismatch")
    return payload, digest


def _validate_arguments(arguments: dict[str, Any]) -> bool:
    allowed = {
        item
        for name in (*_INPUT_NAMES, *_TEXT_INPUT_NAMES)
        for item in (name, f"{name}_sha256")
    }
    if set(arguments) - allowed:
        _fail("input_arguments_invalid")
    for name in _INPUT_NAMES:
        if name not in arguments or f"{name}_sha256" not in arguments:
            _fail("input_pin_required")
    for name in (*_INPUT_NAMES, *_TEXT_INPUT_NAMES):
        if (name in arguments) != (f"{name}_sha256" in arguments):
            _fail("input_pin_pair_required")
        if name in arguments and (
            not isinstance(arguments[name], str)
            or not isinstance(arguments[f"{name}_sha256"], str)
        ):
            _fail("input_pin_invalid")
    has_text = [name in arguments for name in _TEXT_INPUT_NAMES]
    if has_text[0] != has_text[1]:
        _fail("text_layout_recheck_required")
    return has_text[0]


def reconcile_source_layout_operation(arguments: dict[str, Any]) -> dict[str, Any]:
    """Verify supplied report pins and return a redacted reconciliation receipt."""
    include_text = _validate_arguments(arguments)

    payloads: dict[str, bytes] = {}
    pins: dict[str, dict[str, int | str]] = {}
    total_bytes = 0
    names = (*_INPUT_NAMES, *(_TEXT_INPUT_NAMES if include_text else ()))
    for name in names:
        payload, digest = _read_pinned(
            str(arguments[name]), str(arguments[f"{name}_sha256"])
        )
        total_bytes += len(payload)
        if total_bytes > MAX_TOTAL_INPUT_BYTES:
            _fail("input_total_size_invalid")
        payloads[name] = payload
        pins[name] = {"sha256": digest, "bytes": len(payload)}

    reconciled = reconcile_source_layout_reports(
        payloads["census"],
        payloads["workbook_baseline"],
        payloads["pdf_baseline"],
        payloads["workbook_recheck"],
        payloads["pdf_recheck"],
        text_baseline_bytes=payloads.get("text_baseline"),
        text_recheck_bytes=payloads.get("text_recheck"),
    )
    census = json.loads(payloads["census"])
    source_ids = sorted(
        row["source_id"]
        for row in census["records"]
        if row.get("disposition") == "captured"
    )
    if len(source_ids) > MAX_SOURCE_IDENTITIES:
        _fail("source_identity_limit_exceeded")
    if len(source_ids) != reconciled["summary"]["captured_source_count"]:
        _fail("source_census_identity_mismatch")

    return {
        "schema_version": "archive-govt-nz.health-source-layout-operation/v1",
        "status": "reconciled",
        "inputs": pins,
        "source_census_sha256": reconciled["source_census_sha256"],
        "capture_manifest_sha256": reconciled["capture_manifest_sha256"],
        "source_ids": source_ids,
        "summary": reconciled["summary"],
        "pinned_reports": reconciled["pinned_reports"],
        "media_types": reconciled["media_types"],
        "unassessed_sources": reconciled["unassessed_sources"],
        "limitations": reconciled["limitations"],
    }


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_DIGEST_SCHEMA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_PATH_SCHEMA = {"type": "string", "minLength": 1}
_INPUT_PROPERTIES: dict[str, Any] = {}
for _name in (*_INPUT_NAMES, *_TEXT_INPUT_NAMES):
    _INPUT_PROPERTIES[_name] = _PATH_SCHEMA
    _INPUT_PROPERTIES[f"{_name}_sha256"] = _DIGEST_SCHEMA

_INPUT_SCHEMA = _object_schema(
    _INPUT_PROPERTIES,
    [item for name in _INPUT_NAMES for item in (name, f"{name}_sha256")],
)
_INPUT_SCHEMA["dependentRequired"] = {
    name: [f"{name}_sha256"] for name in _TEXT_INPUT_NAMES
} | {f"{name}_sha256": [name] for name in _TEXT_INPUT_NAMES}

_COUNT_SCHEMA = {"type": "integer", "minimum": 0}
_UNASSESSED_SOURCE_SCHEMA = _object_schema(
    {
        "source_id": {"type": "string", "minLength": 1},
        "family": {"type": ["string", "null"]},
        "media_type": {"type": ["string", "null"]},
        "reason": {"type": "string", "minLength": 1},
    },
    ["source_id", "family", "media_type", "reason"],
)
_MEDIA_TYPE_SCHEMA = _object_schema(
    {
        "media_type": {"type": "string", "minLength": 1},
        "captured_source_count": _COUNT_SCHEMA,
        "sources_with_structural_baseline": _COUNT_SCHEMA,
        "sources_without_structural_baseline": _COUNT_SCHEMA,
    },
    [
        "media_type",
        "captured_source_count",
        "sources_with_structural_baseline",
        "sources_without_structural_baseline",
    ],
)
_WORKBOOK_REPORT_SCHEMA = {
    "oneOf": [
        _object_schema(
            {
                "sha256": _DIGEST_SCHEMA,
                "layout_manifest_count": _COUNT_SCHEMA,
                "layout_source_count": _COUNT_SCHEMA,
                "recheck_layout_rows_unchanged": {"const": True},
                "excluded_silver_manifest_count": _COUNT_SCHEMA,
                "current_silver_manifests_outside_capture_count": _COUNT_SCHEMA,
            },
            [
                "sha256",
                "layout_manifest_count",
                "layout_source_count",
                "recheck_layout_rows_unchanged",
                "excluded_silver_manifest_count",
                "current_silver_manifests_outside_capture_count",
            ],
        ),
        _object_schema(
            {
                "sha256": _DIGEST_SCHEMA,
                "basis": {"const": "verified_bronze_structure"},
                "layout_source_count": _COUNT_SCHEMA,
                "recheck_layout_rows_unchanged": {"const": True},
                "pinned_parser": {"type": "object"},
                "recheck_parser": {"type": "object"},
            },
            [
                "sha256",
                "basis",
                "layout_source_count",
                "recheck_layout_rows_unchanged",
                "pinned_parser",
                "recheck_parser",
            ],
        ),
    ]
}
_PDF_REPORT_SCHEMA = _object_schema(
    {
        "sha256": _DIGEST_SCHEMA,
        "pdf_capture_count": _COUNT_SCHEMA,
        "recheck_layout_rows_unchanged": {"const": True},
        "pinned_parser": {"type": ["object", "null"]},
        "recheck_parser": {"type": ["object", "null"]},
    },
    [
        "sha256",
        "pdf_capture_count",
        "recheck_layout_rows_unchanged",
        "pinned_parser",
        "recheck_parser",
    ],
)

MCP_TOOL = {
    "name": "health_appropriations_reconcile_source_layout",
    "description": (
        "Reconcile hash-pinned source census and layout reports without writes. "
        "Returns source identities and explicit gaps; it does not infer rights, "
        "semantic mappings or comparability."
    ),
    "inputSchema": _INPUT_SCHEMA,
    "outputSchema": _object_schema(
        {
            "schema_version": {
                "const": "archive-govt-nz.health-source-layout-operation/v1"
            },
            "status": {"const": "reconciled"},
            "inputs": {
                "type": "object",
                "properties": {
                    name: _object_schema(
                        {
                            "sha256": _DIGEST_SCHEMA,
                            "bytes": {"type": "integer", "minimum": 1},
                        },
                        ["sha256", "bytes"],
                    )
                    for name in (*_INPUT_NAMES, *_TEXT_INPUT_NAMES)
                },
                "required": list(_INPUT_NAMES),
                "additionalProperties": False,
            },
            "source_census_sha256": _DIGEST_SCHEMA,
            "capture_manifest_sha256": _DIGEST_SCHEMA,
            "source_ids": {
                "type": "array",
                "maxItems": MAX_SOURCE_IDENTITIES,
                "items": {"type": "string", "minLength": 1},
            },
            "summary": {
                "type": "object",
                "properties": {
                    key: {"type": "integer", "minimum": 0}
                    for key in (
                        "captured_source_count",
                        "sources_with_structural_baseline",
                        "sources_without_structural_baseline",
                        "workbook_layout_source_count",
                        "pdf_layout_source_count",
                        "pdf_layout_unavailable_count",
                        "text_layout_source_count",
                    )
                },
                "required": [
                    "captured_source_count",
                    "sources_with_structural_baseline",
                    "sources_without_structural_baseline",
                    "workbook_layout_source_count",
                    "pdf_layout_source_count",
                    "pdf_layout_unavailable_count",
                ],
                "additionalProperties": False,
            },
            "pinned_reports": _object_schema(
                {
                    "workbook": _WORKBOOK_REPORT_SCHEMA,
                    "pdf": _PDF_REPORT_SCHEMA,
                    "text": _object_schema(
                        {
                            "sha256": _DIGEST_SCHEMA,
                            "layout_source_count": _COUNT_SCHEMA,
                            "recheck_layout_rows_unchanged": {"const": True},
                        },
                        [
                            "sha256",
                            "layout_source_count",
                            "recheck_layout_rows_unchanged",
                        ],
                    ),
                },
                ["workbook", "pdf"],
            ),
            "media_types": {
                "type": "array",
                "items": _MEDIA_TYPE_SCHEMA,
            },
            "unassessed_sources": {
                "type": "array",
                "maxItems": MAX_SOURCE_IDENTITIES,
                "items": _UNASSESSED_SOURCE_SCHEMA,
            },
            "limitations": {"type": "array", "items": {"type": "string"}},
        },
        [
            "schema_version",
            "status",
            "inputs",
            "source_census_sha256",
            "capture_manifest_sha256",
            "source_ids",
            "summary",
            "pinned_reports",
            "media_types",
            "unassessed_sources",
            "limitations",
        ],
    ),
    "annotations": {
        "title": "Reconcile pinned source layouts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}
