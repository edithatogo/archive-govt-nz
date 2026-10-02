"""Repeatability for the complete registered Bronze adapter dispatch path."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from tests.domains.health_appropriations.test_budget_adapter import (
    _workbook as budget_expenditure_workbook,
)
from tests.domains.health_appropriations.test_budget_revenue_adapter import (
    _revenue_workbook as budget_revenue_workbook,
)
from tests.domains.health_appropriations.test_cpi_adapter import HEADER, META
from tests.domains.health_appropriations.test_gdp import workbook as gdp_workbook
from tests.domains.health_appropriations.test_pharmac_adapter import (
    payload as pharmac_payload,
)
from tests.domains.health_appropriations.test_population_annual_export import (
    payload as population_payload,
)
from tests.domains.health_appropriations.test_qes import fixture as qes_workbook
from tests.domains.health_appropriations.test_vote_health_pdf_adapter import (
    _Reader as vote_health_pdf_reader,
)

from archive_govt_nz.domains.health_appropriations import vote_health_pdf_adapter
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)
from archive_govt_nz.domains.health_appropriations.budget_adapter import (
    budget_expenditure_registration,
)
from archive_govt_nz.domains.health_appropriations.gdp import VINTAGE as GDP_VINTAGE


def test_registered_adapters_repeat_selection_and_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All registered adapters repeat from the same immutable Bronze bytes."""
    monkeypatch.setattr(vote_health_pdf_adapter, "PdfReader", vote_health_pdf_reader)
    qes_source = tmp_path / "qes.xlsx"
    qes_workbook(qes_source)
    gdp_source = gdp_workbook(tmp_path / "gdp.xlsx")
    profiles = (
        (
            "budget-expenditure",
            budget_expenditure_workbook(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "nz-budget-health-expenditure",
        ),
        (
            "budget-revenue",
            budget_revenue_workbook(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "nz-budget-health-revenue",
        ),
        (
            "cpi",
            (HEADER + "CPIQ.SE9A,2026.06,123.4" + META).encode(),
            "text/csv",
            "stats-nz-cpiq-se9a",
        ),
        (
            "population",
            population_payload(),
            "text/csv",
            "stats-nz-dpe056aa-annual-mean",
        ),
        (
            "qes",
            qes_source.read_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "stats-nz-qes-qemq-sasz9a",
        ),
        (
            "gdp",
            gdp_source.read_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "stats-nz-gdp-table1-expenditure-actual",
        ),
        (
            "pharmac",
            pharmac_payload(),
            "text/html",
            "pharmac-combined-pharmaceutical-budget",
        ),
        (
            "vote-health-pdf",
            b"%PDF-1.7\nreviewed source fixture",
            "application/pdf",
            "nz-treasury-vote-health-2003-04-tables",
        ),
    )
    registrations = context_adapter_registrations(
        cpi=AdapterContext("cpi.csv", "2026-Q2", "2026-08-31T00:00:00Z"),
        population=AdapterContext(
            "population.csv", "2026-08-18", "2026-08-31T00:00:00Z"
        ),
        qes=AdapterContext("qes.xlsx", "QES-2026-Q2", "2026-08-31T00:00:00Z"),
        gdp=AdapterContext("gdp.xlsx", GDP_VINTAGE, "2026-08-31T00:00:00Z"),
        budget_revenue=AdapterContext(
            "data/raw/b25-health-budget.xlsx",
            "Budget-2025",
            "2026-08-31T00:00:00Z",
        ),
        pharmac=AdapterContext(
            "pharmac.html", "Pharmac-CPB-2026-08-07", "2026-08-31T00:00:00Z"
        ),
        vote_health=AdapterContext(
            "vote-health.pdf",
            "Treasury-Vote-Health-Supplementary-2003-04",
            "2026-08-31T00:00:00Z",
        ),
    )
    budget_context = {
        "source_locator": "data/raw/b25-health-budget.xlsx",
        "source_vintage": "Budget-2025",
        "observed_at": "2026-08-31T00:00:00Z",
    }
    registrations = tuple(
        sorted(
            (
                *registrations,
                budget_expenditure_registration(**budget_context),
            ),
            key=lambda row: row.adapter_id,
        )
    )

    for profile, bronze, media_type, adapter_id in profiles:
        original = bytes(bronze)
        digest = hashlib.sha256(original).hexdigest()
        first = dispatch_bronze(
            original,
            source_sha256=digest,
            media_type=media_type,
            registrations=registrations,
        )
        repeated = dispatch_bronze(
            original,
            source_sha256=digest,
            media_type=media_type,
            registrations=registrations,
        )

        assert first.selection.to_receipt() == repeated.selection.to_receipt(), profile
        assert first.output == repeated.output, profile
        assert original == bronze, profile
        assert first.selection.status == "selected", profile
        assert first.selection.adapter_id == adapter_id, profile
