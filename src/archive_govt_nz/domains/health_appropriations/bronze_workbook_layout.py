# SPDX-License-Identifier: Apache-2.0
"""Structural layout baselines for captured Bronze workbooks."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from typing import TYPE_CHECKING, Any, NoReturn

import openpyxl

from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.schema_drift import (
    layout_fingerprint,
)

_CENSUS_SCHEMA = "archive-govt-nz.health-source-census/v1"
_REPORT_SCHEMA = "archive-govt-nz.health-bronze-workbook-layout/v1"
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_HEX = frozenset("0123456789abcdef")
_SHA256_LENGTH = 64

if TYPE_CHECKING:
    from pathlib import Path


class BronzeWorkbookLayoutError(ValueError):
    """Raised when pinned source identity or workbook structure is invalid."""


def _fail(code: str) -> NoReturn:
    raise BronzeWorkbookLayoutError(code)


def _object(payload: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except UnicodeDecodeError, json.JSONDecodeError:
        _fail(code)
    if not isinstance(value, dict):
        _fail(code)
    return value


def _structure(inventory: dict[str, object]) -> dict[str, object]:
    """Keep structural fields only; exclude values, URLs, and source labels."""
    allowed = (
        "kind",
        "schema_version",
        "package_member_count",
        "package_members",
        "defined_names",
        "named_range_count",
        "external_link_count",
    )
    sheets = inventory.get("sheets")
    if not isinstance(sheets, list):
        _fail("workbook_inventory_sheets_invalid")
    rows: list[dict[str, object]] = []
    for sheet in sheets:
        if not isinstance(sheet, dict):
            _fail("workbook_inventory_sheet_invalid")
        rows.append(
            {
                key: sheet[key]
                for key in (
                    "title",
                    "state",
                    "max_row",
                    "max_column",
                    "formula_cells",
                    "merged_ranges",
                    "table_names",
                    "chart_count",
                    "dimension",
                    "formula_coordinates",
                    "comment_coordinates",
                    "merged_range_refs",
                    "table_ranges",
                    "hidden_rows",
                    "hidden_columns",
                    "defined_names",
                )
                if key in sheet
            }
        )
    return {key: inventory[key] for key in allowed if key in inventory} | {
        "sheets": rows
    }


def build_bronze_workbook_layout_report(  # noqa: C901, PLR0912 - ordered evidence checks.
    census_bytes: bytes,
    capture_manifest_bytes: bytes,
    cas_root: Path,
) -> dict[str, Any]:
    """Fingerprint captured XLSX structure directly from hash-verified Bronze."""
    census = _object(census_bytes, "source_census_invalid")
    capture = _object(capture_manifest_bytes, "capture_manifest_invalid")
    if census.get("schema_version") != _CENSUS_SCHEMA:
        _fail("source_census_schema_invalid")
    if capture.get("cutoff") != census.get("cutoff"):
        _fail("capture_census_cutoff_mismatch")
    resources = census.get("records")
    results = capture.get("results")
    if not isinstance(resources, list) or not isinstance(results, list):
        _fail("source_layout_inputs_invalid")
    identities: dict[str, dict[str, Any]] = {}
    for row in resources:
        if not isinstance(row, dict):
            _fail("source_census_row_invalid")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in identities:
            _fail("source_id_missing_or_duplicate")
        identities[source_id] = row

    captures: dict[str, tuple[str, int]] = {}
    for result in results:
        if not isinstance(result, dict) or result.get("state") != "captured":
            continue
        source_id, digest, size = (
            result.get("source_id"),
            result.get("sha256"),
            result.get("bytes"),
        )
        if (
            not isinstance(source_id, str)
            or source_id not in identities
            or identities[source_id].get("disposition") != "captured"
            or not isinstance(digest, str)
            or len(digest) != _SHA256_LENGTH
            or any(char not in _HEX for char in digest)
            or type(size) is not int
            or size < 0
            or source_id in captures
        ):
            _fail("capture_identity_invalid")
        captures[source_id] = (digest, size)
    expected = {
        source_id
        for source_id, row in identities.items()
        if row.get("disposition") == "captured"
    }
    if captures.keys() != expected:
        _fail("capture_census_reconciliation_mismatch")

    layouts: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    for source_id, (digest, size) in sorted(captures.items()):
        source = identities[source_id]
        if source.get("media_type") != _XLSX:
            continue
        path = cas_root / digest[:2] / digest
        try:
            payload = path.read_bytes()
        except OSError:
            _fail("bronze_object_missing")
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            _fail("bronze_object_fixity_mismatch")
        try:
            descriptor = _structure(inventory_workbook(BytesIO(payload)))
        except OSError, TypeError, ValueError:
            unavailable.append(
                {"source_id": source_id, "reason": "workbook_layout_invalid"}
            )
            continue
        layouts.append(
            {
                "source_id": source_id,
                "family": source.get("family"),
                "source_object_sha256": digest,
                "source_bytes": size,
                "layout_sha256": layout_fingerprint(descriptor),
                "layout": descriptor,
            }
        )
    return {
        "schema_version": _REPORT_SCHEMA,
        "source_census_sha256": hashlib.sha256(census_bytes).hexdigest(),
        "capture_manifest_sha256": hashlib.sha256(capture_manifest_bytes).hexdigest(),
        "parser": {"name": "openpyxl", "version": openpyxl.__version__},
        "summary": {
            "captured_source_count": len(captures),
            "captured_xlsx_count": sum(
                row.get("media_type") == _XLSX for row in identities.values()
            ),
            "xlsx_with_bronze_layout": len(layouts),
            "xlsx_layout_unavailable": len(unavailable),
        },
        "layouts": layouts,
        "unavailable": unavailable,
        "limitations": [
            (
                "Structural workbook inventory only; no cell values or source "
                "semantics are asserted."
            ),
            (
                "A matching fingerprint does not establish cross-vintage "
                "comparability, rights, or normalization approval."
            ),
        ],
    }
