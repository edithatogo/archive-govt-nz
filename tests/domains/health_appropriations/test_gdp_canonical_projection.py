"""Source-pinned GDP canonicalization tests without analytical admission."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_gdp import workbook

from archive_govt_nz.domains.health_appropriations import gdp
from archive_govt_nz.domains.health_appropriations import (
    gdp_canonical_projection as projection,
)
from archive_govt_nz.domains.health_appropriations.gdp import normalize_gdp
from archive_govt_nz.schemas.health_recordset_normalization import validate_table
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def test_pinned_gdp_projection_validates_lineage_and_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = workbook(tmp_path / "source.xlsx")
    source_pin = hashlib.sha256(source.read_bytes()).hexdigest()
    normalize_gdp(
        source,
        tmp_path / "silver",
        expected_sha256=source_pin,
        source_locator="https://example.invalid/gdp.xlsx",
        source_vintage=projection.SOURCE_VINTAGE,
        observed_at=projection.OBSERVED_AT,
        dry_run=False,
    )
    manifest_bytes = (tmp_path / "silver" / "MANIFEST.json").read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    monkeypatch.setattr(projection, "SOURCE_SHA256", source_pin)
    monkeypatch.setattr(projection, "SOURCE_MANIFEST_SHA256", manifest_sha)
    monkeypatch.setattr(
        projection, "SOURCE_LOCATOR", "https://example.invalid/gdp.xlsx"
    )
    cas_root = tmp_path / "cas"
    bronze = cas_root / source_pin[:2] / source_pin
    bronze.parent.mkdir(parents=True)
    bronze.write_bytes(source.read_bytes())

    facts, lineage, receipt = projection.project_gdp(
        tmp_path / "silver", manifest_sha, cas_root
    )

    assert facts.schema.equals(
        recordset_schema("fiscal_context_fact"), check_metadata=True
    )
    assert lineage.schema.equals(recordset_schema("field_lineage"), check_metadata=True)
    validate_table("fiscal_context_fact", facts)
    validate_table("field_lineage", lineage)
    assert facts.num_rows == 60
    assert lineage.num_rows == 420
    assert facts.to_pylist()[0]["valid_time_start"].isoformat() == "2011-04-01"
    assert facts.to_pylist()[0]["currency"] is None
    assert (
        facts.to_pylist()[0]["seasonal_adjustment"]
        == "actual_as_published_not_seasonally_adjusted"
    )
    assert receipt["denominator_selection"] == "not_performed"
    assert all(row["record_id"].startswith("sha256:") for row in lineage.to_pylist())
    with (tmp_path / "silver" / "gdp_facts.parquet").open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="gdp_canonical_projection_invalid"):
        projection.project_gdp(tmp_path / "silver", manifest_sha, cas_root)


def test_june_successor_projects_without_mixing_the_march_vintage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = workbook(tmp_path / "june.xlsx", projection.JUNE_SOURCE_VINTAGE)
    source_pin = hashlib.sha256(source.read_bytes()).hexdigest()
    normalize_gdp(
        source,
        tmp_path / "silver-june",
        expected_sha256=source_pin,
        source_locator="https://example.invalid/gdp-june.xlsx",
        source_vintage=projection.JUNE_SOURCE_VINTAGE,
        observed_at=projection.JUNE_OBSERVED_AT,
        dry_run=False,
    )
    manifest_bytes = (tmp_path / "silver-june" / "MANIFEST.json").read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    monkeypatch.setattr(projection, "JUNE_SOURCE_SHA256", source_pin)
    monkeypatch.setattr(projection, "JUNE_SOURCE_MANIFEST_SHA256", manifest_sha)
    monkeypatch.setattr(
        projection, "JUNE_SOURCE_LOCATOR", "https://example.invalid/gdp-june.xlsx"
    )
    cas_root = tmp_path / "cas"
    bronze = cas_root / source_pin[:2] / source_pin
    bronze.parent.mkdir(parents=True)
    bronze.write_bytes(source.read_bytes())

    facts, lineage, receipt = projection.project_gdp_june(
        tmp_path / "silver-june", manifest_sha, cas_root
    )

    rows = facts.to_pylist()
    assert facts.num_rows == 61
    assert lineage.num_rows == 427
    assert {row["source_vintage"] for row in rows} == {projection.JUNE_SOURCE_VINTAGE}
    assert {row["transformation_id"] for row in rows} == {
        projection.JUNE_TRANSFORMATION
    }
    assert rows[-1]["period_token"] == gdp.PROFILE_PERIODS[gdp.JUNE_VINTAGE][-1][0]
    assert receipt["source_vintage"] == projection.JUNE_SOURCE_VINTAGE
    assert receipt["currency"] == "unresolved"
    assert receipt["denominator_selection"] == "not_performed"
    assert receipt["rights_state"] == "not_evaluated"
