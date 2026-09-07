"""Synthetic regressions for the six explicitly Health-labelled chart cells."""

import hashlib
from pathlib import Path

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import (
    health_chart_residual_literals as subject,
)


@pytest.mark.parametrize("vintage", ["BEFU-2025", "HYEFU-2024"])
@pytest.mark.parametrize("mutation", ["none", "unit", "label", "formula", "blank"])
def test_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, vintage: str, mutation: str
) -> None:
    profile = subject.PROFILES[vintage]
    book = Workbook()
    sheet = book.create_sheet(profile["sheet"])
    for coordinate, value in profile["anchors"].items():
        sheet[coordinate] = value
    for coordinate in profile["selected"]:
        sheet[coordinate] = 0 if coordinate == profile["selected"][0] else -2
    changes = {
        "unit": (profile["unit_cell"], "percent"),
        "label": (profile["label_cell"], "Other"),
        "formula": (profile["selected"][0], "=1+1"),
        "blank": (profile["selected"][0], None),
    }
    if mutation in changes:
        coordinate, value = changes[mutation]
        sheet[coordinate] = value
    path = tmp_path / "synthetic.xlsx"
    book.save(path)
    book.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setitem(profile, "sha256", digest)
    if mutation != "none":
        with pytest.raises(ValueError, match="health_chart_residual_contract"):
            subject.admit_health_chart_residuals(path, vintage)
        return
    result = subject.admit_health_chart_residuals(path, vintage)
    records = result["records"]
    assert len(records) == (1 if vintage == "BEFU-2025" else 5)
    assert records[0]["amount"] == 0
    assert records[0]["currency"] is None
    assert records[0]["raw_context"] == profile["anchors"]
    assert records[0]["period_start"] is None
    assert records[0]["period_end"] is None
    if vintage == "BEFU-2025":
        assert records[0]["period_status"] == "unknown_no_period_on_source_sheet"
        assert records[0]["column_headers"] == []
        assert records[0]["measure"] == "health_net_capital_spending"
    else:
        assert records[0]["measure"] == "health_nz_obegalx_movement_not_spending"
        assert records[0]["column_headers"] == [2025, "Forecast"]
        assert records[-1]["column_headers"] == ["Total", "change"]
        assert records[-1]["amount"] == -2
    assert result == subject.admit_health_chart_residuals(path, vintage)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_missing_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="health_chart_residual_contract"):
        subject.admit_health_chart_residuals(tmp_path / "missing", "BEFU-2025")


def test_unknown_profile(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="health_chart_residual_contract"):
        subject.admit_health_chart_residuals(tmp_path / "missing", "unapproved")
