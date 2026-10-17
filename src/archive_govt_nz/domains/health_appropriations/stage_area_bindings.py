"""Partial source-area bindings from the existing verified twelve-stage run."""

# Reuse the existing bounded transport rather than adding another parser.

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.area_accounting import (
    PinnedMetadata,
    reconcile_areas,
)
from archive_govt_nz.domains.health_appropriations.raw_reader import _read_rows
from archive_govt_nz.domains.health_appropriations.rebuild_eight import verify_eight
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

STAGES = (
    "budget",
    "revenue",
    "befu-detail",
    "hyefu-detail",
    "befu-chart",
    "hyefu-allowance",
    "befu-residual",
    "hyefu-residual",
    "crown",
)
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_COORDINATE_TEXT = 256


def _require(condition: object) -> None:
    if not condition:
        message = "stage_area_binding_contract"
        raise ValueError(message)


@dataclass
class SheetLinks:
    """Selected fields can overlap between sheets; they are not additive facts."""

    records: set[str] = field(default_factory=set)
    fields: dict[str, set[str]] = field(default_factory=dict)
    rows: int = 0


def _coordinate(value: str, sheets: list[dict[str, Any]]) -> tuple[str, str]:
    _require(isinstance(value, str) and 0 < len(value) <= MAX_COORDINATE_TEXT)
    matches = []
    for sheet in sheets:
        title = sheet["title"]
        escaped = title.replace("'", "''")
        matches.extend(
            (sheet, value[len(prefix) :])
            for prefix in {title + "!", "'" + escaped + "'!"}
            if value.startswith(prefix)
        )
    _require(len(matches) == 1)
    sheet, cell = matches[0]
    match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,6})", cell)
    if match is None:
        message = "stage_area_binding_contract"
        raise ValueError(message)
    letters, row = match.groups()
    column = 0
    for letter in letters:
        column = column * 26 + ord(letter) - ord("A") + 1
    _require(1 <= int(row) <= sheet["max_row"] and 1 <= column <= sheet["max_column"])
    return sheet["title"], cell


def project_stage_bindings(
    name: str,
    receipt: dict[str, Any],
    coverage: dict[str, Any],
    links: list[dict[str, Any]],
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project previously verified fields; this alone is not source admission."""
    _require(name in STAGES)
    _require(
        all(
            receipt[key] == coverage[key]
            for key in ("source_locator", "source_object_sha256")
        )
    )
    ids = set(coverage["record_ids"])
    _require(len(ids) == coverage["facts"] and len(links) == coverage["lineage"])
    _require({row["record_id"] for row in links} == ids)
    _require({row["record_id"] for row in links if row["field"] == "amount"} == ids)
    available = {
        (row["donor_path"], row["source_object_sha256"], row["selector"][0]): row[
            "unit_id"
        ]
        for row in units
        if row["kind"] == "workbook_sheet"
    }
    groups: dict[str, SheetLinks] = {}
    for link in links:
        _require(link["source_object_sha256"] == receipt["source_object_sha256"])
        sheet, cell = _coordinate(
            link["source_coordinate"], receipt["workbook_inventory"]["sheets"]
        )
        group = groups.setdefault(sheet, SheetLinks())
        group.records.add(link["record_id"])
        group.fields.setdefault(link["field"], set()).add(cell)
        group.rows += 1
    result = []
    for sheet, group in sorted(groups.items()):
        unit = available.get(
            (receipt["source_locator"], receipt["source_object_sha256"], sheet)
        )
        _require(unit is not None or name == "crown")
        result.append(
            {
                "stage": name,
                "unit_id": unit,
                "sheet": sheet,
                "source_locator": receipt["source_locator"],
                "source_object_sha256": receipt["source_object_sha256"],
                "source_vintage": receipt["source_vintage"],
                "manifest_sha256": coverage["manifest_sha256"],
                "lineage_sha256": receipt["output_sha256"]["field_lineage.parquet"],
                "inventory_state": "donor_partial_binding"
                if unit
                else "source_separated",
                "reason": "verified_selected_field_lineage"
                if unit
                else "source_not_in_donor_inventory",
                "coverage": "partial",
                "whole_unit_semantics": "unresolved",
                "record_ids": sorted(group.records),
                "lineage_rows": group.rows,
                "amount_coordinates": sorted(group.fields.get("amount", set())),
                "field_coordinates": {
                    key: sorted(values) for key, values in sorted(group.fields.items())
                },
            }
        )
    return result


def build_stage_area_bindings(
    run: Path,
    store: Path,
    *,
    manifest_sha256: str,
    donor: PinnedMetadata,
    census: PinnedMetadata,
) -> dict[str, Any]:
    """Verify existing sources/outputs, then bind selected fields to inventory.

    Reuses verify_eight and its closed per-profile coverage/lineage contracts.
    No workbook re-extraction, source capture, mapping approval or file write.
    Existing whole-unit and adapter-scoped exclusion states are not promoted.
    """
    inventory = reconcile_areas(donor, census)
    verified = verify_eight(run, store, manifest_sha256)
    coverage = {row["stage"]: row for row in verified["coverage"]}
    bindings, catalog = [], []
    for name in STAGES:
        item = coverage[name]
        payload = verified_snapshot(
            run / name / "MANIFEST.json",
            item["manifest_sha256"],
            max_bytes=MAX_MANIFEST_BYTES,
        )
        receipt = json.loads(payload)
        links = _read_rows(
            run / name / "field_lineage.parquet",
            receipt["output_sha256"]["field_lineage.parquet"],
        )
        current = project_stage_bindings(name, receipt, item, links, inventory["units"])
        bindings.extend(current)
        catalog.append(
            {
                "stage": name,
                "manifest_sha256": item["manifest_sha256"],
                "source_object_sha256": item["source_object_sha256"],
                "source_locator": item["source_locator"],
                "source_vintage": receipt["source_vintage"],
                "observed_at": receipt["observed_at"],
                "facts": item["facts"],
                "lineage": item["lineage"],
                "dispositions": item["dispositions"],
                "disposition_sha256": item["disposition_sha256"],
                "disposition_reason_counts": item["reason_counts"],
                "selection_scope": item["scope"],
                "bindings": len(current),
                "source_separated": any(row["unit_id"] is None for row in current),
            }
        )
    return {
        "schema_version": "archive-govt-nz.health-stage-area-bindings/v1",
        "scope": "nine recovered stages; selected fields and source context only",
        "run_manifest_sha256": manifest_sha256,
        "donor_manifest_sha256": donor.sha256,
        "census_sha256": census.sha256,
        "verification": "existing_twelve_stage_source_output_and_lineage_contracts",
        "stage_catalog": catalog,
        "bindings": bindings,
        "global_structural_units": len(inventory["units"]),
        "global_unresolved_units": len(inventory["units"]),
        "record_sets_may_overlap_between_sheets": True,
        "previous_partial_assertions": "unchanged_in_separate_report",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
