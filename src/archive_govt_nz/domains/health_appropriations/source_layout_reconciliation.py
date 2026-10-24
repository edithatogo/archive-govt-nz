# SPDX-License-Identifier: Apache-2.0
"""Reconcile workbook and PDF layout evidence for one captured source cohort."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, NoReturn

_CENSUS_SCHEMA = "archive-govt-nz.health-source-census/v1"
_WORKBOOK_SCHEMA = "archive-govt-nz.health-source-layout-baseline-report/v1"
_PDF_SCHEMA = "archive-govt-nz.health-source-pdf-layout-baseline-report/v1"
_REPORT_SCHEMA = "archive-govt-nz.health-source-layout-reconciliation/v1"
_SHA256_LENGTH = 64
_HEX = frozenset("0123456789abcdef")
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF = "application/pdf"


class SourceLayoutReconciliationError(ValueError):
    """Raised when pinned census or baseline evidence cannot be reconciled."""


def _fail(code: str) -> NoReturn:
    raise SourceLayoutReconciliationError(code)


def _object(payload: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except UnicodeDecodeError, json.JSONDecodeError:
        _fail(code)
    if not isinstance(value, dict):
        _fail(code)
    return value


def _digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_LENGTH
        and all(char in _HEX for char in value)
    )


def _validate_pdf_layout_row(row: dict[str, Any]) -> None:
    status = row.get("status")
    if status not in {"baseline_recorded", "layout_unavailable"}:
        _fail("pdf_layout_status_invalid")
    if status == "layout_unavailable":
        reason = row.get("unavailable_reason")
        if not isinstance(reason, str) or not reason:
            _fail("pdf_layout_unavailable_reason_missing")
        if "layout_sha256" in row:
            _fail("pdf_unavailable_layout_fingerprint_present")
    elif not _digest(row.get("layout_sha256")):
        _fail("layout_fingerprint_invalid")


def _source_rows(  # noqa: C901 - validate evidence fields in fail-closed order.
    report: dict[str, Any],
    key: str,
    identities: dict[str, dict[str, Any]],
    expected_media_type: str,
    *,
    allow_repeats: bool,
) -> tuple[list[dict[str, Any]], set[str]]:
    rows = report.get(key)
    if not isinstance(rows, list):
        _fail("layout_rows_invalid")
    source_ids: set[str] = set()
    seen_rows: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            _fail("layout_row_invalid")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or source_id not in identities:
            _fail("layout_source_not_captured")
        source = identities[source_id]
        if source.get("disposition") != "captured":
            _fail("layout_source_not_captured")
        if source.get("media_type") != expected_media_type:
            _fail("layout_source_media_type_mismatch")
        if row.get("source_object_sha256") != source.get("object_sha256"):
            _fail("layout_source_fixity_mismatch")
        if expected_media_type == _PDF:
            _validate_pdf_layout_row(row)
        elif not _digest(row.get("layout_sha256")):
            _fail("layout_fingerprint_invalid")
        source_ids.add(source_id)
        row_key = (source_id, str(row.get("layout_sha256")))
        if row_key in seen_rows and not allow_repeats:
            _fail("layout_source_duplicate")
        seen_rows.add(row_key)
    return rows, source_ids


def _rows_match(
    left: list[dict[str, Any]], right: list[dict[str, Any]], sort_key: str
) -> bool:
    return sorted(
        left, key=lambda row: (row.get("source_id", ""), row.get(sort_key, ""))
    ) == sorted(
        right, key=lambda row: (row.get("source_id", ""), row.get(sort_key, ""))
    )


def _unassessed_reason(
    source: dict[str, Any], pdf_by_id: dict[str, dict[str, Any]]
) -> str:
    source_id = source["source_id"]
    pdf_row = pdf_by_id.get(source_id)
    if pdf_row is not None and pdf_row.get("status") == "layout_unavailable":
        return "pdf_layout_unavailable"
    if source.get("media_type") == _XLSX:
        return "silver_workbook_inventory_missing"
    return "no_matching_workbook_or_pdf_layout_profile"


def reconcile_source_layout_reports(  # noqa: C901, PLR0912, PLR0915 - explicit evidence boundary.
    census_bytes: bytes,
    workbook_baseline_bytes: bytes,
    pdf_baseline_bytes: bytes,
    workbook_recheck_bytes: bytes,
    pdf_recheck_bytes: bytes,
) -> dict[str, Any]:
    """Reconcile current rechecks to pinned reports without promoting mappings."""
    census = _object(census_bytes, "source_census_invalid")
    workbook = _object(workbook_baseline_bytes, "workbook_baseline_invalid")
    pdf = _object(pdf_baseline_bytes, "pdf_baseline_invalid")
    workbook_recheck = _object(workbook_recheck_bytes, "workbook_recheck_invalid")
    pdf_recheck = _object(pdf_recheck_bytes, "pdf_recheck_invalid")
    if census.get("schema_version") != _CENSUS_SCHEMA:
        _fail("source_census_schema_invalid")
    if (
        workbook.get("schema_version") != _WORKBOOK_SCHEMA
        or workbook_recheck.get("schema_version") != _WORKBOOK_SCHEMA
    ):
        _fail("workbook_baseline_schema_invalid")
    if (
        pdf.get("schema_version") != _PDF_SCHEMA
        or pdf_recheck.get("schema_version") != _PDF_SCHEMA
    ):
        _fail("pdf_baseline_schema_invalid")

    census_sha = hashlib.sha256(census_bytes).hexdigest()
    capture_sha = workbook.get("capture_manifest_sha256")
    reports = (workbook, pdf, workbook_recheck, pdf_recheck)
    if any(
        row.get("source_census_sha256") != census_sha
        or row.get("capture_manifest_sha256") != capture_sha
        for row in reports
    ) or not _digest(capture_sha):
        _fail("layout_cohort_identity_mismatch")

    records = census.get("records")
    if not isinstance(records, list):
        _fail("source_census_records_invalid")
    identities: dict[str, dict[str, Any]] = {}
    captured: dict[str, dict[str, Any]] = {}
    for row in records:
        if not isinstance(row, dict):
            _fail("source_census_row_invalid")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in identities:
            _fail("source_id_missing_or_duplicate")
        identities[source_id] = row
        if row.get("disposition") == "captured":
            if not _digest(row.get("object_sha256")):
                _fail("captured_source_fixity_invalid")
            captured[source_id] = row

    workbook_rows, workbook_ids = _source_rows(
        workbook, "layouts", identities, _XLSX, allow_repeats=True
    )
    workbook_recheck_rows, workbook_recheck_ids = _source_rows(
        workbook_recheck, "layouts", identities, _XLSX, allow_repeats=True
    )
    pdf_rows, pdf_ids = _source_rows(
        pdf, "pdf_layouts", identities, _PDF, allow_repeats=False
    )
    pdf_recheck_rows, pdf_recheck_ids = _source_rows(
        pdf_recheck, "pdf_layouts", identities, _PDF, allow_repeats=False
    )
    if workbook_ids != workbook_recheck_ids or not _rows_match(
        workbook_rows, workbook_recheck_rows, "silver_manifest"
    ):
        _fail("workbook_layout_recheck_changed")
    if pdf_ids != pdf_recheck_ids or not _rows_match(
        pdf_rows, pdf_recheck_rows, "layout_sha256"
    ):
        _fail("pdf_layout_recheck_changed")
    if workbook_ids & pdf_ids:
        _fail("layout_baseline_source_type_overlap")

    pdf_by_id = {row["source_id"]: row for row in pdf_recheck_rows}
    assessed_pdf_ids = {
        row["source_id"]
        for row in pdf_recheck_rows
        if row.get("status") == "baseline_recorded"
    }
    assessed_ids = workbook_recheck_ids | assessed_pdf_ids
    unassessed = sorted(set(captured) - assessed_ids)
    workbook_unassessed = workbook_recheck.get("unassessed_source_ids")
    if not isinstance(workbook_unassessed, list) or set(workbook_unassessed) != (
        set(captured) - workbook_recheck_ids
    ):
        _fail("workbook_unassessed_sources_mismatch")

    by_media: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"captured": set(), "assessed": set()}
    )
    for source_id, source in captured.items():
        media_type = source.get("media_type")
        if not isinstance(media_type, str) or not media_type:
            _fail("captured_source_media_type_missing")
        by_media[media_type]["captured"].add(source_id)
        if source_id in assessed_ids:
            by_media[media_type]["assessed"].add(source_id)

    workbook_excluded_before = workbook.get("excluded_silver_manifests", [])
    workbook_excluded_now = workbook_recheck.get("excluded_silver_manifests", [])
    if not isinstance(workbook_excluded_before, list) or not isinstance(
        workbook_excluded_now, list
    ):
        _fail("excluded_silver_manifests_invalid")

    return {
        "schema_version": _REPORT_SCHEMA,
        "source_census_sha256": census_sha,
        "capture_manifest_sha256": capture_sha,
        "pinned_reports": {
            "workbook": {
                "sha256": hashlib.sha256(workbook_baseline_bytes).hexdigest(),
                "layout_manifest_count": len(workbook_rows),
                "layout_source_count": len(workbook_ids),
                "recheck_layout_rows_unchanged": True,
                "excluded_silver_manifest_count": len(workbook_excluded_before),
                "current_silver_manifests_outside_capture_count": len(
                    workbook_excluded_now
                ),
            },
            "pdf": {
                "sha256": hashlib.sha256(pdf_baseline_bytes).hexdigest(),
                "pdf_capture_count": len(pdf_rows),
                "recheck_layout_rows_unchanged": True,
                "pinned_parser": pdf.get("parser"),
                "recheck_parser": pdf_recheck.get("parser"),
            },
        },
        "summary": {
            "captured_source_count": len(captured),
            "sources_with_structural_baseline": len(assessed_ids),
            "sources_without_structural_baseline": len(unassessed),
            "workbook_layout_source_count": len(workbook_ids),
            "pdf_layout_source_count": len(assessed_pdf_ids),
            "pdf_layout_unavailable_count": len(pdf_ids - assessed_pdf_ids),
        },
        "media_types": [
            {
                "media_type": media_type,
                "captured_source_count": len(counts["captured"]),
                "sources_with_structural_baseline": len(counts["assessed"]),
                "sources_without_structural_baseline": len(
                    counts["captured"] - counts["assessed"]
                ),
            }
            for media_type, counts in sorted(by_media.items())
        ],
        "unassessed_sources": [
            {
                "source_id": source_id,
                "family": captured[source_id].get("family"),
                "media_type": captured[source_id].get("media_type"),
                "reason": _unassessed_reason(captured[source_id], pdf_by_id),
            }
            for source_id in unassessed
        ],
        "limitations": [
            (
                "The report covers only the exact census and capture-manifest "
                "digests above."
            ),
            (
                "PDF structure records geometry/resource metadata, not text, "
                "tables or semantics."
            ),
            (
                "Unassessed media types remain gaps; no baseline, normalization "
                "or mapping is inferred."
            ),
            (
                "Observed layout agreement does not grant cross-vintage "
                "comparability or rights."
            ),
        ],
    }
