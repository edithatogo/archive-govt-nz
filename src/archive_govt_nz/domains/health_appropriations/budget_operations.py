"""Compact read-only receipts for previously reviewed standalone Budget packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.budget_reader import (
    read_verified_budget,
)

if TYPE_CHECKING:
    from pathlib import Path

_COMMON = {
    "schema_version": "archive-govt-nz.health-budget-verification/v1",
    "verification_scope": "reviewed_package_only",
    "rights_state": "not_evaluated",
    "publication_state": "local_validation_only",
}
_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_COUNT = {"type": "integer", "minimum": 0}
MAX_CONTEXT_LENGTH = 2048
_CONTEXT_FIELDS = ("source_locator", "source_vintage", "observed_at")

BUDGET_VERIFICATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        **{name: {"const": value} for name, value in _COMMON.items()},
        "status": {"enum": ["passed", "failed"]},
        "error": {"const": "invalid_budget_package"},
        "manifest_sha256": _DIGEST,
        "source_object_sha256": _DIGEST,
        **{
            name: {"type": "string", "minLength": 1, "maxLength": MAX_CONTEXT_LENGTH}
            for name in _CONTEXT_FIELDS
        },
        "counts": {
            "type": "object",
            "additionalProperties": False,
            "properties": dict.fromkeys(
                ("facts", "field_lineage", "dispositions"), _COUNT
            ),
            "required": ["facts", "field_lineage", "dispositions"],
        },
        "disposition_counts": {
            "type": "object",
            "additionalProperties": False,
            "properties": dict.fromkeys(
                ("input", "normalized", "out_of_scope", "blank", "rejected"), _COUNT
            ),
            "required": ["input", "normalized", "out_of_scope", "blank", "rejected"],
        },
    },
    "required": [*_COMMON, "status"],
    "additionalProperties": False,
    "oneOf": [
        {
            "properties": {"status": {"const": "passed"}},
            "required": [
                "manifest_sha256",
                "source_object_sha256",
                *_CONTEXT_FIELDS,
                "counts",
                "disposition_counts",
            ],
            "not": {"required": ["error"]},
        },
        {
            "properties": {"status": {"const": "failed"}},
            "required": ["error"],
            "maxProperties": len(_COMMON) + 2,
        },
    ],
}


def verify_budget_package(package_dir: Path, manifest_sha256: str) -> dict[str, Any]:
    """Verify capped package snapshots and return metadata, never raw records.

    No source workbook, network or output directory is opened. The underlying
    reader checks package consistency, not arbitrary source truth or rights.
    Every failure is redacted at this operational boundary; interrupts propagate.
    """
    failure = {**_COMMON, "status": "failed", "error": "invalid_budget_package"}
    try:
        facts, lineage, dispositions, manifest = read_verified_budget(
            package_dir, manifest_sha256
        )
        if any(
            not 1 <= len(manifest[name]) <= MAX_CONTEXT_LENGTH
            for name in _CONTEXT_FIELDS
        ):
            return failure
        return {
            **_COMMON,
            "status": "passed",
            "manifest_sha256": manifest_sha256,
            "source_object_sha256": manifest["source_object_sha256"],
            **{name: manifest[name] for name in _CONTEXT_FIELDS},
            "counts": {
                "facts": len(facts),
                "field_lineage": len(lineage),
                "dispositions": len(dispositions),
            },
            "disposition_counts": manifest["counts"],
        }
    except Exception:  # noqa: BLE001 - parser/IO diagnostics must not disclose source bytes
        return failure
