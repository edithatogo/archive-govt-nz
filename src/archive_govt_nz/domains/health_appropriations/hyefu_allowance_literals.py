"""Pinned HYEFU operating allowances, preserving average-per-annum semantics."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any

from openpyxl import load_workbook

from archive_govt_nz.domains.health_appropriations.befu_chart_literals import (
    _selected_tokens,
)
from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.historical import _exact_amount
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

SOURCE_SHA256 = "f77bdab5ef808b0e451a52b9b448a52b07899bc4523da3c02aa5725325d6203c"
SHEET = "Table 2.4"
UNIT = "$millions (average per annum)"
ANCHORS: dict[str, str] = {
    "B1": "Table 2.4 - Future budget operating allowances",
    "B2": "Source: The Treasury",
    "B4": "Year ending 30 June",
    "B5": UNIT,
    "C5": "Budget 2025",
    "D5": "Budget 2026",
    "E5": "Budget 2027",
    "F5": "Budget 2028",
    "B6": "Announced Budget operating allowance",
    "B7": "Pre-commitments",
    "B8": "Non-discretionary spending",
    "B10": "Remaining unallocated future operating allowances",
}
SELECTED = tuple(f"{column}{row}" for row in (6, 7, 8, 10) for column in "CDEF")


def _require(condition: object) -> None:
    if not condition:
        message = "hyefu_allowance_contract"
        raise ValueError(message)


def admit_hyefu_allowances(source: Path) -> dict[str, Any]:
    """Return 16 source observations, never converted to yearly totals."""
    _require(source.is_file() and not source.is_symlink())
    payload = verified_snapshot(source, SOURCE_SHA256, max_bytes=4 * 1024 * 1024)
    inventory = inventory_workbook(BytesIO(payload))
    tokens = _selected_tokens(payload, selected_sheets=frozenset({SHEET}))[SHEET]
    book = load_workbook(BytesIO(payload), data_only=False, keep_links=True)
    try:
        sheet = book[SHEET]
        _require(all(sheet[key].value == value for key, value in ANCHORS.items()))
        context = {
            cell.coordinate: cell.value
            for row in sheet
            for cell in row
            if cell.value is not None and cell.coordinate not in SELECTED
        }
        records = []
        for coordinate in SELECTED:
            cell = sheet[coordinate]
            token = tokens.get(coordinate, "")
            amount = _exact_amount(token)
            _require(cell.data_type == "n" and amount is not None)
            label_cell, budget_cell = f"B{cell.row}", f"{cell.column_letter}5"
            records.append(
                {
                    "source_sha256": SOURCE_SHA256,
                    "source_vintage": "HYEFU-2024",
                    "source_locator": "data/raw/hyefu24-charts-data.xlsx",
                    "sheet": SHEET,
                    "coordinate": coordinate,
                    "label": sheet[label_cell].value,
                    "budget_label": sheet[budget_cell].value,
                    "amount": amount,
                    "source_number_token": token,
                    "source_number_format": cell.number_format,
                    "unit": UNIT,
                    "currency": None,
                    "period_interpretation": "budget_label_not_annual_total",
                    "lineage": {
                        "amount": f"{SHEET}!{coordinate}",
                        "label": f"{SHEET}!{label_cell}",
                        "budget_label": f"{SHEET}!{budget_cell}",
                        "unit": f"{SHEET}!B5",
                        "period_context": f"{SHEET}!B4",
                        "table_title": f"{SHEET}!B1",
                    },
                    "raw_context": context,
                }
            )
        return {
            "schema_version": "hyefu-allowance-literal-context/v1",
            "status": "raw_context_only",
            "records": records,
            "workbook_inventory": inventory,
            "arithmetic_or_cross_vintage_equivalence": "not_performed",
            "rights_state": "not_evaluated",
        }
    finally:
        book.close()
