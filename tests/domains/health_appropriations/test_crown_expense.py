"""The BEFU Crown cache profile preserves formulas, caches and uncertainty."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import defusedxml.ElementTree as DefusedET
import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import (
    crown_expense,
    crown_expense_canonical_projection,
)

_YEARS = tuple(range(2021, 2031))
_COLUMNS = tuple("FGHIJKLMNO")
_VALUES = (100, 110, 120, 130, 140, 150, 160, 170, 180, 190)
_NOTE_1 = (
    "The classifications of the functions of the Government reflect current approved baselines. "
    "Forecast new operating spending is shown as a separate line item in the above analysis and "
    "will be allocated to"
)
_NOTE_2 = "functions of the Government once decisions are made in future Budgets."


def _source(path: Path, *, cached: bool = True) -> str:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = crown_expense.SHEET
    sheet["D6"] = "($millions)"
    sheet["D26"] = "Core Crown expenses"
    sheet["D29"] = _NOTE_1
    sheet["D30"] = _NOTE_2
    sheet["D31"] = "Outside the reviewed profile"
    for column, year, amount_type in zip(
        _COLUMNS, _YEARS, crown_expense.AMOUNT_TYPES, strict=True
    ):
        sheet[f"{column}5"] = str(year)
        sheet[f"{column}6"] = amount_type
        sheet[f"{column}26"] = f"=SUM({column}8:{column}24)"
    workbook.save(path)
    workbook.close()
    if cached:
        contents = {}
        with ZipFile(path) as archive:
            contents = {name: archive.read(name) for name in archive.namelist()}
        name = "xl/worksheets/sheet1.xml"
        root = DefusedET.fromstring(contents[name])
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for column, value in zip(_COLUMNS, _VALUES, strict=True):
            cell = root.find(f".//m:c[@r='{column}26']", ns)
            assert cell is not None
            value_node = cell.find("m:v", ns)
            assert value_node is not None
            value_node.text = str(value)
        contents[name] = DefusedET.tostring(
            root, encoding="utf-8", xml_declaration=True
        )
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            for filename, content in contents.items():
                archive.writestr(filename, content)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize(
    source: Path, output: Path, digest: str, *, dry_run: bool = False
) -> dict[str, Any]:
    return crown_expense.normalize_befu_core_expense(
        source,
        output,
        expected_sha256=digest,
        source_locator=crown_expense.SOURCE_LOCATOR,
        source_vintage=crown_expense.SOURCE_VINTAGE,
        observed_at="2026-08-29T09:00:17Z",
        dry_run=dry_run,
    )


def test_befu_profile_preserves_formula_cache_and_uncertainty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.xlsx"
    digest = _source(source)
    monkeypatch.setattr(crown_expense, "SOURCE_SHA256", digest)
    before = source.read_bytes()
    receipt = _normalize(source, tmp_path / "silver", digest)
    assert receipt["status"] == "passed"
    assert receipt["counts"]["normalized"] == 10
    assert receipt["selection"]["cache_freshness"] == "unverified"
    assert receipt["selection"]["currency"] == "unverified"
    assert receipt["selection"]["financial_year_basis"] == "unverified"
    facts = pq.read_table(tmp_path / "silver/crown_expense_facts.parquet").to_pylist()
    assert [row["year"] for row in facts] == list(_YEARS)
    assert [row["amount_type"] for row in facts] == list(crown_expense.AMOUNT_TYPES)
    assert [row["amount"] for row in facts] == [
        crown_expense.exact_number(value) for value in _VALUES
    ]
    assert all(row["recordset"] == "fiscal_context_fact" for row in facts)
    assert all(
        "formula_cache_freshness_unverified" in row["quality_flags"] for row in facts
    )
    assert all('"formula": "=SUM(' in row["raw_values_json"] for row in facts)
    lineage = pq.read_table(tmp_path / "silver/field_lineage.parquet").to_pylist()
    assert len(lineage) == 60
    assert {row["field"] for row in lineage} == {
        "measure",
        "unit",
        "year",
        "amount_type",
        "formula",
        "amount_cache",
    }
    dispositions = pq.read_table(
        tmp_path / "silver/cell_dispositions.parquet"
    ).to_pylist()
    assert sum(row["disposition"] == "normalized" for row in dispositions) == 10
    assert any(row["disposition"] == "preserved_only" for row in dispositions)
    assert source.read_bytes() == before


def test_befu_profile_preflight_does_not_create_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.xlsx"
    digest = _source(source)
    monkeypatch.setattr(crown_expense, "SOURCE_SHA256", digest)
    result = _normalize(source, tmp_path / "planned", digest, dry_run=True)
    assert result["status"] == "planned"
    assert result["counts"]["normalized"] == 10
    assert not (tmp_path / "planned").exists()


def test_befu_profile_rejects_absent_cached_formula_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.xlsx"
    digest = _source(source, cached=False)
    monkeypatch.setattr(crown_expense, "SOURCE_SHA256", digest)
    with pytest.raises(ValueError, match="crown_expense_contract"):
        _normalize(source, tmp_path / "silver", digest)
    assert not (tmp_path / "silver").exists()


def test_befu_profile_binds_the_reviewed_vintage_and_locator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.xlsx"
    digest = _source(source)
    monkeypatch.setattr(crown_expense, "SOURCE_SHA256", digest)
    with pytest.raises(ValueError, match="crown_expense_contract"):
        crown_expense.normalize_befu_core_expense(
            source,
            tmp_path / "silver",
            expected_sha256=digest,
            source_locator=crown_expense.SOURCE_LOCATOR,
            source_vintage="HYEFU-2025",
            observed_at="2026-08-29T09:00:17Z",
        )


def _canonical_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, str, bytes]:
    source = tmp_path / "source.xlsx"
    digest = _source(source)
    monkeypatch.setattr(crown_expense, "SOURCE_SHA256", digest)
    monkeypatch.setattr(crown_expense_canonical_projection, "SOURCE_SHA256", digest)
    original = source.read_bytes()
    cas_root = tmp_path / "cas"
    cas_object = cas_root / digest[:2] / digest
    cas_object.parent.mkdir(parents=True)
    cas_object.write_bytes(original)
    silver = tmp_path / "silver"
    _normalize(cas_object, silver, digest)
    manifest_sha256 = hashlib.sha256(
        (silver / "MANIFEST.json").read_bytes()
    ).hexdigest()
    monkeypatch.setattr(
        crown_expense_canonical_projection,
        "SOURCE_MANIFEST_SHA256",
        manifest_sha256,
    )
    return cas_root, silver, manifest_sha256, original


def test_canonical_projection_preserves_be_fiscal_context_uncertainty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cas_root, silver, pin, original = _canonical_package(tmp_path, monkeypatch)
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in silver.iterdir()
    }
    facts, lineage, receipt = (
        crown_expense_canonical_projection.project_befu_core_expense(
            silver, pin, cas_root
        )
    )

    rows = facts.to_pylist()
    assert len(rows) == 10
    assert [row["amount_type"] for row in rows] == ["actual"] * 5 + ["forecast"] * 5
    assert [row["period_token"] for row in rows] == [
        f"year_label:{year}" for year in _YEARS
    ]
    assert [row["value_token"] for row in rows] == [str(value) for value in _VALUES]
    assert [row["amount"] for row in rows] == [Decimal(value) for value in _VALUES]
    assert all(row["recordset"] == "fiscal_context_fact" for row in rows)
    assert all(row["valid_time_start"] is None for row in rows)
    assert all(row["valid_time_end"] is None for row in rows)
    assert all(
        row["currency"] is None and row["accounting_basis"] is None for row in rows
    )
    assert {row["unit"] for row in rows} == {"($millions)"}
    assert all(
        "formula_cache_freshness_unverified" in row["quality_flags"] for row in rows
    )
    assert len(lineage) == 80
    assert {row["target_record_id"] for row in lineage.to_pylist()} == {
        row["record_id"] for row in rows
    }
    assert receipt["status"] == "verified_source_faithful_projection"
    assert receipt["denominator_selection"] == "not_performed"
    assert receipt["formula_cache_freshness"] == "unverified"
    assert (
        hashlib.sha256(original).hexdigest()
        == crown_expense_canonical_projection.SOURCE_SHA256
    )
    assert before == {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in silver.iterdir()
    }


def test_canonical_projection_rejects_changed_silver_product(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cas_root, silver, pin, _ = _canonical_package(tmp_path, monkeypatch)
    path = silver / "crown_expense_facts.parquet"
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="crown_expense_canonical_projection_invalid"):
        crown_expense_canonical_projection.project_befu_core_expense(
            silver, pin, cas_root
        )


def test_canonical_projection_rejects_wrong_manifest_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cas_root, silver, _, _ = _canonical_package(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="crown_expense_canonical_projection_invalid"):
        crown_expense_canonical_projection.project_befu_core_expense(
            silver, "0" * 64, cas_root
        )
