"""Read-only fixity verification for contextual Health Gold packages."""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pathlib import Path

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "archive-govt-nz.health-context-gold/v1"
_OUTPUTS = {
    "context_observations.parquet",
    "context_coverage.parquet",
    "context_quality.parquet",
    "context-quality-report.md",
}
_SOURCE_MARKER_COUNT = 4
_ERROR = "invalid_context_gold_package"
_COMMON = {
    "schema_version": "archive-govt-nz.health-context-gold-verification/v1",
    "verification_scope": "manifest_declared_output_fixity",
    "rights_state": "not_evaluated",
    "denominator_selection": "not_performed",
    "publication": "not_performed",
}

CONTEXT_GOLD_VERIFICATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        **{key: {"const": value} for key, value in _COMMON.items()},
        "status": {"enum": ["verified", "failed"]},
        "error": {"const": "invalid_context_gold_package"},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "output_count": {"type": "integer", "const": 4},
        "output_bytes": {"type": "integer", "minimum": 0},
        "source_marker_count": {"type": "integer", "const": 4},
        "quality_report": {"const": "verified_as_declared_output"},
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
                "source_marker_count",
                "quality_report",
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


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate_manifest_key")
        result[key] = value
    return result


def _fail(reason: str) -> None:
    raise ValueError(reason)


def _read_manifest(root: Path, digest: str) -> dict[str, Any]:
    marker = root / "MANIFEST.json"
    if marker.is_symlink() or not marker.is_file():
        _fail("invalid_manifest_file")
    with marker.open("rb") as stream:
        payload = stream.read(MAX_MANIFEST_BYTES + 1)
    if (
        len(payload) > MAX_MANIFEST_BYTES
        or hashlib.sha256(payload).hexdigest() != digest
    ):
        _fail("manifest_digest_mismatch")
    manifest = json.loads(payload, object_pairs_hook=_pairs)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != _SCHEMA:
        _fail("invalid_manifest_schema")
    if (
        manifest.get("rights_state") != "not_evaluated"
        or manifest.get("denominator_selection") != "not_performed"
        or manifest.get("publication") != "not_performed"
    ):
        _fail("invalid_assessment_boundary")
    return manifest


def _verify_products(root: Path, manifest: dict[str, Any]) -> tuple[int, int]:
    products = manifest.get("products")
    if not isinstance(products, dict) or set(products) != _OUTPUTS:
        _fail("invalid_products")
    product_entries = cast("dict[str, Any]", products)
    if {path.name for path in root.iterdir()} != {*_OUTPUTS, "MANIFEST.json"}:
        _fail("output_inventory_mismatch")
    total = 0
    for name in sorted(_OUTPUTS):
        entry = product_entries[name]
        if not isinstance(entry, dict):
            _fail("invalid_product_metadata")
        digest, size, rows = entry.get("sha256"), entry.get("bytes"), entry.get("rows")
        path = root / name
        if (
            type(digest) is not str
            or _DIGEST.fullmatch(digest) is None
            or type(size) is not int
            or not 0 <= size <= MAX_PACKAGE_BYTES
            or type(rows) is not int
            or rows < 0
            or path.is_symlink()
            or not path.is_file()
            or path.stat().st_size != size
        ):
            _fail("invalid_product_metadata")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest:
            _fail("product_digest_mismatch")
        total += cast("int", size)
        if total > MAX_PACKAGE_BYTES:
            _fail("package_byte_limit")
    return len(_OUTPUTS), total


def _verify(root: Path, manifest_sha256: str) -> dict[str, Any]:
    if (
        type(manifest_sha256) is not str
        or _DIGEST.fullmatch(manifest_sha256) is None
        or root.is_symlink()
        or not root.is_dir()
    ):
        _fail("invalid_package_root")
    manifest = _read_manifest(root, manifest_sha256)
    output_count, total = _verify_products(root, manifest)
    markers = manifest.get("source_marker_sha256")
    if (
        not isinstance(markers, list)
        or len(markers) != _SOURCE_MARKER_COUNT
        or any(
            type(value) is not str or _DIGEST.fullmatch(value) is None
            for value in markers
        )
    ):
        _fail("invalid_source_markers")
    return {
        **_COMMON,
        "status": "verified",
        "manifest_sha256": manifest_sha256,
        "output_count": output_count,
        "output_bytes": total,
        "source_marker_count": _SOURCE_MARKER_COUNT,
        "quality_report": "verified_as_declared_output",
    }


def verify_context_gold_package(root: Path, manifest_sha256: str) -> dict[str, Any]:
    """Verify pinned manifest and exact output fixity without writes.

    This confirms declared bytes and closure only; it does not recompute Silver
    facts, source coverage, rights, denominator suitability, or publication.
    """
    try:
        return _verify(root, manifest_sha256)
    except Exception:  # noqa: BLE001 - stable redacted read-only receipt
        return {
            **_COMMON,
            "status": "failed",
            "error": _ERROR,
        }
