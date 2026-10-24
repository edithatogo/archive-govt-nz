"""Hash-pinned Budget 2023 expenditure through the shared literal source parser."""

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

PROFILE = "budget-expenditure-2023/v1"
TRANSFORMATION = "budget-2023-health-expenditure/v1"
VINTAGE = "Budget-2023"
SOURCE_SHA256 = "bee0e4cd776f0511d271ec842ade355661772c804d12239035e32ad61db06da9"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2023-09/b23-expenditure-data.xlsx"
)
MAX_BYTES = shared.MAX_BYTES
MAX_ROWS = 6696
PERIOD_TYPES = {
    2019: "Actuals",
    2020: "Actuals",
    2021: "Actuals",
    2022: "Actuals",
    2023: "Estimated Actual",
    2024: "Main Estimates",
}
DEFINITIONS = {
    **shared.DEFINITIONS,
    "B3": (
        "This Expense workbook contains details of actual government expenditure "
        "for the years ended 30 June 2019, 2020, 2021 and 2022; estimated actual "
        "government expenditure for the year ending 30\u00a0June 2023 and budgeted "
        "government expenditure for the year ending 30 June 2024 as published in "
        "Budget 2023."
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
        "nz-budget-2023-health-expenditure",
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
    """Register only the reviewed 2023 expenditure observation."""
    return shared.profile_registration(
        profile=_configuration(),
        source_locator=source_locator,
        source_vintage=source_vintage,
        observed_at=observed_at,
    )
