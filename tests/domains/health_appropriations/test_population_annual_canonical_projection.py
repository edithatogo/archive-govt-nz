"""Canonical population projection preserves context without selecting a denominator."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_population_annual_export import payload

from archive_govt_nz.domains.health_appropriations import (
    population_annual_canonical_projection as projection,
)
from archive_govt_nz.domains.health_appropriations.population_annual_canonical_projection import (
    _canonicalize,
    project_population_annual,
)
from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    normalize_population_annual,
)
from archive_govt_nz.schemas.health_recordset_normalization import validate_table
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def test_canonical_projection_keeps_provisional_null_and_complete_lineage(
    tmp_path: Path,
) -> None:
    source = tmp_path / "population.csv"
    content = payload()
    source.write_bytes(content)
    source_pin = hashlib.sha256(content).hexdigest()
    normalize_population_annual(
        source,
        tmp_path / "silver",
        expected_sha256=source_pin,
        observed_at="2026-09-25T09:37:50Z",
        source_vintage="2026-08-18",
        source_locator="https://infoshare.stats.govt.nz/ExportDirect.aspx",
        dry_run=False,
    )

    source_facts = pq.read_table(tmp_path / "silver" / "population_facts.parquet")
    facts, lineage = _canonicalize(source_facts)

    assert facts.schema.equals(
        recordset_schema("price_population_fact"), check_metadata=True
    )
    assert lineage.schema.equals(recordset_schema("field_lineage"), check_metadata=True)
    validate_table("price_population_fact", facts)
    validate_table("field_lineage", lineage)
    rows = facts.to_pylist()
    assert len(rows) == 36
    assert rows[0]["amount"] is None
    assert rows[0]["null_reason"] == "figure_not_available"
    assert rows[-2]["quality_flags"]
    assert "context_only_not_selected_as_denominator" in rows[-1]["quality_flags"]
    assert all(row["rights_state"] == "not_evaluated" for row in rows)
    assert len(lineage) == 108
    assert all(row["record_id"].startswith("sha256:") for row in lineage.to_pylist())
    assert {row["field"] for row in lineage.to_pylist()} == {
        "period_token",
        "amount",
        "source_label",
    }


def test_bronze_bound_projector_rebuilds_and_rejects_tampered_silver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "population.csv"
    content = payload()
    source.write_bytes(content)
    source_pin = hashlib.sha256(content).hexdigest()
    normalize_population_annual(
        source,
        tmp_path / "silver",
        expected_sha256=source_pin,
        observed_at="2026-09-25T09:37:50Z",
        source_vintage="2026-08-18",
        source_locator="https://infoshare.stats.govt.nz/ExportDirect.aspx",
        dry_run=False,
    )
    manifest_bytes = (tmp_path / "silver" / "MANIFEST.json").read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    monkeypatch.setattr(projection, "SOURCE_SHA256", source_pin)
    monkeypatch.setattr(projection, "SOURCE_MANIFEST_SHA256", manifest_sha)
    cas_root = tmp_path / "cas"
    bronze_object = cas_root / source_pin[:2] / source_pin
    bronze_object.parent.mkdir(parents=True)
    bronze_object.write_bytes(content)

    facts, lineage, receipt = project_population_annual(
        tmp_path / "silver", manifest_sha, cas_root
    )

    assert facts.num_rows == 36
    assert lineage.num_rows == 108
    assert receipt["source_object_sha256"] == source_pin
    assert receipt["analytical_selection"] == "not_selected"
    with (tmp_path / "silver" / "population_facts.parquet").open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(
        ValueError, match="population_annual_canonical_projection_invalid"
    ):
        project_population_annual(tmp_path / "silver", manifest_sha, cas_root)
