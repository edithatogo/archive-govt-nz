"""Hash-pinned Budget 2020 expenditure through the shared literal source parser."""

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

PROFILE = "budget-expenditure-2020/v1"
TRANSFORMATION = "budget-2020-health-expenditure/v1"
VINTAGE = "Budget-2020"
SOURCE_SHA256 = "d6a4f00122a05a86bf905f2c43f53cc065b8f033ee080647cf8033961c43aced"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2020-05/b20-expenditure-data.xlsx"
)
MAX_BYTES = shared.MAX_BYTES
MAX_ROWS = 6303
PERIOD_TYPES = {
    2016: "Actuals",
    2017: "Actuals",
    2018: "Actuals",
    2019: "Actuals",
    2020: "Estimated Actual",
    2021: "Main Estimates",
}
DEFINITION_COORDINATES = (
    ("periodicity", "B37"),
    ("unit", "B38"),
    ("valid_time_end", "B39"),
    ("amount_type", "B40"),
    ("app_id", "B47"),
    ("parent_id", "B48"),
    ("group_type", "B49"),
    ("functional_classification", "B50"),
)
DEFINITIONS = {
    **{
        coordinate: shared.DEFINITIONS[old_coordinate]
        for (_, coordinate), (_, old_coordinate) in zip(
            DEFINITION_COORDINATES, shared.DEFINITION_COORDINATES, strict=True
        )
    },
    "B3": (
        "This Expense workbook contains details of actual government "
        "expenditure for the years ended 30 June 2016, 2017, 2018 and 2019; "
        "estimated actual government expenditure for the year ending 30\xa0June "
        "2020 and budgeted government expenditure for the year ending 30 June "
        "2021 as published in Budget 2020."
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
        "nz-budget-2020-health-expenditure",
        DEFINITION_COORDINATES,
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
    """Register only the reviewed 2020 expenditure observation."""
    return shared.profile_registration(
        profile=_configuration(),
        source_locator=source_locator,
        source_vintage=source_vintage,
        observed_at=observed_at,
    )
