"""Read-only fixity verification for canonical Health Gold packages."""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from pathlib import Path

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
MAX_OUTPUTS = 512
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_VERSION = "archive-govt-nz.health-canonical-gold/v2"
_REVISION_KEY_FIELDS = (
    "recordset",
    "measure",
    "source_label",
    "unit",
    "currency",
    "price_basis",
    "base_period",
    "denominator_definition",
    "institutional_coverage",
    "accounting_basis",
    "period_token",
)
_PRODUCT_REVISION_KEY_FIELDS = {
    "budget": (
        "period_token",
        "amount_type",
        "unit",
        "vote",
        "department",
        "portfolio",
        "source_label",
    ),
    "revenue": (
        "period_token",
        "amount_type",
        "unit",
        "vote",
        "department",
        "revenue_type",
        "source_label",
    ),
}
_COMMON = {
    "schema_version": "archive-govt-nz.health-canonical-gold-verification/v1",
    "verification_scope": "manifest_declared_output_fixity",
    "rights_state": "not_evaluated",
    "publication": "not_performed",
}


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _fail_type(message: str) -> NoReturn:
    raise TypeError(message)


def _valid_product_revision_reports(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(_PRODUCT_REVISION_KEY_FIELDS):
        return False
    for name, key_fields in _PRODUCT_REVISION_KEY_FIELDS.items():
        report = value.get(name)
        if (
            not isinstance(report, dict)
            or report.get("scope")
            != "same_literal_source_dimensions_and_period_token_within_product"
            or report.get("key_fields") != list(key_fields)
            or report.get("completeness") != "observed_rows_only"
            or report.get("interpretation") != "not_assessed"
            or not isinstance(report.get("candidates"), list)
        ):
            return False
        counts = (
            report.get("shared_series_period_count"),
            report.get("unchanged_series_period_count"),
            report.get("ambiguous_series_period_count"),
            report.get("changed_candidate_count"),
        )
        if any(type(count) is not int or count < 0 for count in counts):
            return False
        if counts[3] != len(report["candidates"]):
            return False
    return True


CANONICAL_GOLD_VERIFICATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        **{key: {"const": value} for key, value in _COMMON.items()},
        "status": {"enum": ["verified", "failed"]},
        "error": {"const": "invalid_canonical_gold_package"},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "output_count": {"type": "integer", "minimum": 0},
        "output_bytes": {"type": "integer", "minimum": 0},
        "products": {"type": "array", "items": {"type": "string"}},
        "temporal_coverage_groups": {"type": "integer", "minimum": 0},
    },
    "required": [*_COMMON, "status"],
    "additionalProperties": False,
    "oneOf": [
        {
            "properties": {"status": {"const": "verified"}},
            "required": [
                "manifest_sha256",
                "output_count",
                "output_bytes",
                "products",
                "temporal_coverage_groups",
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


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(result) != len(pairs):
        _fail("duplicate_manifest_key")
    return result


def _read_manifest(path: Path) -> tuple[bytes, dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        _fail("invalid_manifest_file")
    with path.open("rb") as stream:
        payload = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(payload) > MAX_MANIFEST_BYTES:
        _fail("manifest_byte_limit")
    value = json.loads(payload, object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        _fail_type("invalid_manifest")
    return payload, value


def _output_name_is_safe(name: object) -> bool:
    return (
        type(name) is str
        and bool(name)
        and name not in {".", "..", "MANIFEST.json", "FAILURE.json"}
        and "/" not in name
        and "\\" not in name
    )


def _verify_outputs(root: Path, outputs: object) -> tuple[int, int]:
    if not isinstance(outputs, dict) or not 0 < len(outputs) <= MAX_OUTPUTS:
        _fail("invalid_outputs")
    if any(not _output_name_is_safe(name) for name in outputs):
        _fail("invalid_output_name")
    if {path.name for path in root.iterdir()} != {*outputs, "MANIFEST.json"}:
        _fail("output_inventory_mismatch")

    total_bytes = 0
    for name, metadata in outputs.items():
        if not isinstance(metadata, dict):
            _fail("invalid_output_metadata")
        digest = metadata.get("sha256")
        size = metadata.get("bytes")
        if (
            type(digest) is not str
            or _DIGEST.fullmatch(digest) is None
            or type(size) is not int
            or not 0 <= size <= MAX_PACKAGE_BYTES
        ):
            _fail("invalid_output_metadata")
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            _fail("output_size_mismatch")
        with path.open("rb") as stream:
            actual_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual_digest != digest:
            _fail("output_digest_mismatch")
        total_bytes += size
        if total_bytes > MAX_PACKAGE_BYTES:
            _fail("package_byte_limit")
    return len(outputs), total_bytes


def _verify(root: Path, manifest_sha256: str) -> dict[str, Any]:
    if (
        type(manifest_sha256) is not str
        or _DIGEST.fullmatch(manifest_sha256) is None
        or root.is_symlink()
        or not root.is_dir()
    ):
        _fail("invalid_package_root")
    manifest_bytes, manifest = _read_manifest(root / "MANIFEST.json")
    if hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256:
        _fail("manifest_digest_mismatch")
    if manifest.get("schema_version") != _SCHEMA_VERSION:
        _fail("invalid_manifest_schema")
    outputs = manifest.get("outputs")
    output_count, output_bytes = _verify_outputs(root, outputs)
    products = manifest.get("products")
    temporal_report = manifest.get("temporal_coverage_report")
    classification_report = manifest.get("classification_drift_report")
    revision_report = manifest.get("revision_reconciliation_report")
    try:
        revision_payload = json.loads(
            (root / "historical_revision_reconciliation.json").read_text(
                encoding="utf-8"
            )
        )
    except OSError, UnicodeDecodeError, json.JSONDecodeError:
        revision_payload = None
    if (
        not isinstance(products, dict)
        or not isinstance(temporal_report, dict)
        or temporal_report.get("schema_version")
        != "archive-govt-nz.health-temporal-coverage/v1"
        or not isinstance(temporal_report.get("groups"), list)
        or not isinstance(classification_report, dict)
        or classification_report.get("schema_version")
        != "archive-govt-nz.health-classification-drift/v1"
        or classification_report.get("mapping") != "not_inferred"
        or not isinstance(classification_report.get("candidates"), list)
        or not isinstance(revision_report, dict)
        or revision_report.get("schema_version")
        != "archive-govt-nz.health-revision-reconciliation/v1"
        or revision_report.get("key_fields") != list(_REVISION_KEY_FIELDS)
        or revision_report.get("completeness")
        != "historical_budget_revenue_product_rows"
        or revision_report.get("difference_interpretation") != "not_assessed"
        or revision_report.get("other_product_revisions") != "not_assessed"
        or revision_report.get("cross_source_comparison") != "not_performed"
        or not _valid_product_revision_reports(revision_report.get("product_revisions"))
        or not isinstance(revision_report.get("candidates"), list)
        or revision_payload != revision_report
        or any(type(name) is not str or not name for name in products)
    ):
        _fail("invalid_gold_reports")
    return {
        **_COMMON,
        "status": "verified",
        "manifest_sha256": manifest_sha256,
        "output_count": output_count,
        "output_bytes": output_bytes,
        "products": sorted(products),
        "temporal_coverage_groups": len(temporal_report["groups"]),
    }


def verify_canonical_gold_package(root: Path, manifest_sha256: str) -> dict[str, Any]:
    """Verify a pinned manifest and every declared direct-child output.

    This checks package fixity and basic report presence only. It neither
    rereads Parquet semantics nor establishes source completeness, rights,
    analytical approval, or publication. Failures return a fixed redacted
    receipt and never create or modify local state.
    """
    try:
        return _verify(root, manifest_sha256)
    except Exception:  # noqa: BLE001 - keep paths, bytes and parser errors private
        return {
            **_COMMON,
            "status": "failed",
            "error": "invalid_canonical_gold_package",
        }
