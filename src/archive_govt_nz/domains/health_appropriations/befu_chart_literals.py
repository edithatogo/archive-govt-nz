"""Pinned BEFU chart-table literals; no additions, netting or cache admission."""

from __future__ import annotations

import re
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypedDict
from zipfile import ZipFile

from openpyxl import load_workbook

from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.historical import (
    _exact_amount,
    _xml,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

SOURCE_SHA256 = "cf98f5e21f60c76c7d05f788df7955fb45cfdd780c12cb18e26ff8e83615e168"


class Profile(TypedDict):
    """Literal coordinates and exact header anchors for one pinned table."""

    family: str
    anchors: dict[str, str | int]
    selected: list[str]
    excluded: list[str]


PROFILES: dict[str, Profile] = {
    "Table 2.4": {
        "family": "budget_2025_expenditure_decisions",
        "anchors": {
            "B1": (
                "Table 2.4 - Composition of the net increase in core Crown expenditure "
                "by functional classification from Budget 2025 decisions1"
            ),
            "B4": "Year ending 30 June",
            "B5": "$millions",
            **{
                f"{column}4": year
                for column, year in zip("DEFGH", range(2025, 2030), strict=True)
            },
            **{f"{column}5": "Forecast" for column in "DEFGH"},
            "I4": "5-year",
            "I5": "Total",
        },
        "selected": [f"{column}{row}" for row in range(7, 18) for column in "DEFGHI"],
        "excluded": [],
    },
    "Table 2.5": {
        "family": "budget_2025_capital_decisions",
        "anchors": {
            "B1": (
                "Table 2.5 - Budget 2025 capital decisions (by sectors) "
                "and impact on the fiscal forecasts"
            ),
            "B4": "Year ending 30 June",
            "B5": "$millions",
            "D4": "5-year",
            "D5": "Total",
            "E4": "Post",
            "E5": "2029",
            "F4": "Overall Budget 2025",
            "F5": "Total",
        },
        "selected": [
            f"{column}{row}" for row in [7, 8, 9, 10, 11, 12, 14] for column in "DE"
        ],
        "excluded": [f"F{row}" for row in range(7, 16)] + ["D13", "E13", "D15", "E15"],
    },
    "Table 2.8": {
        "family": "budget_2026_allowances",
        "anchors": {
            "B1": "Table 2.8 - Budget 2026 allowances",
            "B4": "Year ending 30 June",
            "B5": "$millions",
            "C4": "Operating",
            "D4": "Capital",
            "C5": "allowance",
            "D5": "allowance",
            "B7": "Pre-commitments:",
        },
        "selected": [f"{column}{row}" for row in [6, 8, 9] for column in "CD"],
        "excluded": ["C11", "D11"],
    },
}


def _require(condition: object) -> None:
    if not condition:
        message = "befu_chart_literal_contract"
        raise ValueError(message)


def _selected_tokens(payload: bytes) -> dict[str, dict[str, str]]:
    # Inventory caps and whole-object fixity precede this lexical read. Unlike
    # historical._number_tokens, unrelated chart-sheet parts are not worksheets.
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    with ZipFile(BytesIO(payload)) as package:
        relations = list(_xml(package, "xl/_rels/workbook.xml.rels"))
        by_id = {item.get("Id"): item for item in relations}
        _require(len(by_id) == len(relations))
        result = {}
        for sheet in _xml(package, "xl/workbook.xml").findall(f"{ns}sheets/{ns}sheet"):
            title = sheet.get("name", "")
            if title not in PROFILES:
                continue
            _require(title not in result)
            relation = by_id[sheet.get(f"{rel}id")]
            target = relation.get("Target", "")
            member = target[1:] if target.startswith("/") else "xl/" + target
            _require(
                relation.get("TargetMode") != "External"
                and re.fullmatch(r"xl/worksheets/[A-Za-z0-9_.-]+\.xml", member)
            )
            tokens = {}
            seen = set()
            for cell in _xml(package, member).findall(f"{ns}sheetData/{ns}row/{ns}c"):
                coordinate = cell.get("r", "")
                _require(coordinate not in seen)
                seen.add(coordinate)
                values = cell.findall(f"{ns}v")
                _require(len(values) <= 1)
                if (
                    cell.get("t", "n") == "n"
                    and cell.find(f"{ns}f") is None
                    and values
                    and values[0].text is not None
                ):
                    tokens[coordinate] = values[0].text
            result[title] = tokens
        _require(set(result) == set(PROFILES))
        return result


def admit_befu_chart_literals(source: Path) -> dict[str, Any]:
    """Read one hash-pinned original into distinct raw/context records only."""
    _require(source.is_file() and not source.is_symlink())
    payload = verified_snapshot(source, SOURCE_SHA256, max_bytes=4 * 1024 * 1024)
    inventory_workbook(BytesIO(payload))
    tokens = _selected_tokens(payload)
    book = load_workbook(BytesIO(payload), data_only=False, keep_links=True)
    try:
        records = []
        excluded = []
        for title, profile in PROFILES.items():
            sheet = book[title]
            _require(
                all(
                    sheet[key].value == value
                    for key, value in profile["anchors"].items()
                )
            )
            # Complete literal context for these small pinned tables, including
            # footnotes and section labels; formula strings are never interpreted.
            context = {
                cell.coordinate: cell.value
                for row in sheet
                for cell in row
                if cell.value is not None and cell.coordinate not in profile["selected"]
            }
            for coordinate in profile["selected"]:
                cell = sheet[coordinate]
                token = tokens[title].get(coordinate, "")
                amount = _exact_amount(token)
                label_coordinate = f"B{cell.row}"
                label = sheet[label_coordinate].value
                _require(
                    cell.data_type == "n"
                    and amount is not None
                    and isinstance(label, str)
                )
                records.append(
                    {
                        "source_sha256": SOURCE_SHA256,
                        "source_vintage": "BEFU-2025",
                        "source_locator": "data/raw/befu25-charts-data.xlsx",
                        "sheet": title,
                        "coordinate": coordinate,
                        "family": profile["family"],
                        "label": label,
                        "amount": amount,
                        "source_number_token": token,
                        "source_number_format": cell.number_format,
                        "column_headers": [
                            sheet[f"{cell.column_letter}4"].value,
                            sheet[f"{cell.column_letter}5"].value,
                        ],
                        "unit": "$millions",
                        "currency": None,
                        "period_interpretation": "source_headers_only",
                        "lineage": {
                            "amount": f"{title}!{coordinate}",
                            "label": f"{title}!{label_coordinate}",
                            "unit": f"{title}!B5",
                            "column_header_4": f"{title}!{cell.column_letter}4",
                            "column_header_5": f"{title}!{cell.column_letter}5",
                        },
                        "raw_context": context,
                    }
                )
            for coordinate in profile["excluded"]:
                _require(sheet[coordinate].data_type == "f")
                excluded.append(
                    {
                        "sheet": title,
                        "coordinate": coordinate,
                        "formula": sheet[coordinate].value,
                        "reason": "formula_cache_not_admitted",
                    }
                )
        return {
            "schema_version": "befu-chart-literal-context/v1",
            "status": "raw_context_only",
            "records": records,
            "excluded_formulas": excluded,
            "rights_state": "not_evaluated",
            "analytical_addition_or_netting": "not_performed",
        }
    finally:
        book.close()
