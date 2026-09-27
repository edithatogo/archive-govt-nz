"""The exact DPE056AA export is available through Bronze dispatch."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from tests.domains.health_appropriations.test_population_annual_export import payload

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.population_annual_adapter import (
    PopulationAnnualAdapter,
    population_annual_registration,
)


def registration() -> AdapterRegistration:
    return population_annual_registration(
        source_locator="https://infoshare.stats.govt.nz/ExportDirect.aspx",
        source_vintage="2026-08-18",
        observed_at="2026-09-25T09:37:50Z",
    )


def test_dispatch_preserves_population_status_and_denominator_boundary() -> None:
    bronze = payload()
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="text/csv",
        registrations=(registration(),),
    )

    assert result.selection.adapter_id == "stats-nz-dpe056aa-annual-mean"
    assert result.output.layout == "stats-nz-population-annual-mean-context/v1"
    assert len(result.output.records) == 36
    assert len(result.output.lineage) == 108
    assert result.output.losses == ()
    missing = next(row for row in result.output.records if row["amount"] is None)
    assert missing["missing_reason"] == "figure_not_available"
    assert missing["denominator_selected"] is False
    assert missing["rights_state"] == "not_evaluated"
    provisional = [row for row in result.output.records if row["status"] == "P"]
    assert len(provisional) == 2
    assert next(row for row in result.output.records if row["amount"] is not None)[
        "amount"
    ] == Decimal(3501992)


def test_population_layout_probe_rejects_unknown_csv() -> None:
    profile = registration()
    assert profile.layout_probe is not None
    assert profile.layout_probe(b"unexpected,headers\nvalue,1\n") is False


def test_population_adapter_hash_vintage_size_and_preserved_layout(
    monkeypatch: MonkeyPatch,
) -> None:
    bronze = payload()
    digest = hashlib.sha256(bronze).hexdigest()
    adapter = PopulationAnnualAdapter("source", "2026-08-18", "now")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        adapter.extract(bronze, source_sha256="0" * 64)
    assert adapter.matches_layout(bronze)
    assert not PopulationAnnualAdapter("source", "wrong", "now").matches_layout(bronze)
    monkeypatch.setattr(
        "archive_govt_nz.domains.health_appropriations.population_annual_export.MAX_BYTES",
        1,
    )
    assert not adapter.matches_layout(bronze)
    output = adapter.extract(bronze, source_sha256=digest)
    assert output.losses[0].reason == "unsupported_population_export_layout"
