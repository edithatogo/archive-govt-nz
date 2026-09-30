"""Exact GDP vintage overlap comparison preserves unresolved interpretation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import (
    gdp,
)
from archive_govt_nz.domains.health_appropriations import (
    gdp_canonical_projection as projection,
)
from archive_govt_nz.domains.health_appropriations import (
    gdp_vintage_comparison as comparison,
)


def rows(vintage: str) -> list[dict[str, Any]]:
    transformation = (
        projection.TRANSFORMATION
        if vintage == projection.SOURCE_VINTAGE
        else projection.JUNE_TRANSFORMATION
    )
    periods = gdp.PROFILE_PERIODS[vintage]
    result = []
    for index, (token, period_end) in enumerate(periods):
        value = Decimal(100 + index)
        result.append(
            {
                "recordset": "fiscal_context_fact",
                "source_vintage": vintage,
                "transformation_id": transformation,
                "measure": "gross_domestic_product_expenditure_actual_current_prices",
                "currency": None,
                "base_period": None,
                "denominator_definition": None,
                "rights_state": "not_evaluated",
                "valid_time_status": "source_quarter_ended",
                "unit": "$(million)",
                "price_basis": "current_prices",
                "amount_type": "economic_aggregate",
                "institutional_coverage": "whole_economy",
                "accounting_basis": "national_accounts_expenditure",
                "seasonal_adjustment": "actual_as_published_not_seasonally_adjusted",
                "period_token": token,
                "amount": value,
                "value_token": str(value),
                "source_label": "Gross domestic product expenditure",
                "valid_time_start": date(period_end.year, period_end.month - 2, 1),
                "valid_time_end": period_end,
            }
        )
    return result


def test_comparison_reports_exact_changed_overlap_without_semantic_promotion() -> None:
    march = rows(projection.SOURCE_VINTAGE)
    june = rows(projection.JUNE_SOURCE_VINTAGE)
    june[0]["amount"] = Decimal(101)
    june[0]["value_token"] = str(june[0]["amount"])

    report = comparison.compare_gdp_vintages(march, june)

    assert report["overlap_count"] == 60
    assert report["unchanged_period_count"] == 59
    assert report["changed_period_count"] == 1
    assert report["changed_period_tokens"] == ["Jun-11"]
    assert report["difference_interpretation"] == "not_assessed"
    assert report["currency"] == "unresolved"
    assert report["rights_state"] == "not_evaluated"
    assert report["denominator_selection"] == "not_performed"
    assert report["analytical_admission"] == "not_performed"


@pytest.mark.parametrize("fault", ["wrong_vintage", "duplicate_period", "currency"])
def test_comparison_rejects_invalid_vintage_contract(fault: str) -> None:
    march = rows(projection.SOURCE_VINTAGE)
    june = rows(projection.JUNE_SOURCE_VINTAGE)
    if fault == "wrong_vintage":
        june[0]["source_vintage"] = projection.SOURCE_VINTAGE
    elif fault == "duplicate_period":
        june[-1]["period_token"] = june[0]["period_token"]
    else:
        june[0]["currency"] = "NZD"

    with pytest.raises(ValueError, match="gdp_vintage_comparison_invalid"):
        comparison.compare_gdp_vintages(march, june)
