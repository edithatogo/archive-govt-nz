"""Explicit registration set for reviewed health source-operation profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from archive_govt_nz.domains.health_appropriations import (
    supplementary_summary_adapter as supplementary_adapters,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_2002_03_adapter as estimates_2002_03_adapter,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_2016_17_adapter as estimates_2016_17_adapter,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as overview_adapters,
)
from archive_govt_nz.domains.health_appropriations.budget_adapter import (
    budget_expenditure_registration,
)
from archive_govt_nz.domains.health_appropriations.budget_revenue_adapter import (
    budget_revenue_registration,
)
from archive_govt_nz.domains.health_appropriations.cpi_adapter import cpi_registration
from archive_govt_nz.domains.health_appropriations.donor_sqlite_adapter import (
    donor_sqlite_registration,
)
from archive_govt_nz.domains.health_appropriations.forecast_adapter import (
    forecast_health_registration,
)
from archive_govt_nz.domains.health_appropriations.gdp_adapter import gdp_registration
from archive_govt_nz.domains.health_appropriations.historical_source_adapter import (
    historical_source_registration,
)
from archive_govt_nz.domains.health_appropriations.literal_source_adapter import (
    literal_source_registration,
)
from archive_govt_nz.domains.health_appropriations.pharmac_adapter import (
    pharmac_budget_registration,
)
from archive_govt_nz.domains.health_appropriations.population_annual_adapter import (
    population_annual_registration,
)
from archive_govt_nz.domains.health_appropriations.qes_adapter import qes_registration
from archive_govt_nz.domains.health_appropriations.vote_health_pdf_adapter import (
    vote_health_pdf_registration,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
        AdapterRegistration,
        CompoundAdapterRegistration,
    )
    from archive_govt_nz.domains.health_appropriations.donor_sqlite_adapter import (
        DonorSQLiteContext,
    )


@dataclass(frozen=True, slots=True)
class AdapterContext:
    """Caller-observed locator, vintage and time for one source profile."""

    source_locator: str
    source_vintage: str
    observed_at: str


def context_adapter_registrations(  # noqa: PLR0913 - each family has explicit context.
    *,
    cpi: AdapterContext,
    population: AdapterContext,
    qes: AdapterContext,
    gdp: AdapterContext,
    budget_expenditure: AdapterContext | None = None,
    budget_revenue: AdapterContext | None = None,
    pharmac: AdapterContext | None = None,
    befu_2026: AdapterContext | None = None,
    hyefu_2025: AdapterContext | None = None,
    vote_health: AdapterContext | None = None,
    vote_health_estimates_2002_03: AdapterContext | None = None,
    vote_health_estimates_2016_17: AdapterContext | None = None,
    vote_health_estimates_overviews: tuple[AdapterContext, ...] = (),
    vote_health_supplementary_summaries: tuple[AdapterContext, ...] = (),
    donor_sqlite: DonorSQLiteContext | None = None,
    literal_workbooks: tuple[AdapterContext, ...] = (),
    historical_workbook: AdapterContext | None = None,
) -> tuple[AdapterRegistration, ...]:
    """Return deterministic, probe-bound registrations for supplied families.

    Only exact reviewed layouts are registered. This performs no acquisition,
    rights decision, period alignment, or denominator choice.
    """
    registrations = [
        cpi_registration(
            source_locator=cpi.source_locator,
            source_vintage=cpi.source_vintage,
            observed_at=cpi.observed_at,
        ),
        population_annual_registration(
            source_locator=population.source_locator,
            source_vintage=population.source_vintage,
            observed_at=population.observed_at,
        ),
        qes_registration(
            source_locator=qes.source_locator,
            source_vintage=qes.source_vintage,
            observed_at=qes.observed_at,
        ),
        gdp_registration(
            source_locator=gdp.source_locator,
            source_vintage=gdp.source_vintage,
            observed_at=gdp.observed_at,
        ),
    ]
    registrations.extend(
        () if donor_sqlite is None else (donor_sqlite_registration(donor_sqlite),)
    )
    registrations.extend(
        literal_source_registration(
            source_locator=context.source_locator,
            source_vintage=context.source_vintage,
            observed_at=context.observed_at,
        )
        for context in literal_workbooks
    )
    if budget_expenditure is not None:
        registrations.append(
            budget_expenditure_registration(
                source_locator=budget_expenditure.source_locator,
                source_vintage=budget_expenditure.source_vintage,
                observed_at=budget_expenditure.observed_at,
            )
        )
    if budget_revenue is not None:
        registrations.append(
            budget_revenue_registration(
                source_locator=budget_revenue.source_locator,
                source_vintage=budget_revenue.source_vintage,
                observed_at=budget_revenue.observed_at,
            )
        )
    if pharmac is not None:
        registrations.append(
            pharmac_budget_registration(
                source_locator=pharmac.source_locator,
                source_vintage=pharmac.source_vintage,
                observed_at=pharmac.observed_at,
            )
        )
    if vote_health is not None:
        registrations.append(
            vote_health_pdf_registration(
                source_locator=vote_health.source_locator,
                source_vintage=vote_health.source_vintage,
                observed_at=vote_health.observed_at,
            )
        )
    if vote_health_estimates_2002_03 is not None:
        registrations.append(
            estimates_2002_03_adapter.vote_health_estimates_2002_03_registration(
                source_locator=vote_health_estimates_2002_03.source_locator,
                source_vintage=vote_health_estimates_2002_03.source_vintage,
                observed_at=vote_health_estimates_2002_03.observed_at,
            )
        )
    if vote_health_estimates_2016_17 is not None:
        registrations.append(
            estimates_2016_17_adapter.vote_health_estimates_2016_17_registration(
                source_locator=vote_health_estimates_2016_17.source_locator,
                source_vintage=vote_health_estimates_2016_17.source_vintage,
                observed_at=vote_health_estimates_2016_17.observed_at,
            )
        )
    registrations.extend(
        overview_adapters.vote_health_estimates_overview_registration(
            source_locator=context.source_locator,
            source_vintage=context.source_vintage,
            observed_at=context.observed_at,
        )
        for context in vote_health_estimates_overviews
    )
    registrations.extend(
        supplementary_adapters.supplementary_summary_registration(
            source_locator=context.source_locator,
            source_vintage=context.source_vintage,
            observed_at=context.observed_at,
        )
        for context in vote_health_supplementary_summaries
    )
    for profile, context in (
        ("befu-2026/v1", befu_2026),
        ("hyefu-2025/v1", hyefu_2025),
    ):
        if context is not None:
            registrations.append(
                forecast_health_registration(
                    profile=profile,
                    source_locator=context.source_locator,
                    source_vintage=context.source_vintage,
                    observed_at=context.observed_at,
                )
            )
    registrations.extend(
        ()
        if historical_workbook is None
        else (
            historical_source_registration(
                source_locator=historical_workbook.source_locator,
                source_vintage=historical_workbook.source_vintage,
                observed_at=historical_workbook.observed_at,
            ),
        )
    )
    if len({row.adapter_id for row in registrations}) != len(registrations):
        message = "duplicate reviewed adapter identity"
        raise ValueError(message)
    return tuple(sorted(registrations, key=lambda row: row.adapter_id))


def compound_workbook_registrations(
    contexts: tuple[AdapterContext, ...],
) -> tuple[CompoundAdapterRegistration, ...]:
    """Explicit native-only registry; legacy result consumers remain unchanged."""
    from archive_govt_nz.domains.health_appropriations import (  # noqa: PLC0415 - Native-only import.
        forecast_detail_source_adapter as native_adapters,
    )

    registrations = tuple(
        native_adapters.forecast_detail_source_registration(
            source_locator=context.source_locator,
            source_vintage=context.source_vintage,
            observed_at=context.observed_at,
        )
        for context in contexts
    )
    if len({row.adapter_id for row in registrations}) != len(registrations):
        message = "duplicate reviewed adapter identity"
        raise ValueError(message)
    return tuple(sorted(registrations, key=lambda row: row.adapter_id))
