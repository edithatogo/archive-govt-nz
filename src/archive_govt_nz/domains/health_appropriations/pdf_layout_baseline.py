"""Page-level structural baselines for retained official PDF vintages."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypeGuard

import pypdf
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from archive_govt_nz.domains.health_appropriations.schema_drift import (
    layout_fingerprint,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pypdf._page import PageObject

_SCHEMA = "archive-govt-nz.health-source-census/v1"
_REPORT = "archive-govt-nz.health-source-pdf-layout-baseline-report/v1"
_SHA256_LENGTH = 64
_HEX = frozenset("0123456789abcdef")
_RESOURCE_KEYS = (
    "/Font",
    "/XObject",
    "/ExtGState",
    "/ColorSpace",
    "/Pattern",
    "/Shading",
    "/Properties",
)


class PdfLayoutBaselineError(ValueError):
    """Raised when census, capture or Bronze PDF evidence is inconsistent."""


def _pdf_page_descriptor(page: PageObject) -> dict[str, Any]:
    resources = page.get("/Resources") or {}
    return {
        "media_box": [str(value) for value in page.mediabox],
        "crop_box": [str(value) for value in page.cropbox],
        "rotation": int(page.get("/Rotate", 0) or 0) % 360,
        "resource_counts": {
            key: len(resources.get(key, {}))
            for key in _RESOURCE_KEYS
            if key in resources
        },
        "annotation_count": len(page.get("/Annots", [])),
    }


def _parse_pdf(payload: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        reader = PdfReader(BytesIO(payload), strict=True)
        if reader.is_encrypted:
            return None, "encrypted_pdf"
        profiles = Counter(
            json.dumps(
                _pdf_page_descriptor(page), sort_keys=True, separators=(",", ":")
            )
            for page in reader.pages
        )
    except PdfReadError, FileNotDecryptedError:
        return None, "pdf_parse_error"
    descriptor = {
        "page_count": len(reader.pages),
        "page_layouts": [
            {"profile": json.loads(profile), "page_count": count}
            for profile, count in sorted(profiles.items())
        ],
        "metadata_keys": sorted(str(key) for key in (reader.metadata or {})),
    }
    return descriptor, None


def _load_inputs(
    census_bytes: bytes, capture_manifest_bytes: bytes
) -> tuple[dict[str, Any], list[Any], list[Any]]:
    try:
        census = json.loads(census_bytes)
        capture = json.loads(capture_manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        msg = "pdf_layout_input_invalid"
        raise PdfLayoutBaselineError(msg) from exc
    if not isinstance(census, dict) or not isinstance(capture, dict):
        msg = "pdf_layout_input_invalid"
        raise PdfLayoutBaselineError(msg)
    if census.get("schema_version") != _SCHEMA:
        msg = "pdf_layout_census_schema_invalid"
        raise PdfLayoutBaselineError(msg)
    if census.get("cutoff") != capture.get("cutoff"):
        msg = "pdf_layout_cutoff_mismatch"
        raise PdfLayoutBaselineError(msg)
    records, results = census.get("records"), capture.get("results")
    if not isinstance(records, list) or not isinstance(results, list):
        msg = "pdf_layout_input_shape_invalid"
        raise PdfLayoutBaselineError(msg)
    return census, records, results


def _capture_rows(
    results: list[Any], identities: dict[str, Any], cas_root: Path
) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        if not _is_pdf_capture(result):
            continue
        source_id, digest = _validated_capture_identity(result, identities)
        payload = _read_verified_bronze(result, digest, cas_root)
        descriptor, error = _parse_pdf(payload)
        resource = identities[source_id]
        row: dict[str, Any] = {
            "source_id": source_id,
            "family": resource.get("family"),
            "source_title": resource.get("title"),
            "source_object_sha256": digest,
            "source_bytes": len(payload),
            "status": "baseline_recorded"
            if descriptor is not None
            else "layout_unavailable",
        }
        if descriptor is None:
            row["unavailable_reason"] = error
        else:
            row["layout_sha256"] = layout_fingerprint(descriptor)
            row["layout"] = descriptor
        rows.append(row)
    return sorted(rows, key=lambda row: row["source_id"])


def _is_pdf_capture(result: object) -> TypeGuard[dict[str, Any]]:
    return (
        isinstance(result, dict)
        and result.get("state") == "captured"
        and str(result.get("content_type", "")).split(";", maxsplit=1)[0].strip()
        == "application/pdf"
    )


def _validated_capture_identity(
    result: dict[str, Any], identities: dict[str, Any]
) -> tuple[str, str]:
    source_id, digest = result.get("source_id"), result.get("sha256")
    if (
        not isinstance(source_id, str)
        or source_id not in identities
        or identities[source_id].get("disposition") != "captured"
        or not isinstance(digest, str)
        or len(digest) != _SHA256_LENGTH
        or any(char not in _HEX for char in digest)
    ):
        msg = "pdf_capture_identity_invalid"
        raise PdfLayoutBaselineError(msg)
    return source_id, digest


def _read_verified_bronze(result: dict[str, Any], digest: str, cas_root: Path) -> bytes:
    try:
        payload = (cas_root / digest[:2] / digest).read_bytes()
    except OSError as exc:
        msg = "pdf_bronze_object_missing"
        raise PdfLayoutBaselineError(msg) from exc
    if hashlib.sha256(payload).hexdigest() != digest:
        msg = "pdf_bronze_object_hash_mismatch"
        raise PdfLayoutBaselineError(msg)
    expected_bytes = result.get("bytes")
    if isinstance(expected_bytes, int) and len(payload) != expected_bytes:
        msg = "pdf_bronze_object_size_mismatch"
        raise PdfLayoutBaselineError(msg)
    return payload


def _family_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["status"] == "baseline_recorded":
            by_family[str(row["family"])].add(row["layout_sha256"])
    return [
        {
            "family": family,
            "source_count": sum(row["family"] == family for row in rows),
            "distinct_layout_count": len(fingerprints),
            "state": "matching"
            if len(fingerprints) == 1
            else "layout_variation_observed",
        }
        for family, fingerprints in sorted(by_family.items())
    ]


def build_pdf_layout_baseline_report(
    census_bytes: bytes,
    capture_manifest_bytes: bytes,
    cas_root: Path,
) -> dict[str, Any]:
    """Fingerprint PDF page geometry/resource structure without extracting text."""
    _, records, results = _load_inputs(census_bytes, capture_manifest_bytes)
    identities: dict[str, Any] = {}
    for row in records:
        if isinstance(row, dict) and isinstance(row.get("source_id"), str):
            identities[row["source_id"]] = row
    rows = _capture_rows(results, identities, cas_root)
    family_summary = _family_summary(rows)
    return {
        "schema_version": _REPORT,
        "source_census_sha256": hashlib.sha256(census_bytes).hexdigest(),
        "capture_manifest_sha256": hashlib.sha256(capture_manifest_bytes).hexdigest(),
        "parser": {"name": "pypdf", "version": pypdf.__version__, "strict": True},
        "summary": {
            "pdf_capture_count": len(rows),
            "layout_baseline_count": sum(
                row["status"] == "baseline_recorded" for row in rows
            ),
            "layout_unavailable_count": sum(
                row["status"] == "layout_unavailable" for row in rows
            ),
            "family_count": len(family_summary),
        },
        "families": family_summary,
        "pdf_layouts": rows,
        "limitations": [
            (
                "Only page geometry, rotation, resource counts and metadata keys "
                "are fingerprinted."
            ),
            (
                "Text, typography, tables, semantics and within-page layout are not "
                "assessed."
            ),
            (
                "A structural variation is not an approved mapping or normalization "
                "decision."
            ),
            "Rights, discovery and source-calendar completeness are not assessed.",
        ],
    }
