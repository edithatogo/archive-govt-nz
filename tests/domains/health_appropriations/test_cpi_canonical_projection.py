"""Canonical CPI projection retains source and index qualification limits."""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.domains.health_appropriations import cpi, cpi_canonical_projection
from archive_govt_nz.schemas.health_recordset_normalization import validate_table
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

_HEADER = (
    "Series_reference,Period,Data_value,STATUS,UNITS,Subject,Group,"
    "Series_title_1,Series_title_2\n"
)
_META = ",FINAL,Index,CPI,CPI All Groups for New Zealand,All groups,NA\n"


def _build(tmp_path: Path, monkeypatch: MonkeyPatch) -> tuple[Path, Path, str, str]:
    source = tmp_path / "source.csv"
    source.write_text(
        _HEADER + "CPIQ.SE9A,2026.03,123.4500" + _META + "CPIQ.SE9A,2026.06,NA" + _META,
        encoding="utf-8",
    )
    source_pin = hashlib.sha256(source.read_bytes()).hexdigest()
    cas = tmp_path / "cas" / "sha256"
    original = cas / source_pin[:2] / source_pin
    original.parent.mkdir(parents=True)
    original.write_bytes(source.read_bytes())
    silver = tmp_path / "silver"
    locator = "https://example.test/cpi.csv"
    vintage = "synthetic-cpi-v1"
    observed_at = "2026-08-29T09:00:17Z"
    cpi.normalize_cpi(
        source,
        silver,
        expected_sha256=source_pin,
        source_locator=locator,
        source_vintage=vintage,
        observed_at=observed_at,
        dry_run=False,
    )
    manifest_pin = hashlib.sha256((silver / "MANIFEST.json").read_bytes()).hexdigest()
    monkeypatch_values = {
        "SOURCE_SHA256": source_pin,
        "SOURCE_LOCATOR": locator,
        "SOURCE_VINTAGE": vintage,
        "OBSERVED_AT": observed_at,
        "SOURCE_MANIFEST_SHA256": manifest_pin,
    }
    for key, value in monkeypatch_values.items():
        monkeypatch.setattr(cpi_canonical_projection, key, value)
    return silver, cas, manifest_pin, source_pin


def test_projection_preserves_cpi_values_nulls_and_unverified_base(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    silver, cas, manifest_pin, source_pin = _build(tmp_path, monkeypatch)
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in silver.iterdir()
    }
    facts, lineage, receipt = cpi_canonical_projection.project_cpi(
        silver, manifest_pin, cas
    )

    assert facts.schema.equals(
        recordset_schema("price_population_fact"), check_metadata=True
    )
    assert lineage.schema.equals(recordset_schema("field_lineage"), check_metadata=True)
    validate_table("price_population_fact", facts)
    validate_table("field_lineage", lineage)
    rows = facts.to_pylist()
    lineage_row = lineage.to_pylist()[0]
    assert lineage_row["record_id"].startswith("sha256:")
    assert lineage_row["recordset"] == "field_lineage"
    assert lineage_row["source_object_sha256"] == source_pin
    assert lineage_row["target_record_id"] == rows[0]["record_id"]
    assert rows[0]["amount"] == Decimal("123.4500")
    assert rows[0]["source_decimal_scale"] == 4
    assert rows[0]["valid_time_start"] == date(2026, 1, 1)
    assert rows[0]["valid_time_end"] == date(2026, 3, 31)
    assert rows[0]["base_period"] is None
    assert rows[0]["rights_state"] == "not_evaluated"
    assert rows[0]["amount_type"] == "price_index"
    assert rows[1]["amount"] is None
    assert rows[1]["null_reason"] == "missing_unknown_reason"
    assert lineage.num_rows == 14
    assert receipt["source_object_sha256"] == source_pin
    assert receipt["index_base"] == "unverified"
    assert {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in silver.iterdir()
    } == before


def test_projection_rejects_tampered_silver_product(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    silver, cas, manifest_pin, _source_pin = _build(tmp_path, monkeypatch)
    with (silver / "cpi_facts.parquet").open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="cpi_canonical_projection_invalid"):
        cpi_canonical_projection.project_cpi(silver, manifest_pin, cas)
