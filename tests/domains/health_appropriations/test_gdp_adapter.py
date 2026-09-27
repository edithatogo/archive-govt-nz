"""The retained Stats NZ GDP profile is selectable from Bronze bytes."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_gdp import workbook

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.gdp import VINTAGE
from archive_govt_nz.domains.health_appropriations.gdp_adapter import (
    GdpAdapter,
    gdp_registration,
)


def test_dispatch_emits_quarterly_facts_and_retains_nonselected_cells(
    tmp_path: Path,
) -> None:
    source = workbook(tmp_path / "gdp.xlsx")
    bronze = source.read_bytes()
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(
            gdp_registration(
                source_locator="https://www.stats.govt.nz/gdp.xlsx",
                source_vintage=VINTAGE,
                observed_at="2026-08-29T09:00:17Z",
            ),
        ),
    )

    assert result.selection.adapter_id == "stats-nz-gdp-table1-expenditure-actual"
    assert result.output.layout.endswith("/v1")
    assert len(result.output.records) == 60
    assert len(result.output.lineage) > len(result.output.records)
    assert result.output.losses
    assert all(row["currency"] is None for row in result.output.records)


def test_gdp_registration_rejects_other_vintage(tmp_path: Path) -> None:
    source = workbook(tmp_path / "gdp.xlsx")
    bronze = source.read_bytes()
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(
            gdp_registration(
                source_locator="https://www.stats.govt.nz/gdp.xlsx",
                source_vintage="2026-Q2-other",
                observed_at="2026-08-29T09:00:17Z",
            ),
        ),
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == "no_matching_layout"


def test_gdp_adapter_bad_hash_and_invalid_or_wrong_vintage(tmp_path: Path) -> None:
    source = workbook(tmp_path / "gdp.xlsx")
    bronze = source.read_bytes()
    adapter = GdpAdapter("source", VINTAGE, "2026-08-29T09:00:17Z")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        adapter.extract(bronze, source_sha256="0" * 64)
    assert not adapter.matches_layout(b"not xlsx")
    assert not GdpAdapter("source", "wrong", "now").matches_layout(bronze)
    output = adapter.extract(
        b"invalid", source_sha256=hashlib.sha256(b"invalid").hexdigest()
    )
    assert output.losses[0].reason == "unsupported_gdp_workbook_layout"
