"""The reviewed context-source adapters compose deterministically."""

from __future__ import annotations

import hashlib

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
