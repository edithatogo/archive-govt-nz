"""The reviewed context-source adapters compose deterministically."""

from __future__ import annotations

import hashlib

import pytest
from tests.domains.health_appropriations.test_budget_revenue_adapter import (
    _revenue_workbook,
)

from archive_govt_nz.domains.health_appropriations import budget_revenue
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)


def test_context_registration_set_is_stable_and_profile_scoped() -> None:
    registrations = context_adapter_registrations(
        cpi=AdapterContext(
            "https://example.test/cpi", "2026-Q2", "2026-09-01T00:00:00Z"
        ),
        population=AdapterContext(
            "https://example.test/population", "2026-08-18", "2026-09-01T00:00:00Z"
        ),
        qes=AdapterContext(
            "https://example.test/qes", "QES-2026-Q2", "2026-09-01T00:00:00Z"
        ),
        gdp=AdapterContext(
            "https://example.test/gdp", "StatsNZ-GDP-2026Q1", "2026-09-01T00:00:00Z"
        ),
    )
    assert tuple(row.adapter_id for row in registrations) == tuple(
        sorted(row.adapter_id for row in registrations)
    )
    assert {row.adapter_id for row in registrations} == {
        "stats-nz-cpiq-se9a",
        "stats-nz-dpe056aa-annual-mean",
        "stats-nz-gdp-table1-expenditure-actual",
        "stats-nz-qes-qemq-sasz9a",
    }


def test_optional_pharmac_context_adds_only_its_reviewed_profile() -> None:
    contexts = {
        "cpi": AdapterContext("cpi", "2026-Q2", "now"),
        "population": AdapterContext("population", "2026-08-18", "now"),
        "qes": AdapterContext("qes", "QES-2026-Q2", "now"),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026Q1", "now"),
    }
    base = context_adapter_registrations(**contexts)
    extended = context_adapter_registrations(
        **contexts,
        pharmac=AdapterContext("pharmac", "Pharmac-CPB-2026-08-07", "now"),
    )
    assert len(extended) == len(base) + 1
    assert "pharmac-combined-pharmaceutical-budget" in {
        row.adapter_id for row in extended
    }


@pytest.mark.parametrize(
    ("vintage", "definitions", "year"),
    [
        ("Budget-2025", budget_revenue.DEFINITIONS, 2021),
        ("Budget-2026", budget_revenue.DEFINITIONS_2026, 2022),
    ],
)
def test_optional_budget_revenue_context_dispatches_exact_edition(
    vintage: str,
    definitions: dict[str, str],
    year: int,
) -> None:
    contexts = {
        "cpi": AdapterContext("cpi", "2026-Q2", "2026-09-01T00:00:00Z"),
        "population": AdapterContext(
            "population", "2026-08-18", "2026-09-01T00:00:00Z"
        ),
        "qes": AdapterContext("qes", "QES-2026-Q2", "2026-09-01T00:00:00Z"),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026Q1", "2026-09-01T00:00:00Z"),
    }
    registrations = context_adapter_registrations(
        **contexts,
        budget_revenue=AdapterContext("budget.xlsx", vintage, "2026-09-01T00:00:00Z"),
    )
    payload = _revenue_workbook(definitions=definitions, year=year)

    result = dispatch_bronze(
        payload,
        source_sha256=hashlib.sha256(payload).hexdigest(),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        registrations=registrations,
    )

    assert result.selection.adapter_id == "nz-budget-health-revenue"
    assert result.selection.matched_adapter_ids == ("nz-budget-health-revenue",)
    assert result.output.records[0]["source_vintage"] == vintage
    assert result.output.records[0]["year"] == year


def test_composed_registrations_select_one_exact_csv_profile() -> None:
    registrations = context_adapter_registrations(
        cpi=AdapterContext(
            "https://example.test/cpi", "2026-Q2", "2026-09-01T00:00:00Z"
        ),
        population=AdapterContext(
            "https://example.test/population", "2026-08-18", "2026-09-01T00:00:00Z"
        ),
        qes=AdapterContext(
            "https://example.test/qes", "QES-2026-Q2", "2026-09-01T00:00:00Z"
        ),
        gdp=AdapterContext(
            "https://example.test/gdp", "StatsNZ-GDP-2026Q1", "2026-09-01T00:00:00Z"
        ),
    )
    payload = (
        b"Series_reference,Period,Data_value,STATUS,UNITS,Subject,Group,Series_title_1,Series_title_2\n"
        b"CPIQ.SE9A,2026.06,123.4,FINAL,Index,CPI,CPI All Groups for New Zealand,All groups,NA\n"
    )

    result = dispatch_bronze(
        payload,
        source_sha256=hashlib.sha256(payload).hexdigest(),
        media_type="text/csv",
        registrations=registrations,
    )
    assert result.selection.adapter_id == "stats-nz-cpiq-se9a"
    assert result.selection.considered_adapter_ids == (
        "stats-nz-cpiq-se9a",
        "stats-nz-dpe056aa-annual-mean",
    )
