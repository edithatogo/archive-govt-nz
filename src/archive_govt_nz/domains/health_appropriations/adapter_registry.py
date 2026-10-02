"""Explicit registration set for reviewed health source-operation profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from archive_govt_nz.domains.health_appropriations.budget_revenue_adapter import (
    budget_revenue_registration,
)
from archive_govt_nz.domains.health_appropriations.cpi_adapter import cpi_registration
from archive_govt_nz.domains.health_appropriations.gdp_adapter import gdp_registration
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
    budget_revenue: AdapterContext | None = None,
    pharmac: AdapterContext | None = None,
    vote_health: AdapterContext | None = None,
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
    return tuple(sorted(registrations, key=lambda row: row.adapter_id))
