"""Pinned supplemental definitions and read-only native numeric preflight.

Supplemental metadata is an unretained author observation, not independently
replayable evidence. It never replaces source-native unknowns or selects an
analytical deflator. New vintages require explicit profile review.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Self

from pydantic import model_validator

from archive_govt_nz.domains.health_appropriations import cpi, qes
from archive_govt_nz.domains.health_appropriations.source_context_census import (
    Contract,
    Digest,
    Text,
)

if TYPE_CHECKING:
    from pathlib import Path

_CPI_URL = (
    "https://www.stats.govt.nz/assets/Uploads/Consumers-price-index/"
    "Consumers-price-index-June-2026-quarter/Download-data/"
    "consumers-price-index-june-2026-quarter-index-numbers.csv"
)
_QES_URL = (
    "https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/"
    "Labour-market-statistics-June-2026-quarter/Download-data/"
    "quarterly-employment-survey-june-2026-quarter.xlsx"
)

# These are exact reviewed snapshots, not mutable publisher-wide defaults.
_PROFILES: dict[str, tuple[object, ...]] = {
    "cpi": (
        "CPIQ.SE9A",
        "Stats-NZ-CPI-2026-Q2",
        _CPI_URL,
        "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
        "4dd64eafa66ceb711ab750308387a2eb72b54b44333f4d2dfb3659b1a59d4c32",
        "CPI009AA",
        "2026-07-21T10:45:00",
        "Index",
        "2017Q2",
        1000,
        None,
        "historical_component_change",
        "1914Q2",
        "2026Q2",
        "All groups; New Zealand",
        "quarterly index level",
        (
            "Fresh fruit and vegetables seasonally adjusted through 2006Q2; "
            "seasonally unadjusted from 2006Q3; no uniform whole-series claim."
        ),
    ),
    "qes": (
        "QEMQ.SASZ9A",
        "QES-2026-Q2",
        _QES_URL,
        "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97",
        "446b6fa8e0e2238eccac82207cf83d6dd4091bdaa8ba29b19e308179d9e762b9",
        "QEM003AA",
        "2026-08-05T10:45:00",
        "$",
        None,
        None,
        "Both sexes",
        "not_supplied",
        "2024Q2",
        "2026Q2",
        "Total All Sectors - Total Both Sexes - Ordinary Time Hourly",
        "ordinary-time earnings divided by paid hours",
        (
            "Not supplied for Table 8 / QEMQ.SASZ9A; "
            "other-table adjustment labels are not transferable."
        ),
    ),
}


class PriceWageContext(Contract):
    """Exact definition snapshot; metadata evidence and admission stay distinct."""

    schema_version: Literal["archive-govt-nz.price-wage-context/v1"]
    family: Literal["cpi", "qes"]
    series: Text
    source_vintage: Text
    source_url: Text
    source_sha256: Digest
    source_observed_at: Literal["2026-08-29T09:00:17Z"]
    metadata_response_sha256: Digest
    metadata_observation_date: Literal["2026-09-07"]
    metadata_evidence: Literal["author_observation_unretained"]
    metadata_catalogue_url: Literal["https://infoshare.stats.govt.nz/SearchPage.aspx"]
    metadata_export: Literal["session_bound_POST_not_static_export_URL"]
    table: Text
    publisher_updated_local: Text
    publisher_timezone: Literal["not_supplied"]
    unit_label: Text
    magnitude: Literal["Units"]
    base_period: Text | None
    base_value: int | None
    sex: Text | None
    currency_code: None
    adjustment: Text
    first_period: Text
    last_period: Text
    definition: Text
    measure_basis: Text
    adjustment_detail: Text
    frequency: Literal["quarterly_Mar_Jun_Sep_Dec"]
    period_join: Literal["exact_series_quarter_vintage_no_annual_join"]
    analytical_selection: Literal["not_selected"]
    annual_weighting: Literal["not_selected"]
    rights: Literal["not_evaluated"]

    @model_validator(mode="after")
    def reviewed_profile(self) -> Self:
        """Reject mixed identities, revisions and unsupported semantic upgrades."""
        actual = (
            self.series,
            self.source_vintage,
            self.source_url,
            self.source_sha256,
            self.metadata_response_sha256,
            self.table,
            self.publisher_updated_local,
            self.unit_label,
            self.base_period,
            self.base_value,
            self.sex,
            self.adjustment,
            self.first_period,
            self.last_period,
            self.definition,
            self.measure_basis,
            self.adjustment_detail,
        )
        if actual != _PROFILES[self.family]:
            message = "price_wage_reviewed_profile_mismatch"
            raise ValueError(message)
        return self


def admit_retained(
    source: Path,
    probe_output: Path,
    definition: PriceWageContext,
) -> dict[str, object]:
    """Hash-check and preflight retained bytes with the existing native reader.

    No output, acquisition, rights decision or analytical projection occurs.
    Revalidation also rejects mutated/model-constructed definition instances.
    Native reader errors propagate without creating a successful receipt.
    """
    definition = PriceWageContext.model_validate(definition.model_dump())
    if probe_output.exists() or probe_output.is_symlink():
        message = "price_wage_probe_path_must_be_unused"
        raise ValueError(message)
    adapter = cpi.normalize_cpi if definition.family == "cpi" else qes.normalize_qes
    native = adapter(
        source,
        probe_output,
        expected_sha256=definition.source_sha256,
        observed_at=definition.source_observed_at,
        source_vintage=definition.source_vintage,
        source_locator=definition.source_url,
        dry_run=True,
    )
    return {
        "schema_version": "archive-govt-nz.price-wage-admission/v1",
        "numeric_admission": "preflight_passed",
        "native_receipt": native,
        "supplemental_definition": definition.model_dump(),
        "supplemental_qualification": "not_independently_replayable",
        "promotion": "not_performed",
    }
