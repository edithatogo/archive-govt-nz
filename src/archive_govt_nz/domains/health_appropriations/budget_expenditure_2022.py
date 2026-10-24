"""Hash-pinned Budget 2022 expenditure through the shared literal source parser."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import (
    budget_expenditure_2024 as shared,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
        AdapterRegistration,
    )

PROFILE = "budget-expenditure-2022/v1"
TRANSFORMATION = "budget-2022-health-expenditure/v1"
VINTAGE = "Budget-2022"
SOURCE_SHA256 = "406f74344833b3f9b91c4c5c22bbbd5dd9484af0d25ab3be054367fd07026338"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2022-05/b22-expenditure-data.xlsx"
)
MAX_BYTES = shared.MAX_BYTES
MAX_ROWS = 6568
PERIOD_TYPES = {
    2018: "Actuals",
    2019: "Actuals",
    2020: "Actuals",
    2021: "Actuals",
    2022: "Estimated Actual",
    2023: "Main Estimates",
}
DEFINITIONS = {
    **shared.DEFINITIONS,
    "B3": (
        "This Expense workbook contains details of actual government "
        "expenditure for the years ended 30 June 2018, 2019, 2020 and 2021; "
        "estimated actual government expenditure for the year ending 30\xa0June "
        "2022 and budgeted government expenditure for the year ending 30 June "
        "2023 as published in Budget 2022."
    ),
}


def _configuration() -> shared.ExpenditureProfile:
    return shared.ExpenditureProfile(
        PROFILE,
        TRANSFORMATION,
        VINTAGE,
        SOURCE_SHA256,
        SOURCE_LOCATOR,
        MAX_ROWS,
        PERIOD_TYPES,
        DEFINITIONS,
        "nz-budget-2022-health-expenditure",
    )


def source_binding(vintage: str, locator: str, digest: str) -> bool:
    """Require the exact captured original, locator and edition."""
    return _configuration().matches(vintage, locator, digest)


def normalize(  # noqa: PLR0913 - explicit source observation contract
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_locator: str,
    source_vintage: str,
    observed_at: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write a source-specific derivative without currency or rights inference."""
    return shared.normalize_profile(
        source,
        output_dir,
        profile=_configuration(),
        expected_sha256=expected_sha256,
        source_locator=source_locator,
        source_vintage=source_vintage,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register only the reviewed 2022 expenditure observation."""
    return shared.profile_registration(
        profile=_configuration(),
        source_locator=source_locator,
        source_vintage=source_vintage,
        observed_at=observed_at,
    )
