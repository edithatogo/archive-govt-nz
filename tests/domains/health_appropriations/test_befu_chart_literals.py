"""Synthetic tests for chart-table literal admission, not source replay."""

import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import befu_chart_literals as subject
from archive_govt_nz.domains.health_appropriations.befu_chart_literals import (
    _selected_tokens,
)


@pytest.mark.parametrize(
    "mutation", ["none", "formula", "blank", "unit", "label", "total"]
)
def test_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    book = Workbook()
    for title, profile in subject.PROFILES.items():
        sheet = book.create_sheet(title)
        for key, value in profile["anchors"].items():
            sheet[key] = value
        for coordinate in profile["selected"]:
            sheet[coordinate] = -2
            sheet[f"B{sheet[coordinate].row}"] = "Synthetic label"
        for coordinate in profile["excluded"]:
            sheet[coordinate] = "=1+1"
    sheet = book["Table 2.4"]
    sheet["D7"] = 0
    changes = {
        "formula": ("D7", "=1+1"),
        "blank": ("D7", None),
        "unit": ("B5", "$billions"),
        "label": ("B7", None),
    }
    if mutation in changes:
        coordinate, value = changes[mutation]
        sheet[coordinate] = value
    if mutation == "total":
        book["Table 2.5"]["F7"] = 2
    path = tmp_path / "synthetic.xlsx"
    book.save(path)
    book.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(subject, "SOURCE_SHA256", digest)
    if mutation != "none":
        with pytest.raises(ValueError, match="befu_chart_literal_contract"):
            subject.admit_befu_chart_literals(path)
        return
    result = subject.admit_befu_chart_literals(path)
    assert len(result["records"]) == 86
    assert len(result["excluded_formulas"]) == 15
    assert result["records"][0]["amount"] == 0
    assert result["records"][-1]["amount"] == -2
    assert result["records"][0]["currency"] is None
    assert result["records"][0]["raw_context"]["B4"] == "Year ending 30 June"
    assert result["records"][0]["lineage"]["amount"] == "Table 2.4!D7"
    assert result == subject.admit_befu_chart_literals(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_missing_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="befu_chart_literal_contract"):
        subject.admit_befu_chart_literals(tmp_path / "absent")


@pytest.mark.parametrize(
    "mutation",
    [
        "none",
        "duplicate_rel",
        "external",
        "duplicate_cell",
        "duplicate_value",
        "missing_sheet",
        "duplicate_sheet",
    ],
)
def test_selected_xml_contract(mutation: str) -> None:
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    sheets = [
        f'<sheet name="{title}" r:id="r{i}"/>'
        for i, title in enumerate(subject.PROFILES)
    ]
    if mutation == "missing_sheet":
        sheets.pop()
    if mutation == "duplicate_sheet":
        sheets.append(sheets[0])
    mode = ' TargetMode="External"' if mutation == "external" else ""
    relations = [
        f'<Relationship Id="r{i}" Target="worksheets/sheet{i}.xml"{mode}/>'
        for i in range(3)
    ]
    if mutation == "duplicate_rel":
        relations.append(relations[0])
    value = "<v>0</v>" * (2 if mutation == "duplicate_value" else 1)
    cell = f'<c r="A1" t="n">{value}</c>'
    if mutation == "duplicate_cell":
        cell += cell
    payload = BytesIO()
    with ZipFile(payload, "w") as package:
        package.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{ns}" xmlns:r="{rel}">'
            f"<sheets>{''.join(sheets)}</sheets></workbook>",
        )
        package.writestr(
            "xl/_rels/workbook.xml.rels",
            "<Relationships>" + "".join(relations) + "</Relationships>",
        )
        for i in range(3):
            package.writestr(
                f"xl/worksheets/sheet{i}.xml",
                f'<worksheet xmlns="{ns}">'
                f"<sheetData><row>{cell}</row></sheetData></worksheet>",
            )
    if mutation != "none":
        with pytest.raises(ValueError, match="befu_chart_literal_contract"):
            _selected_tokens(payload.getvalue())
        return
    assert _selected_tokens(payload.getvalue()) == {
        title: {"A1": "0"} for title in subject.PROFILES
    }
