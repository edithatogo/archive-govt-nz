"""Pinned donor detail literals with source-reference headers, never cache values."""

from __future__ import annotations

import re
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

from openpyxl import load_workbook
from openpyxl.utils.cell import column_index_from_string

from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.historical import (
    _exact_amount,
    _number_tokens,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

    from openpyxl.worksheet.worksheet import Worksheet

PROFILES = {
    "BEFU-2025": (
        "dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6",
        "Core Crown Expense Tables",
        102,
    ),
    "HYEFU-2024": (
        "725399c09323594c921dbcc493206abe59bf7b91dd968b8c7f6f3a67d4707969",
        "Expense Tables",
        103,
    ),
}
MAX_COLUMN = 16384
MAX_ROW = 1048576


def _require(condition: object) -> None:
    if not condition:
        message = "donor_health_detail_contract"
        raise ValueError(message)


def resolve_header(sheet: Worksheet, coordinate: str) -> tuple[str, dict[str, str]]:
    """Trace at most eight same-sheet single-cell links to literal text.

    This deliberately supports no arithmetic, names, ranges, external links,
    formula cache substitution or general Excel evaluation.
    """
    chain: dict[str, str] = {}
    for _ in range(8):
        _require(coordinate not in chain)
        cell = sheet[coordinate]
        value = cell.value
        _require(isinstance(value, str))
        value = cast("str", value)
        chain[coordinate] = value
        if cell.data_type != "f":
            _require(cell.data_type == "s")
            return value, chain
        match = re.fullmatch(r"=\$?([A-Z]{1,3})\$?([1-9][0-9]{0,6})", value)
        _require(match is not None)
        match = cast("re.Match[str]", match)
        column, row = match.groups()
        _require(column_index_from_string(column) <= MAX_COLUMN and int(row) <= MAX_ROW)
        coordinate = column + row
    message = "donor_health_detail_header_depth"
    raise ValueError(message)


def admit_donor_health_detail(source: Path, vintage: str) -> dict[str, Any]:
    """Return raw/context records only from either exact verified original."""
    _require(vintage in PROFILES)
    digest, title, first = PROFILES[vintage]
    _require(source.is_file() and not source.is_symlink())
    payload = verified_snapshot(source, digest, max_bytes=1024 * 1024)
    inventory = inventory_workbook(BytesIO(payload))
    tokens = _number_tokens(payload)[title]
    book = load_workbook(BytesIO(payload), data_only=False, keep_links=True)
    try:
        sheet = book[title]
        unit_coordinate = f"D{first - 2}"
        _require(sheet[unit_coordinate].value == "($millions)")
        notes = {
            f"D{row}": sheet[f"D{row}"].value for row in range(first + 11, first + 14)
        }
        records = []
        for column in "FGHIJKLMNO":
            year, years = resolve_header(sheet, f"{column}{first - 3}")
            kind, kinds = resolve_header(sheet, f"{column}{first - 2}")
            _require(year == str(2020 + ord(column) - ord("F")))
            _require(kind == ("Actual" if column < "K" else "Forecast"))
            for row in range(first, first + 8):
                coordinate = f"{column}{row}"
                token = tokens.get(coordinate, "")
                amount = _exact_amount(token)
                _require(sheet[coordinate].data_type == "n" and amount is not None)
                label_coordinate = f"D{row}"
                label = sheet[label_coordinate].value
                _require(isinstance(label, str))
                records.append(
                    {
                        "source_sha256": digest,
                        "source_vintage": vintage,
                        "sheet": title,
                        "coordinate": coordinate,
                        "source_number_token": token,
                        "amount": amount,
                        "number_format": sheet[coordinate].number_format,
                        "label": label,
                        "year_label": year,
                        "amount_type": kind,
                        "unit": "($millions)",
                        "currency": None,
                        "period_start": None,
                        "period_end": None,
                        "raw_context": {
                            **years,
                            **kinds,
                            **notes,
                            label_coordinate: label,
                            unit_coordinate: "($millions)",
                        },
                    }
                )
        return {
            "schema_version": "donor-health-detail-literal-context/v1",
            "status": "raw_context_only",
            "records": records,
            "workbook_inventory": inventory,
            "formula_totals": {
                "range": f"F{first + 9}:O{first + 9}",
                "disposition": "excluded_formula_cache_not_admitted",
            },
            "consolidation_equivalence": "not_asserted",
            "rights_state": "not_evaluated",
        }
    finally:
        book.close()
