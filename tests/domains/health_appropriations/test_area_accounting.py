"""Structural accounting is metadata-only and never extraction certification."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import area_accounting
from archive_govt_nz.domains.health_appropriations.area_accounting import (
    PinnedMetadata,
    reconcile_areas,
)


def pinned(value: object) -> PinnedMetadata:
    payload = json.dumps(value, sort_keys=True).encode()
    return PinnedMetadata(payload, hashlib.sha256(payload).hexdigest())


def inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    digest = "a" * 64
    sheet = {
        "title": "Raw Data",
        "state": "visible",
        "max_row": 4,
        "max_column": 17,
        "formula_cells": 0,
        "merged_ranges": 0,
        "table_names": ["Amounts"],
        "chart_count": 0,
    }
    workbook = {
        "kind": "xlsx",
        "package_member_count": 1,
        "expanded_bytes": 20,
        "has_macros": False,
        "external_link_count": 0,
        "named_range_count": 0,
        "sheets": [sheet],
    }
    donor = {
        "schema_version": "archive-govt-nz.health-donor-manifest/v1",
        "file_count": 2,
        "objects": [
            {
                "path": "data/book.xlsx",
                "sha256": digest,
                "object_id": f"sha256:{digest}",
            },
            {
                "path": "data/document.pdf",
                "sha256": "b" * 64,
                "object_id": f"sha256:{'b' * 64}",
            },
        ],
    }
    census = {
        "schema_version": "archive-govt-nz.health-format-census/v1",
        "items": [
            {"path": "data/book.xlsx", "object_id": f"sha256:{digest}", **workbook},
            {
                "path": "data/document.pdf",
                "object_id": f"sha256:{'b' * 64}",
                "kind": "pdf",
                "byte_count": 20,
                "page_count": 471,
            },
        ],
    }
    receipt = {
        "schema_version": "archive-govt-nz.health-budget-extraction/v1",
        "transformation_id": "budget-expenditure/v1",
        "status": "passed",
        "source_object_sha256": digest,
        "source_locator": "data/book.xlsx",
        "source_vintage": "Budget-2025",
        "excluded_sheets": [],
        "workbook_inventory": deepcopy(workbook),
    }
    return donor, census, receipt


def test_legacy_units_default_unresolved_without_invented_pdf_pages() -> None:
    donor, census, receipt = inputs()
    result = reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))
    assert result["scope"] == "detected_structural_units_only"
    assert result["normalization_verification"] == "not_performed"
    assert result["rights_state"] == "not_evaluated"
    assert len(result["units"]) == 3
    assert {row["state"] for row in result["units"]} == {"unresolved"}
    pdf = next(row for row in result["units"] if row["kind"] == "pdf_structure")
    assert pdf["page_count_observation"] == 471
    assert pdf["table_detection"] == "not_performed"
    table = next(row for row in result["units"] if row["kind"] == "workbook_table")
    assert table["range"] is None


def test_partial_assertion_never_resolves_whole_sheet() -> None:
    donor, census, receipt = inputs()
    snapshots = pinned(donor), pinned(census), (pinned(receipt),)
    planned = reconcile_areas(*snapshots)
    sheet = next(row for row in planned["units"] if row["kind"] == "workbook_sheet")
    assertion = {
        "unit_id": sheet["unit_id"],
        "manifest_sha256": snapshots[2][0].sha256,
        "state": "mapped",
        "coverage": "partial",
        "reason": "selected_health_rows",
    }
    result = reconcile_areas(*snapshots, assertions=(assertion,))
    actual = next(row for row in result["units"] if row["unit_id"] == sheet["unit_id"])
    assert actual["state"] == "unresolved"
    assert actual["contexts"][0]["mapping_assurance"] == "assertion_only"
    assert actual["contexts"][0]["coverage"] == "partial"


def rich(workbook: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(workbook)
    result["schema_version"] = "archive-govt-nz.workbook-inventory/v1"
    for sheet in result["sheets"]:
        sheet.update(
            {
                "dimension": "A1:Q4",
                "formula_coordinates": [],
                "comment_coordinates": [],
                "merged_range_refs": [],
                "table_ranges": [[name, "A1:Q4"] for name in sheet["table_names"]],
                "hidden_rows": [],
                "hidden_columns": [],
                "defined_names": [],
                "formula_cache": [],
            }
        )
    return result


def test_rich_inventory_and_legacy_receipt_keep_exact_same_unit_identity() -> None:
    donor, census, receipt = inputs()
    legacy = reconcile_areas(pinned(donor), pinned(census))
    census["items"][0] = rich(census["items"][0])
    result = reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))
    assert [row["unit_id"] for row in result["units"]] == [
        row["unit_id"] for row in legacy["units"]
    ]
    assert (
        next(row for row in result["units"] if row["kind"] == "workbook_table")["range"]
        == "A1:Q4"
    )


@pytest.mark.parametrize("state", ["mapped", "excluded", "unresolved"])
@pytest.mark.parametrize("coverage", ["whole_unit", "partial"])
def test_explicit_context_states_never_promote_rights(
    state: str, coverage: str
) -> None:
    donor, census, receipt = inputs()
    snapshots = pinned(donor), pinned(census), (pinned(receipt),)
    before = deepcopy((donor, census, receipt))
    unit = next(
        row
        for row in reconcile_areas(*snapshots)["units"]
        if row["kind"] == "workbook_table"
    )
    assertion = {
        "unit_id": unit["unit_id"],
        "manifest_sha256": snapshots[2][0].sha256,
        "state": state,
        "coverage": coverage,
        "reason": "reviewed_selection",
    }
    result = reconcile_areas(*snapshots, assertions=(assertion,))
    row = next(row for row in result["units"] if row["unit_id"] == unit["unit_id"])
    expected = (
        "mapped_assertion_only"
        if state == "mapped" and coverage == "whole_unit"
        else "unresolved"
    )
    assert row["state"] == expected
    assert row["contexts"][0]["state"] == state
    assert row["contexts"][0]["mapping_assurance"] == "assertion_only"
    assert result["source_fixity"] == "not_performed"
    assert result["normalization_verification"] == "not_performed"
    assert (donor, census, receipt) == before
    assert result == reconcile_areas(*snapshots, assertions=(assertion,))


def test_exclusions_are_context_only_and_never_implied_for_tables() -> None:
    donor, census, receipt = inputs()
    receipt["excluded_sheets"] = [{"sheet": "Raw Data", "reason": "outside_selection"}]
    result = reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))
    sheet = next(row for row in result["units"] if row["kind"] == "workbook_sheet")
    assert sheet["state"] == "unresolved"
    assert sheet["contexts"][0]["state"] == "excluded"
    assert sheet["contexts"][0]["scope"] == "adapter_context_only"
    assert sheet["contexts"][0]["mapping_assurance"] == "not_performed"
    assert (
        next(row for row in result["units"] if row["kind"] == "workbook_table")[
            "contexts"
        ]
        == []
    )


def test_sqlite_is_oracle_not_workbook_coverage_and_sql_is_not_copied() -> None:
    donor, census, _ = inputs()
    donor["file_count"] = 3
    donor["objects"].append(
        {
            "path": "data/oracle.sqlite",
            "sha256": "c" * 64,
            "object_id": f"sha256:{'c' * 64}",
        }
    )
    census["items"].append(
        {
            "path": "data/oracle.sqlite",
            "object_id": f"sha256:{'c' * 64}",
            "kind": "sqlite",
            "integrity": "ok",
            "tables": [
                {"name": "health", "row_count": 312, "sql": "private source detail"}
            ],
        }
    )
    result = reconcile_areas(pinned(donor), pinned(census))
    oracle = next(
        row for row in result["units"] if row["kind"] == "sqlite_oracle_table"
    )
    assert oracle["row_count_observation"] == 312
    assert oracle["state"] == "unresolved"
    assert "private source detail" not in json.dumps(result)


@pytest.mark.parametrize(
    "value",
    [
        b"{}",
        b"[]",
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b"\xff",
    ],
)
def test_invalid_pinned_metadata_fails(value: bytes) -> None:
    _, census, _ = inputs()
    snapshot = PinnedMetadata(value, hashlib.sha256(value).hexdigest())
    with pytest.raises((ValueError, KeyError)):
        reconcile_areas(snapshot, pinned(census))


@pytest.mark.parametrize(
    ("field", "value"), [("payload", bytearray(b"{}")), ("sha256", "0" * 64)]
)
def test_pins_and_immutable_bytes_are_required(field: str, value: object) -> None:
    donor, census, _ = inputs()
    data: dict[str, Any] = {
        "payload": pinned(donor).payload,
        "sha256": pinned(donor).sha256,
        field: value,
    }
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(PinnedMetadata(**data), pinned(census))


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_metadata_size_exact_bound(monkeypatch: pytest.MonkeyPatch, delta: int) -> None:
    donor, census, receipt = inputs()
    snapshots = pinned(donor), pinned(census), (pinned(receipt),)
    maximum = max(len(item.payload) for item in (*snapshots[:2], *snapshots[2]))
    monkeypatch.setattr(area_accounting, "MAX_BYTES", maximum + delta)
    if delta < 0:
        with pytest.raises(ValueError, match="area_accounting"):
            reconcile_areas(*snapshots)
    else:
        assert reconcile_areas(*snapshots)["metadata_fixity"] == "verified"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "unknown"),
        ("file_count", True),
        ("file_count", -1),
        ("file_count", 1),
        ("file_count", 1_000_000_001),
    ],
)
def test_donor_root_contract(field: str, value: object) -> None:
    donor, census, _ = inputs()
    donor[field] = value
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", "../book.xlsx"),
        ("path", "/book.xlsx"),
        ("path", "data//book.xlsx"),
        ("path", "data/./book.xlsx"),
        ("path", "data\\book.xlsx"),
        ("path", "C:book.xlsx"),
        ("path", ""),
        ("path", "x" * 257),
        ("path", "data/\nbook.xlsx"),
        ("sha256", "invalid"),
        ("object_id", "sha256:" + "0" * 64),
    ],
)
def test_donor_path_identity_failures(field: str, value: object) -> None:
    donor, census, _ = inputs()
    donor["objects"][0][field] = value
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census))


@pytest.mark.parametrize(
    "change",
    [
        "duplicate_donor",
        "duplicate_census",
        "missing",
        "object_id",
        "wrong_kind",
        "schema",
    ],
)
def test_census_set_and_source_joins(change: str) -> None:
    donor, census, _ = inputs()
    if change == "duplicate_donor":
        donor["objects"].append(deepcopy(donor["objects"][0]))
        donor["file_count"] = 3
    elif change == "duplicate_census":
        census["items"].append(deepcopy(census["items"][0]))
    elif change == "missing":
        census["items"].pop()
    elif change == "object_id":
        census["items"][0]["object_id"] = "sha256:" + "0" * 64
    elif change == "wrong_kind":
        census["items"][0]["kind"] = "pdf"
    else:
        census["schema_version"] = "unknown"
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census))


@pytest.mark.parametrize(
    "change",
    [
        "version",
        "sheet_shape",
        "state",
        "count",
        "table_type",
        "duplicate_sheet",
        "duplicate_table",
        "table_range",
        "range_names",
        "duplicate_range",
    ],
)
def test_workbook_shapes_fail_closed(change: str) -> None:
    donor, census, _ = inputs()
    item = census["items"][0]
    sheet = item["sheets"][0]
    if change == "version":
        item["schema_version"] = "unknown"
    elif change == "sheet_shape":
        sheet["unexpected"] = True
    elif change == "state":
        sheet["state"] = "missing"
    elif change == "count":
        sheet["max_row"] = True
    elif change == "table_type":
        sheet["table_names"] = "Amounts"
    elif change == "duplicate_sheet":
        item["sheets"].append({**sheet, "title": "RAW DATA"})
    elif change == "duplicate_table":
        sheet["table_names"].append("AMOUNTS")
    else:
        census["items"][0] = rich(item)
        ranges = census["items"][0]["sheets"][0]["table_ranges"]
        if change == "table_range":
            ranges[0][1] = "source cell text"
        elif change == "range_names":
            ranges[0][0] = "Absent"
        else:
            ranges.append(ranges[0])
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "unknown"),
        ("transformation_id", "unknown"),
        ("status", "complete"),
        ("source_vintage", ""),
        ("source_object_sha256", "0" * 64),
        ("source_locator", "absent.xlsx"),
        ("excluded_sheets", [{"sheet": "absent", "reason": "not_selected"}]),
        ("excluded_sheets", [{"sheet": "Raw Data", "reason": "private cell text"}]),
    ],
)
def test_receipt_joins_and_context_validation(field: str, value: object) -> None:
    donor, census, receipt = inputs()
    receipt[field] = value
    with pytest.raises((ValueError, KeyError)):
        reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))


def test_duplicate_receipts_and_inventory_mismatch() -> None:
    donor, census, receipt = inputs()
    snapshot = pinned(receipt)
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census), (snapshot, snapshot))
    receipt["workbook_inventory"]["sheets"][0]["table_names"] = []
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))


@pytest.mark.parametrize(
    ("field", "value"), [("max_row", 5), ("state", "hidden"), ("formula_cells", 1)]
)
def test_conflicting_structural_attributes_fail(field: str, value: object) -> None:
    donor, census, receipt = inputs()
    receipt["workbook_inventory"]["sheets"][0][field] = value
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))


def test_conflicting_rich_table_ranges_fail() -> None:
    donor, census, receipt = inputs()
    census["items"][0] = rich(census["items"][0])
    receipt["workbook_inventory"] = rich(receipt["workbook_inventory"])
    receipt["workbook_inventory"]["sheets"][0]["table_ranges"][0][1] = "A1:P4"
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))


@pytest.mark.parametrize(
    "value", ["ZZZ1:A1", "A1:XFE2", "B2:A1", "A1:Q5", "A1:R4", "A1:A1048577"]
)
def test_rich_table_ranges_have_order_and_excel_and_sheet_bounds(value: str) -> None:
    donor, census, _ = inputs()
    census["items"][0] = rich(census["items"][0])
    census["items"][0]["sheets"][0]["table_ranges"][0][1] = value
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census))


def forecast_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(receipt)
    result.update(
        {
            "schema_version": "archive-govt-nz.health-forecast-extraction/v1",
            "transformation_id": "treasury-health-expense-summary/v1",
            "selection": {
                "sheet": "Raw Data",
                "label_cell": "A4",
                "unit_cell": "A1",
                "year_row": 2,
                "amount_type_row": 3,
                "columns": [2, 3],
            },
        }
    )
    return result


def test_forecast_coordinates_retained_without_whole_sheet_mapping() -> None:
    donor, census, original = inputs()
    receipt = forecast_receipt(original)
    result = reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))
    assert result["extractions"][0]["selection"] == receipt["selection"]
    assert result["extractions"][0]["selection_scope"] == "partial_adapter_selection"
    assert all(row["state"] == "unresolved" for row in result["units"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("label_cell", "not cell text"),
        ("unit_cell", "R1"),
        ("label_cell", "A0"),
        ("year_row", 0),
        ("year_row", 5),
        ("amount_type_row", True),
        ("columns", []),
        ("columns", [2, 2]),
        ("columns", [0]),
        ("columns", [18]),
        ("columns", "B"),
        ("sheet", "missing"),
        ("extra", "private cell text"),
    ],
)
def test_partial_selection_rejects_invalid_coordinates(
    field: str, value: object
) -> None:
    donor, census, original = inputs()
    receipt = forecast_receipt(original)
    receipt["selection"][field] = value
    with pytest.raises((ValueError, KeyError)):
        reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))


def test_selected_sheet_cannot_also_be_excluded() -> None:
    donor, census, original = inputs()
    receipt = forecast_receipt(original)
    receipt["excluded_sheets"] = [{"sheet": "Raw Data", "reason": "not_selected"}]
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))


def test_exact_excel_bounds_and_multiple_column_letters() -> None:
    donor, census, _ = inputs()
    census["items"][0] = rich(census["items"][0])
    sheet = census["items"][0]["sheets"][0]
    sheet.update(
        max_row=1_048_576,
        max_column=16_384,
        table_ranges=[["Amounts", "AA1:XFD1048576"]],
    )
    result = reconcile_areas(pinned(donor), pinned(census))
    assert (
        next(row for row in result["units"] if row["kind"] == "workbook_table")["range"]
        == "AA1:XFD1048576"
    )


@pytest.mark.parametrize(("name", "bound"), [("MAX_UNITS", 3), ("MAX_RECEIPTS", 1)])
@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_exact_collection_limits(
    monkeypatch: pytest.MonkeyPatch, name: str, bound: int, delta: int
) -> None:
    donor, census, receipt = inputs()
    monkeypatch.setattr(area_accounting, name, bound + delta)
    if delta < 0:
        with pytest.raises(ValueError, match="area_accounting"):
            reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))
    else:
        assert (
            len(
                reconcile_areas(pinned(donor), pinned(census), (pinned(receipt),))[
                    "units"
                ]
            )
            == 3
        )


def test_conflicting_same_context_assertions_fail() -> None:
    donor, census, receipt = inputs()
    receipt["excluded_sheets"] = [{"sheet": "Raw Data", "reason": "not_selected"}]
    snapshots = pinned(donor), pinned(census), (pinned(receipt),)
    unit = next(
        row
        for row in reconcile_areas(*snapshots)["units"]
        if row["kind"] == "workbook_sheet"
    )
    with pytest.raises(ValueError, match="area_accounting"):
        reconcile_areas(
            *snapshots,
            assertions=(
                {
                    "unit_id": unit["unit_id"],
                    "manifest_sha256": snapshots[2][0].sha256,
                    "state": "mapped",
                    "coverage": "whole_unit",
                    "reason": "asserted",
                },
            ),
        )


def test_contexts_remain_distinct_and_sorted_across_vintages() -> None:
    donor, census, receipt = inputs()
    newer = {**receipt, "source_vintage": "Budget-2026"}
    snapshots = (pinned(receipt), pinned(newer))
    result = reconcile_areas(pinned(donor), pinned(census), snapshots)
    assert result == reconcile_areas(
        pinned(donor), pinned(census), tuple(reversed(snapshots))
    )
    assert {item["source_vintage"] for item in result["extractions"]} == {
        "Budget-2025",
        "Budget-2026",
    }
    assert [item["manifest_sha256"] for item in result["extractions"]] == sorted(
        item.sha256 for item in snapshots
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing_unit",
        "missing_receipt",
        "state",
        "coverage",
        "reason",
        "extra",
        "duplicate",
        "partial_receipt",
        "pdf",
    ],
)
def test_assertions_fail_closed(change: str) -> None:
    donor, census, receipt = inputs()
    if change == "partial_receipt":
        receipt["status"] = "partial"
    snapshots = pinned(donor), pinned(census), (pinned(receipt),)
    units = reconcile_areas(*snapshots)["units"]
    selected = next(
        row
        for row in units
        if row["kind"] == ("pdf_structure" if change == "pdf" else "workbook_sheet")
    )
    assertion = {
        "unit_id": selected["unit_id"],
        "manifest_sha256": snapshots[2][0].sha256,
        "state": "mapped",
        "coverage": "whole_unit",
        "reason": "reviewed",
    }
    if change == "missing_unit":
        assertion["unit_id"] = "0" * 64
    elif change == "missing_receipt":
        assertion["manifest_sha256"] = "0" * 64
    elif change in {"state", "coverage", "reason", "extra"}:
        assertion[change] = "invalid value"
    assertions = (assertion, assertion) if change == "duplicate" else (assertion,)
    with pytest.raises((ValueError, KeyError)):
        reconcile_areas(*snapshots, assertions=assertions)
