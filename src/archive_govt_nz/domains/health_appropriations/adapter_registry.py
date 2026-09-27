"""Explicit registration set for supported CPI, wage, population and GDP inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from archive_govt_nz.domains.health_appropriations.cpi_adapter import cpi_registration
from archive_govt_nz.domains.health_appropriations.gdp_adapter import gdp_registration
from archive_govt_nz.domains.health_appropriations.pharmac_adapter import (
    pharmac_budget_registration,
)
from archive_govt_nz.domains.health_appropriations.population_annual_adapter import (
    population_annual_registration,
)
from archive_govt_nz.domains.health_appropriations.qes_adapter import qes_registration

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


def context_adapter_registrations(
    *,
    cpi: AdapterContext,
    population: AdapterContext,
    qes: AdapterContext,
    gdp: AdapterContext,
    pharmac: AdapterContext | None = None,
) -> tuple[AdapterRegistration, ...]:
    """Return one deterministic, probe-bound registration per context family.

    The registration set enables exact reviewed CPI, population, QES and GDP
    layouts. It performs no acquisition, rights decision or denominator choice.
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
    if pharmac is not None:
        registrations.append(
            pharmac_budget_registration(
                source_locator=pharmac.source_locator,
                source_vintage=pharmac.source_vintage,
                observed_at=pharmac.observed_at,
            )
        )
    return tuple(sorted(registrations, key=lambda row: row.adapter_id))
