"""Source-hash-bound workbook listings and head previews are read-only."""

import hashlib
import json
import tempfile
from datetime import date, time, timedelta
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator
from openpyxl import Workbook
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

from archive_govt_nz.cli import health_appropriations_inspect_workbook
from archive_govt_nz.domains.health_appropriations import inspection
from archive_govt_nz.domains.health_appropriations.inspection import (
    _display,
    inspect_workbook,
)


def _source(
    root: Path,
    label: str = "Health",
    formula: str | ArrayFormula | DataTableFormula = "=1+1",
) -> tuple[Path, str]:
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.title = "Data"
    sheet.append(["Label", "Amount", "Formula"])
    sheet.append([label, 1.25, formula])
    sheet.append([None, True, "#N/A"])
    book.create_sheet("Other")["A1"] = "second"
    source = root / "original"
    book.save(source)
    book.close()
    return source, hashlib.sha256(source.read_bytes()).hexdigest()


def test_inspection_retains_source_and_formula_text(tmp_path: Path) -> None:
    source, digest = _source(tmp_path)
    result = inspect_workbook(source, digest, rows=2, columns=3)
    assert result["status"] == "inspected"
    assert result["source_sha256"] == digest
    assert [sheet["name"] for sheet in result["previews"]] == ["Data", "Other"]
    data = result["previews"][0]
    assert data["row_truncated"] is True
    assert data["column_truncated"] is False
    assert data["cells"][-1] == {
        "coordinate": "C2",
        "data_type": "f",
        "decoded_value_json": '"=1+1"',
    }
    assert result["value_semantics"] == "decoded_preview_not_canonical_facts"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


def test_selected_sheet_and_bounded_failures(tmp_path: Path) -> None:
    source, digest = _source(tmp_path)
    result = inspect_workbook(source, digest, sheet="Other", rows=1, columns=1)
    assert len(result["previews"]) == 1
    assert result["previews"][0]["name"] == "Other"
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest, sheet="missing")
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, "0" * 64)


@pytest.mark.parametrize(
    ("rows", "columns"), [(-1, 1), (21, 1), (True, 1), (1, 0), (1, 51), (1, False)]
)
def test_preview_limits(tmp_path: Path, rows: int, columns: int) -> None:
    source, digest = _source(tmp_path)
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest, rows=rows, columns=columns)


def test_listing_without_previews(tmp_path: Path) -> None:
    source, digest = _source(tmp_path)
    result = inspect_workbook(source, digest, rows=0)
    assert result["previews"] == []
    assert [row["title"] for row in result["inventory"]["sheets"]] == ["Data", "Other"]


def test_preview_byte_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source, digest = _source(tmp_path)
    monkeypatch.setattr(inspection, "_MAX_PREVIEW_VALUE_BYTES", 1, raising=False)
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest)


def test_exact_aggregate_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = _source(tmp_path, "Māori 🩺")
    result = inspect_workbook(source, digest, rows=20, columns=50)
    cells = [cell for preview in result["previews"] for cell in preview["cells"]]
    encoded_size = sum(
        len(cell["decoded_value_json"].encode("utf-8")) for cell in cells
    )
    monkeypatch.setattr(inspection, "_MAX_PREVIEW_CELLS", len(cells))
    monkeypatch.setattr(inspection, "_MAX_PREVIEW_VALUE_BYTES", encoded_size)
    assert inspect_workbook(source, digest, rows=20, columns=50) == result
    monkeypatch.setattr(inspection, "_MAX_PREVIEW_VALUE_BYTES", encoded_size - 1)
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest)
    monkeypatch.setattr(inspection, "_MAX_PREVIEW_VALUE_BYTES", encoded_size)
    monkeypatch.setattr(inspection, "_MAX_PREVIEW_CELLS", len(cells) - 1)
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest)


def test_source_size_and_bad_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = _source(tmp_path)
    monkeypatch.setattr(inspection, "_MAX_SOURCE_BYTES", source.stat().st_size)
    assert (
        inspect_workbook(source, digest, columns=2)["previews"][0]["column_truncated"]
        is True
    )
    monkeypatch.setattr(inspection, "_MAX_SOURCE_BYTES", source.stat().st_size - 1)
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest)
    source.write_bytes(b"private malformed source")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="workbook_inspection_failed") as error:
        inspect_workbook(source, digest)
    assert "private" not in str(error.value)


def test_inspection_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source, digest = _source(tmp_path)
    assert health_appropriations_inspect_workbook(source, digest, rows=0) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "inspected"
    assert result["previews"] == []
    assert health_appropriations_inspect_workbook(source, "0" * 64) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_inspection_schema(tmp_path: Path) -> None:
    source, digest = _source(tmp_path)
    schema = json.loads(
        Path("schemas/health-workbook-inspection-v1.schema.json").read_bytes()
    )
    result = inspect_workbook(source, digest)
    Draft202012Validator(schema).validate(result)
    result["source_sha256"] = "bad"
    assert list(Draft202012Validator(schema).iter_errors(result))


@settings(max_examples=30, deadline=None)
@given(rows=st.integers(0, 20), columns=st.integers(1, 50))
def test_head_dimensions_preserve_original(rows: int, columns: int) -> None:
    with tempfile.TemporaryDirectory() as directory:
        source, digest = _source(Path(directory))
        result = inspect_workbook(source, digest, rows=rows, columns=columns)
        count = sum(len(preview["cells"]) for preview in result["previews"])
        assert count == (min(rows, 3) * min(columns, 3) + 1 if rows else 0)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


def test_nonfinite_numeric_preview_fails_closed(tmp_path: Path) -> None:
    source, _ = _source(tmp_path)
    patched = BytesIO()
    with ZipFile(source) as original, ZipFile(patched, "w") as target:
        for member in original.infolist():
            payload = original.read(member.filename)
            if member.filename == "xl/worksheets/sheet1.xml":
                payload = payload.replace(b">1.25<", b">1e309<")
            target.writestr(member, payload)
    source.write_bytes(patched.getvalue())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="workbook_inspection_failed"):
        inspect_workbook(source, digest)
    assert inspect_workbook(source, digest, rows=0)["previews"] == []


@pytest.mark.parametrize(
    "formula",
    [ArrayFormula("C2:C3", "=SUM(B2:B3)"), DataTableFormula("C2:C3", r1="B2")],
)
def test_structured_formula_preview(
    tmp_path: Path, formula: ArrayFormula | DataTableFormula
) -> None:
    source, digest = _source(tmp_path, formula=formula)
    result = inspect_workbook(source, digest, sheet="Data", rows=2, columns=3)
    value = json.loads(result["previews"][0]["cells"][-1]["decoded_value_json"])
    assert value["attributes"] == dict(formula)
    if isinstance(formula, ArrayFormula):
        assert value["text"] == "=SUM(B2:B3)"


@pytest.mark.parametrize("value", [date(2026, 8, 30), time(12, 30), timedelta(hours=2)])
def test_temporal_display(value: date | time | timedelta) -> None:
    assert _display(value) == str(value)


def test_unknown_display_is_not_object_repr() -> None:
    with pytest.raises(TypeError, match="unsupported_preview_value"):
        _display(object())
