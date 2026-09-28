"""Contract tests for the source-faithful Pharmac canonical projection."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_pharmac import fixture_source

from archive_govt_nz.domains.health_appropriations import pharmac
from archive_govt_nz.domains.health_appropriations.pharmac_canonical_projection import (
    project_pharmac_cpb,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def package(tmp_path: Path) -> tuple[Path, Path, str, str]:
    source, source_sha256 = fixture_source(tmp_path)
    cas = tmp_path / "cas"
    object_path = cas / source_sha256[:2] / source_sha256
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(source.read_bytes())
    silver = tmp_path / "silver"
    pharmac.normalize_pharmac_budget(
        object_path,
        silver,
        expected_sha256=source_sha256,
        source_locator=(
            "https://www.pharmac.govt.nz/medicine-funding-and-supply/"
            "the-funding-process/setting-and-managing-the-combined-"
            "pharmaceutical-budget-cpb/budget-bid-information"
        ),
        source_vintage="Pharmac-CPB-2026-08-07",
        observed_at="2026-08-29T09:00:00Z",
        dry_run=False,
    )
    pin = hashlib.sha256((silver / "MANIFEST.json").read_bytes()).hexdigest()
    return silver, cas, pin, source_sha256


def test_projection_preserves_pharmac_allocation_and_caveats(tmp_path: Path) -> None:
    silver, cas, pin, source_sha256 = package(tmp_path)
    original = {path.name: path.read_bytes() for path in silver.iterdir()}

    facts, lineage, receipt = project_pharmac_cpb(silver, pin, cas, source_sha256)

    assert facts.schema.equals(
        recordset_schema("pharmaceutical_budget_fact"), check_metadata=True
    )
    assert facts.num_rows == 14
    assert lineage.num_rows == 14 * 8
    assert receipt["status"] == "verified_source_faithful_projection"
    assert receipt["source_package_unchanged"] is True
    rows = facts.to_pylist()
    assert {row["amount_type"] for row in rows} == {"published_budget_allocation"}
    assert {row["measure"] for row in rows} == {"pharmaceutical_budget_allocation"}
    assert {row["rights_state"] for row in rows} == {"not_evaluated"}
    assert {row["currency"] for row in rows} == {"NZD"}
    assert {row["price_basis"] for row in rows} == {None}
    assert {row["source_decimal_precision"] for row in rows} == {20}
    assert {row["source_decimal_scale"] for row in rows} == {3}
    post_cutover = next(
        row
        for row in rows
        if row["period_token"] == "2022/23"  # noqa: S105
    )
    pre_cutover = next(
        row
        for row in rows
        if row["period_token"] == "2021/22"  # noqa: S105
    )
    assert post_cutover["funding_regime"] == (
        "government_appropriation_allocated_to_pharmac"
    )
    assert pre_cutover["funding_regime"] == "district_health_board_budget_holder"
    assert all(row["quality_flags"] == list(pharmac.FLAGS) for row in rows)
    assert {path.name: path.read_bytes() for path in silver.iterdir()} == original


def test_projection_rejects_wrong_manifest_and_changed_source(tmp_path: Path) -> None:
    silver, cas, pin, source_sha256 = package(tmp_path)
    with pytest.raises(ValueError, match="pharmac_canonical_projection_invalid"):
        project_pharmac_cpb(silver, "0" * 64, cas, source_sha256)
    object_path = cas / source_sha256[:2] / source_sha256
    object_path.write_bytes(object_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        project_pharmac_cpb(silver, pin, cas, source_sha256)


def test_projection_rejects_tampered_silver_product(tmp_path: Path) -> None:
    silver, cas, pin, source_sha256 = package(tmp_path)
    path = silver / "pharmaceutical_budget_facts.parquet"
    table = pq.read_table(path)
    pq.write_table(table.slice(0, 1), path)
    with pytest.raises(ValueError, match="pharmac_canonical_projection_invalid"):
        project_pharmac_cpb(silver, pin, cas, source_sha256)
