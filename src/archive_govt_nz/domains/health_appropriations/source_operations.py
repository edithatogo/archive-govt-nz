"""Allowlisted local source extraction and redacted read-only preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import (
    cpi,
    moh_indicators,
    pharmac,
    qes,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import source_context

MAX_CONTEXT = 2048
PROFILES = MappingProxyType(
    {
        "cpiq-se9a/v1": (
            cpi.TRANSFORMATION,
            ("input", "selected", "numeric", "missing", "unselected"),
            "cpi_facts.parquet",
            "row_dispositions.parquet",
        ),
        "moh-hair2024-fig27/v1": (
            moh_indicators.TRANSFORMATION,
            ("input", "facts", "lineage"),
            "moh_indicator_facts.parquet",
            "row_dispositions.parquet",
        ),
        "moh-hair2024-fig28/v1": (
            moh_indicators.TRANSFORMATION,
            ("input", "facts", "lineage"),
            "moh_indicator_facts.parquet",
            "row_dispositions.parquet",
        ),
        "qes-june2026-table8/v1": (
            qes.TRANSFORMATION,
            ("normalized", "field_lineage", "inventoried_cells"),
            "qes_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "pharmac-cpb-20260807/v1": (
            pharmac.TRANSFORMATION,
            ("facts", "lineage", "table_cells"),
            "pharmaceutical_budget_facts.parquet",
            "cell_dispositions.parquet",
        ),
    }
)
_COMMON = {
    "schema_version": "archive-govt-nz.health-source-operation/v1",
    "verification_scope": "adapter_execution_only",
    "rights_state": "not_evaluated",
    "publication_state": "local_validation_only",
}
_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$", "maxLength": 64}
_COUNT = {"type": "integer", "minimum": 0}
_TEXT = {"type": "string", "minLength": 1, "maxLength": MAX_CONTEXT}
SOURCE_PREFLIGHT_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "profile": {"enum": list(PROFILES)},
        "expected_sha256": _DIGEST,
        **dict.fromkeys(
            ("source", "output_dir", "source_vintage", "source_locator", "observed_at"),
            _TEXT,
        ),
    },
    "required": [
        "profile",
        "expected_sha256",
        "source",
        "output_dir",
        "source_vintage",
        "source_locator",
        "observed_at",
    ],
}
SOURCE_OPERATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        **{key: {"const": value} for key, value in _COMMON.items()},
        "status": {"enum": ["preflight_passed", "written_local", "failed"]},
        "error": {"const": "invalid_source_operation"},
        "profile": {"enum": list(PROFILES)},
        "source_object_sha256": _DIGEST,
        "transformation_id": {
            "enum": sorted({value[0] for value in PROFILES.values()})
        },
        "counts": {"type": "object"},
        "output_sha256": {"type": "object"},
    },
    "required": [*_COMMON, "status"],
    "oneOf": [
        {
            "properties": {"status": {"const": "failed"}},
            "required": ["error"],
            "maxProperties": len(_COMMON) + 2,
        },
        {
            "properties": {"status": {"enum": ["preflight_passed", "written_local"]}},
            "required": [
                "profile",
                "source_object_sha256",
                "transformation_id",
                "counts",
            ],
            "not": {"required": ["error"]},
            "oneOf": [
                {
                    "properties": {
                        "profile": {"const": name},
                        "transformation_id": {"const": values[0]},
                        "counts": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": dict.fromkeys(values[1], _COUNT),
                            "required": list(values[1]),
                        },
                        "output_sha256": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": dict.fromkeys(
                                (values[2], "field_lineage.parquet", values[3]), _DIGEST
                            ),
                            "required": [values[2], "field_lineage.parquet", values[3]],
                        },
                    }
                }
                for name, values in PROFILES.items()
            ],
            "allOf": [
                {
                    "if": {"properties": {"status": {"const": "written_local"}}},
                    "then": {"required": ["output_sha256"]},
                    "else": {"not": {"required": ["output_sha256"]}},
                }
            ],
        },
    ],
}


@dataclass(frozen=True, slots=True)
class SourceRequest:
    """Explicit caller context; validation is not acquisition attestation."""

    source: Path
    output_dir: Path
    profile: str
    expected_sha256: str
    source_vintage: str
    source_locator: str
    observed_at: str


def _validate(request: SourceRequest, *, dry_run: bool) -> None:
    arguments = {
        "source": str(request.source),
        "output_dir": str(request.output_dir),
        "profile": request.profile,
        "expected_sha256": request.expected_sha256,
        "source_vintage": request.source_vintage,
        "source_locator": request.source_locator,
        "observed_at": request.observed_at,
    }
    Draft202012Validator(SOURCE_PREFLIGHT_INPUT_SCHEMA).validate(arguments)
    locator = urlsplit(request.source_locator)
    if (
        not isinstance(dry_run, bool)
        or locator.scheme != "https"
        or not locator.hostname
        or locator.username is not None
        or locator.password is not None
        or locator.query
        or locator.fragment
        or any(
            not char.isprintable() or char.isspace() for char in request.source_locator
        )
        or request.source.is_symlink()
        or not request.source.is_file()
        or request.output_dir.exists()
        or request.output_dir.is_symlink()
    ):
        message = "invalid_source_operation"
        raise ValueError(message)
    source_context(
        request.expected_sha256,
        request.source_locator,
        request.source_vintage,
        request.observed_at,
    )


def _invoke(request: SourceRequest, *, dry_run: bool) -> dict[str, Any]:
    context = {
        "expected_sha256": request.expected_sha256,
        "observed_at": request.observed_at,
        "source_vintage": request.source_vintage,
        "source_locator": request.source_locator,
    }
    if request.profile == "cpiq-se9a/v1":
        return cpi.normalize_cpi(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == "qes-june2026-table8/v1":
        return qes.normalize_qes(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == "pharmac-cpb-20260807/v1":
        return pharmac.normalize_pharmac_budget(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    profile = {
        "moh-hair2024-fig27/v1": "fig27/v1",
        "moh-hair2024-fig28/v1": "fig28/v1",
    }[request.profile]
    return moh_indicators.normalize_moh_indicators(
        request.source, request.output_dir, **context, profile=profile, dry_run=dry_run
    )


def operate_source(request: SourceRequest, *, dry_run: bool = True) -> dict[str, Any]:
    """Preflight by default; only a real False enables exclusive local writing.

    No caller locator/path/context or raw rows escape in these compact receipts.
    Signed/query URLs are rejected before parsing. Expected parser/IO failures
    are redacted; interrupts propagate. Existing parser output schemas, original
    bytes, donor rebuild and archive-status semantics remain unchanged.
    """
    try:
        _validate(request, dry_run=dry_run)
        raw = _invoke(request, dry_run=dry_run)
        expected_status = (
            "passed"
            if not dry_run or request.profile == "qes-june2026-table8/v1"
            else "planned"
        )
        if raw["status"] != expected_status:
            return {**_COMMON, "status": "failed", "error": "invalid_source_operation"}
        profile = PROFILES[request.profile]
        result = {
            **_COMMON,
            "status": "preflight_passed" if dry_run else "written_local",
            "profile": request.profile,
            "source_object_sha256": request.expected_sha256,
            "transformation_id": profile[0],
            "counts": raw["counts"],
        }
        if not dry_run:
            result["output_sha256"] = raw["output_sha256"]
        Draft202012Validator(SOURCE_OPERATION_SCHEMA).validate(result)
    except Exception:  # noqa: BLE001 - never disclose parser diagnostics or user context
        return {**_COMMON, "status": "failed", "error": "invalid_source_operation"}
    return result


def preflight_source(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate the closed MCP input shape before constructing paths; never write."""
    try:
        Draft202012Validator(SOURCE_PREFLIGHT_INPUT_SCHEMA).validate(arguments)
        request = SourceRequest(
            Path(arguments["source"]),
            Path(arguments["output_dir"]),
            arguments["profile"],
            arguments["expected_sha256"],
            arguments["source_vintage"],
            arguments["source_locator"],
            arguments["observed_at"],
        )
        return operate_source(request, dry_run=True)
    except Exception:  # noqa: BLE001 - schema errors can contain sensitive input values
        return {**_COMMON, "status": "failed", "error": "invalid_source_operation"}
