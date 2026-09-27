"""The CPI source profile participates in the Bronze adapter protocol."""

from __future__ import annotations

import hashlib
from decimal import Decimal

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.cpi_adapter import cpi_registration

HEADER = "Series_reference,Period,Data_value,STATUS,UNITS,Subject,Group,Series_title_1,Series_title_2\n"
META = ",FINAL,Index,CPI,CPI All Groups for New Zealand,All groups,NA\n"


def test_dispatch_extracts_exact_series_and_accounts_for_other_rows() -> None:
    bronze = (
        HEADER + "CPIQ.SE9A,2026.06,123.4" + META + "OTHER,2026.06,10" + META
    ).encode()
    digest = hashlib.sha256(bronze).hexdigest()
    registration = cpi_registration(
        source_locator="https://www.stats.govt.nz/cpi.csv",
        source_vintage="2026-Q2",
        observed_at="2026-08-31T00:00:00Z",
    )

    result = dispatch_bronze(
        bronze,
        source_sha256=digest,
        media_type="text/csv",
        registrations=(registration,),
    )

    assert result.selection.adapter_id == "stats-nz-cpiq-se9a"
    assert result.output.layout == "stats-nz-cpi-all-groups/v1"
    assert len(result.output.records) == 1
    assert result.output.records[0]["series_reference"] == "CPIQ.SE9A"
    assert result.output.records[0]["amount"] == Decimal("123.4")
    assert result.output.losses[0].disposition == "unselected"
    assert (
        result.output.lineage[0].source_coordinate
        == "csv:row=2;column=Series_reference"
    )


def test_dispatch_preserves_unrecognized_csv_profile() -> None:
    bronze = b"unexpected,headers\nvalue,1\n"
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="text/csv",
        registrations=(
            cpi_registration(
                source_locator="https://www.stats.govt.nz/cpi.csv",
                source_vintage="2026-Q2",
                observed_at="2026-08-31T00:00:00Z",
            ),
        ),
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == "no_matching_layout"
    assert result.output.records == ()
