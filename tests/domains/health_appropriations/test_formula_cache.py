"""Cached formula results are observations, never recalculated fiscal truth."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook


def _cached_fixture(tmp_path: Path) -> Path:
    source = tmp_path / "template.xlsx"
    workbook = Workbook()
    workbook.save(source)
    workbook.close()
    path = tmp_path / "cached.xlsx"
    worksheet = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row r="1">'
        '<c r="A1"><f>1-1</f><v>0</v></c>'
        '<c r="B1" t="b"><f>FALSE()</f><v>0</v></c>'
        '<c r="C1" t="str"><f>"cached content"</f><v>cached content</v></c>'
        '<c r="D1" t="e"><f>1/0</f><v>#DIV/0!</v></c>'
        '<c r="E1"><f>1+1</f></c>'
        '<c r="F1"><f>2+2</f><v/></c>'
        '<c r="G1"><v>23</v></c>'
        "</row></sheetData></worksheet>"
    )
    with ZipFile(source) as original, ZipFile(path, "w") as output:
        for part in original.infolist():
            payload = (
                worksheet.encode()
                if part.filename == "xl/worksheets/sheet1.xml"
                else original.read(part.filename)
            )
            output.writestr(part, payload)
    return path


def test_formula_cache_states_do_not_evaluate_or_disclose_values(
    tmp_path: Path,
) -> None:
    path = _cached_fixture(tmp_path)
    before = path.read_bytes()
    result = inventory_workbook(path)
    assert result["formula_cache_freshness"] == "not_verified"
    sheets = result["sheets"]
    assert isinstance(sheets, list)
    assert sheets[0]["formula_cache"] == (
        {"coordinate": "A1", "state": "stored_value", "data_type": "n"},
        {"coordinate": "B1", "state": "stored_value", "data_type": "b"},
        {"coordinate": "C1", "state": "stored_value", "data_type": "s"},
        {"coordinate": "D1", "state": "stored_error", "data_type": "e"},
        {"coordinate": "E1", "state": "missing_or_empty", "data_type": "n"},
        {"coordinate": "F1", "state": "missing_or_empty", "data_type": "n"},
    )
    assert sheets[0]["formula_cells"] == len(sheets[0]["formula_cache"])
    assert "cached content" not in json.dumps(result)
    assert "#DIV/0!" not in json.dumps(result)
    assert inventory_workbook(path) == result
    assert path.read_bytes() == before


def test_workbook_without_formulas_has_empty_cache_inventory(tmp_path: Path) -> None:
    path = tmp_path / "literal.xlsx"
    workbook = Workbook()
    workbook.save(path)
    workbook.close()
    result = inventory_workbook(path)
    sheets = result["sheets"]
    assert isinstance(sheets, list)
    assert sheets[0]["formula_cache"] == ()
