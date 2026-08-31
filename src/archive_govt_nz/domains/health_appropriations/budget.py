"""Budget expenditure facts from immutable, hash-verified original XLSX bytes.

No formula evaluation, donor-database dependency or redistribution approval is
implied. Outputs occupy a new directory; MANIFEST.json is the completion marker.
An interrupted write leaves an incomplete directory which must not be consumed.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from openpyxl import load_workbook

from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    exact_number,
    identity,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

    from openpyxl.cell.cell import Cell, MergedCell
    from openpyxl.worksheet.worksheet import Worksheet

_MAX_SOURCE_BYTES = 64 * 1024 * 1024
_SHEET = "Raw Data"
_TRANSFORMATION = "budget-expenditure/v1"
_FIELDS = {
    "Year": "year",
    "Department": "department",
    "Appropriation Name": "appropriation_name",
    "Functional Classification": "functional_classification",
    "Amount $000": "amount",
    "Amount Type": "amount_type",
    "Portfolio Name": "portfolio_name",
}
_LABELS = tuple(name for name in _FIELDS if name not in ("Year", "Amount $000"))
_DISPOSITION_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("sheet", pa.string()),
        ("source_row", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
        ("record_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)


def _headers(sheet: Worksheet) -> list[str]:
    cells = next(sheet.iter_rows(min_row=1, max_row=1))
    headers = [cell.value for cell in cells]
    if (
        any(not isinstance(value, str) or not value.strip() for value in headers)
        or any(cell.data_type in ("f", "e") for cell in cells)
        or len(set(headers)) != len(headers)
        or not {"Vote", *_FIELDS}.issubset(headers)
    ):
        raise ValueError("invalid_headers")
    return [str(value) for value in headers]


def _classify(
    cells: tuple[Cell | MergedCell, ...], values: dict[str, Any]
) -> tuple[str, str]:
    if all(cell.value is None for cell in cells):
        return "blank", "empty_row"
    vote = values["Vote"]
    if (
        not isinstance(vote, str)
        or not vote.strip()
        or next(
            cell for cell, name in zip(cells, values, strict=True) if name == "Vote"
        ).data_type
        in ("f", "e")
    ):
        return "rejected", "invalid_vote"
    if vote != "Health":
        return "out_of_scope", "non_health_vote"
    if any(cell.data_type == "f" for cell in cells):
        return "rejected", "formula_not_evaluated"
    if any(cell.data_type == "e" for cell in cells):
        return "rejected", "spreadsheet_error"
    if any(
        not isinstance(values[name], str) or not values[name].strip()
        for name in _LABELS
    ):
        return "rejected", "missing_label"
    if exact_number(values["Year"], year=True) is None:
        return "rejected", "invalid_year"
    if exact_number(values["Amount $000"]) is None:
        return "rejected", "invalid_amount"
    return "normalized", "named_columns"


def _extract(
    sheet: Worksheet, context: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    headers = _headers(sheet)
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    for source_row, cells in enumerate(sheet.iter_rows(min_row=2), start=2):
        values = dict(zip(headers, (cell.value for cell in cells), strict=True))
        disposition, reason = _classify(cells, values)
        record_id = identity(
            _TRANSFORMATION, context["source_object_sha256"], _SHEET, source_row
        )
        dispositions.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "source_locator": context["source_locator"],
                "sheet": _SHEET,
                "source_row": source_row,
                "disposition": disposition,
                "reason": reason,
                "record_id": record_id if disposition == "normalized" else None,
                "raw_values_json": encode_json(values),
            }
        )
        if disposition != "normalized":
            continue
        fact = {
            **context,
            "record_id": record_id,
            "schema_version": "archive-govt-nz.health-appropriations-silver/v1",
            "recordset": "appropriation_fact",
            "valid_time_start": None,
            "rights_state": "not_evaluated",
            "quality_flags": ["financial_year_basis_unverified"],
            "transformation_id": _TRANSFORMATION,
            "lineage_id": identity(record_id, "lineage"),
            "donor_table": None,
            "donor_row_number": None,
            **{field: values[name] for name, field in _FIELDS.items()},
            "year": int(Decimal(str(values["Year"]))),
            "amount": exact_number(values["Amount $000"]),
            "measure": "appropriation_amount",
            "unit": "NZD_thousands",
            "raw_values_json": encode_json(values),
        }
        facts.append(fact)
        for name, cell in zip(headers, cells, strict=True):
            field = _FIELDS.get(name, f"raw:{name}")
            lineage.append(
                {
                    "lineage_id": fact["lineage_id"],
                    "record_id": record_id,
                    "field": field,
                    "source_object_sha256": context["source_object_sha256"],
                    "source_locator": context["source_locator"],
                    "source_coordinate": f"'{_SHEET}'!{cell.coordinate}",
                    "raw_value": str(cell.value),
                    "normalized_value": str(fact.get(field, cell.value)),
                    "rule": _TRANSFORMATION,
                }
            )
    return facts, lineage, dispositions


def normalize_budget_workbook(
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    observed_at: str,
    source_vintage: str,
    source_locator: str,
) -> dict[str, object]:
    """Extract Health rows with dispositions and exact source-cell lineage.

    Source may be an extensionless Bronze CAS object. All parsing uses one
    verified in-memory snapshot. Other worksheets remain inventoried, not
    normalized. A passed receipt establishes extraction, not publication rights.
    """
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=_MAX_SOURCE_BYTES)
    inventory = inventory_workbook(BytesIO(payload))
    workbook = load_workbook(BytesIO(payload), data_only=False, keep_links=True)
    try:
        if _SHEET not in workbook.sheetnames:
            raise ValueError("missing_raw_data_sheet")
        facts, lineage, dispositions = _extract(workbook[_SHEET], context)
        excluded = [
            {"sheet": name, "reason": "not_budget_raw_data"}
            for name in workbook.sheetnames
            if name != _SHEET
        ]
    finally:
        workbook.close()
    counts = {
        name: sum(row["disposition"] == name for row in dispositions)
        for name in ("normalized", "out_of_scope", "blank", "rejected")
    }
    counts["input"] = len(dispositions)
    outputs = {
        "budget_facts.parquet": pa.Table.from_pylist(facts, schema=SILVER_SCHEMA),
        "field_lineage.parquet": pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        "row_dispositions.parquet": pa.Table.from_pylist(
            dispositions, schema=_DISPOSITION_SCHEMA
        ),
    }
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.health-budget-extraction/v1",
        "transformation_id": _TRANSFORMATION,
        "status": "partial" if counts["rejected"] else "passed" if facts else "empty",
        "source_object_sha256": expected_sha256,
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "counts": counts,
        "excluded_sheets": excluded,
        "workbook_inventory": inventory,
    }
    return write_workbook_outputs(output_dir, outputs, receipt)
