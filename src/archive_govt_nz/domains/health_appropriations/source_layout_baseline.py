"""Evidence-bounded source layout baselines from retained Silver manifests."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import TYPE_CHECKING, Any, NoReturn

from archive_govt_nz.domains.health_appropriations.schema_drift import (
    layout_fingerprint,
)

_SCHEMA = "archive-govt-nz.health-source-census/v1"
_REPORT = "archive-govt-nz.health-source-layout-baseline-report/v1"
_HEX = frozenset("0123456789abcdef")
_SHA256_LENGTH = 64
_MIN_COMPARABLE_VINTAGES = 2

if TYPE_CHECKING:
    from pathlib import Path


class SourceLayoutBaselineError(ValueError):
    """Raised when census, capture, Silver or Bronze evidence is inconsistent."""


def _fail(code: str) -> NoReturn:
    raise SourceLayoutBaselineError(code)


def _load_object(payload: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except UnicodeDecodeError, json.JSONDecodeError:
        _fail(code)
    if not isinstance(value, dict):
        _fail(code)
    return value


def _layout_descriptor(manifest: dict[str, Any]) -> dict[str, Any] | None:
    inventory = manifest.get("workbook_inventory")
    if not isinstance(inventory, dict):
        return None
    sheets = inventory.get("sheets", [])
    if not isinstance(sheets, list):
        _fail("silver_workbook_sheets_invalid")
    structural_sheets = []
    for sheet in sheets:
        if not isinstance(sheet, dict):
            _fail("silver_workbook_sheet_invalid")
        structural_sheets.append(
            {
                key: sheet[key]
                for key in (
                    "title",
                    "state",
                    "dimension",
                    "max_row",
                    "max_column",
                    "merged_ranges",
                    "table_names",
                    "table_ranges",
                    "formula_coordinates",
                )
                if key in sheet
            }
        )
    return {
        key: inventory[key]
        for key in (
            "kind",
            "schema_version",
            "package_member_count",
            "package_members",
            "defined_names",
            "named_range_count",
        )
        if key in inventory
    } | {"sheets": structural_sheets}


def build_source_layout_baseline_report(  # noqa: C901, PLR0912, PLR0915 - explicit validation boundary.
    census_bytes: bytes,
    capture_manifest_bytes: bytes,
    silver_root: Path,
    cas_root: Path,
) -> dict[str, Any]:
    """Fingerprint captured source layouts already characterized by Silver.

    A repeated source object under the same transformation is checked for stable
    structure. Distinct vintages under one transformation are compared as
    observed layouts; variation is reported without normalization approval.
    Captured sources without a workbook inventory stay explicitly unassessed.
    """
    census = _load_object(census_bytes, "source_census_invalid")
    capture = _load_object(capture_manifest_bytes, "capture_manifest_invalid")
    if census.get("schema_version") != _SCHEMA:
        _fail("source_census_schema_invalid")
    if capture.get("cutoff") != census.get("cutoff"):
        _fail("capture_census_cutoff_mismatch")
    resources = census.get("records")
    results = capture.get("results")
    if not isinstance(resources, list) or not isinstance(results, list):
        _fail("source_layout_inputs_invalid")
    identities: dict[str, dict[str, Any]] = {}
    for resource in resources:
        if not isinstance(resource, dict):
            _fail("source_census_row_invalid")
        source_id = resource.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in identities:
            _fail("source_id_missing_or_duplicate")
        identities[source_id] = resource

    captures: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict) or result.get("state") != "captured":
            continue
        digest = result.get("sha256")
        source_id = result.get("source_id")
        if (
            not isinstance(digest, str)
            or len(digest) != _SHA256_LENGTH
            or any(char not in _HEX for char in digest)
            or not isinstance(source_id, str)
            or source_id not in identities
            or digest in captures
        ):
            _fail("capture_identity_invalid")
        if identities[source_id].get("disposition") != "captured":
            _fail("capture_inventory_state_mismatch")
        object_path = cas_root / digest[:2] / digest
        try:
            source_bytes = object_path.read_bytes()
        except OSError:
            _fail("bronze_object_missing")
        if hashlib.sha256(source_bytes).hexdigest() != digest:
            _fail("bronze_object_hash_mismatch")
        expected_size = result.get("bytes")
        if isinstance(expected_size, int) and len(source_bytes) != expected_size:
            _fail("bronze_object_size_mismatch")
        captures[digest] = {"source_id": source_id, "bytes": len(source_bytes)}
    expected_captured = {
        row["source_id"]
        for row in resources
        if isinstance(row, dict) and row.get("disposition") == "captured"
    }
    if {value["source_id"] for value in captures.values()} != expected_captured:
        _fail("capture_census_reconciliation_mismatch")

    entries: list[dict[str, Any]] = []
    excluded_manifests: list[dict[str, str]] = []
    manifests = sorted(silver_root.rglob("MANIFEST.json"))
    for path in manifests:
        raw = path.read_bytes()
        manifest = _load_object(raw, "silver_manifest_invalid")
        digest = manifest.get("source_object_sha256")
        if digest is None:
            continue
        if digest not in captures:
            excluded_manifests.append(
                {
                    "silver_manifest": path.relative_to(silver_root).as_posix(),
                    "silver_manifest_sha256": hashlib.sha256(raw).hexdigest(),
                    "state": "outside_pinned_capture_scope",
                }
            )
            continue
        descriptor = _layout_descriptor(manifest)
        if descriptor is None:
            continue
        transformation = manifest.get("transformation_id")
        vintage = manifest.get("source_vintage")
        if not isinstance(transformation, str) or not transformation:
            _fail("silver_transformation_missing")
        if not isinstance(vintage, str) or not vintage:
            _fail("silver_vintage_missing")
        entries.append(
            {
                "source_id": captures[digest]["source_id"],
                "family": identities[captures[digest]["source_id"]].get("family"),
                "source_vintage": vintage,
                "source_object_sha256": digest,
                "source_bytes": captures[digest]["bytes"],
                "transformation_id": transformation,
                "silver_manifest": path.relative_to(silver_root).as_posix(),
                "silver_manifest_sha256": hashlib.sha256(raw).hexdigest(),
                "layout_sha256": layout_fingerprint(descriptor),
                "layout": descriptor,
            }
        )
    entries.sort(
        key=lambda row: (
            str(row["family"]),
            row["transformation_id"],
            row["source_vintage"],
            row["source_object_sha256"],
            row["silver_manifest"],
        )
    )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        grouped[entry["transformation_id"]].append(entry)
    comparisons = []
    for transformation, group in sorted(grouped.items()):
        by_vintage: dict[str, set[str]] = defaultdict(set)
        for entry in group:
            by_vintage[entry["source_vintage"]].add(entry["layout_sha256"])
        repeated = [
            {
                "source_vintage": vintage,
                "layout_fingerprints": sorted(fingerprints),
                "state": "stable"
                if len(fingerprints) == 1
                else "repeat_build_layout_variation",
            }
            for vintage, fingerprints in sorted(by_vintage.items())
        ]
        vintage_fingerprints = {
            vintage: next(iter(fingerprints))
            for vintage, fingerprints in by_vintage.items()
            if len(fingerprints) == 1
        }
        comparisons.append(
            {
                "transformation_id": transformation,
                "vintage_count": len(by_vintage),
                "vintages": repeated,
                "cross_vintage_state": (
                    "not_comparable_single_vintage"
                    if len(by_vintage) < _MIN_COMPARABLE_VINTAGES
                    else "matching"
                    if len(vintage_fingerprints) == len(by_vintage)
                    and len(set(vintage_fingerprints.values())) == 1
                    else "layout_variation_observed"
                ),
                "normalization_approval": "not_granted",
            }
        )

    characterized = {entry["source_object_sha256"] for entry in entries}
    captured_ids = {value["source_id"] for value in captures.values()}
    characterized_ids = {entry["source_id"] for entry in entries}
    return {
        "schema_version": _REPORT,
        "source_census_sha256": hashlib.sha256(census_bytes).hexdigest(),
        "capture_manifest_sha256": hashlib.sha256(capture_manifest_bytes).hexdigest(),
        "summary": {
            "captured_object_count_verified": len(captures),
            "captured_objects_with_layout_baseline": len(characterized),
            "captured_sources_with_layout_baseline": len(characterized_ids),
            "captured_sources_without_layout_baseline": len(
                captured_ids - characterized_ids
            ),
            "layout_manifest_count": len(entries),
            "transformation_count": len(comparisons),
        },
        "comparisons": comparisons,
        "layouts": entries,
        "excluded_silver_manifests": excluded_manifests,
        "unassessed_source_ids": sorted(captured_ids - characterized_ids),
        "limitations": [
            (
                "Only captured sources with retained Silver workbook inventories are "
                "fingerprinted."
            ),
            (
                "A layout variation is an observed structural difference, not proof "
                "of semantic drift."
            ),
            (
                "A matching layout does not establish source-calendar completeness "
                "or rights."
            ),
            "No source values, locators, or inferred mapping approvals are included.",
        ],
    }
