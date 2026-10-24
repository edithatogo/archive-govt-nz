"""Exact names of the four required common-registry fixture contexts."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_registry import (
        AdapterContext,
    )


class RequiredContexts(TypedDict):
    """Known fixture keys; optional registry arguments are supplied explicitly."""

    cpi: AdapterContext
    population: AdapterContext
    qes: AdapterContext
    gdp: AdapterContext
