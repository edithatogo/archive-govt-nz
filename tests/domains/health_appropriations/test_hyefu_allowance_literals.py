"""Synthetic allowance contract regressions, distinct from retained replay."""

import hashlib
from pathlib import Path

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import (
    hyefu_allowance_literals as subject,
)


@pytest.mark.parametrize(
    "mutation", ["none", "unit", "header", "label", "formula", "blank"]
)
def test_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    book = Workbook()
    sheet = book.create_sheet(subject.SHEET)
    for coordinate, value in subject.ANCHORS.items():
        sheet[coordinate] = value
    for coordinate in subject.SELECTED:
        sheet[coordinate] = 0 if coordinate == "C6" else -2
    changes = {
        "unit": ("B5", "$millions"),
        "header": ("C5", "2025"),
        "label": ("B10", "Annual total"),
        "formula": ("C6", "=1+1"),
        "blank": ("C6", None),
    }
    if mutation in changes:
        coordinate, value = changes[mutation]
        sheet[coordinate] = value
    path = tmp_path / "synthetic.xlsx"
    book.save(path)
    book.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(subject, "SOURCE_SHA256", digest)
    if mutation != "none":
        with pytest.raises(ValueError, match="hyefu_allowance_contract"):
            subject.admit_hyefu_allowances(path)
        return
    result = subject.admit_hyefu_allowances(path)
    records = result["records"]
    assert len(records) == 16
    assert records[0]["amount"] == 0
    assert records[-1]["amount"] == -2
    assert records[0]["unit"] == "$millions (average per annum)"
    assert records[0]["budget_label"] == "Budget 2025"
    assert records[-1]["budget_label"] == "Budget 2028"
    assert records[0]["currency"] is None
    assert records[0]["lineage"]["unit"] == "Table 2.4!B5"
    assert records[0]["raw_context"] == subject.ANCHORS
    assert result == subject.admit_hyefu_allowances(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_missing_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="hyefu_allowance_contract"):
        subject.admit_hyefu_allowances(tmp_path / "absent")
