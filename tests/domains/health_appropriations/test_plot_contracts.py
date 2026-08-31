"""Pure plot semantics preserve exact numbers, gaps, source partitions and labels."""

import copy
import json
from decimal import Decimal
from typing import Any

from archive_govt_nz.domains.health_appropriations.plot_contracts import (
    build_plot_contracts,
)


def historical(year: int, **context: object) -> dict[str, Any]:
    return {
        "record_id": f"health-{year}",
        "year": year,
        "exact_amount": Decimal("605.70000000000005000"),
        "source_context_json": json.dumps(
            {
                "source_object_sha256": "a" * 64,
                "source_vintage": "2024",
                "accounting_basis": "Cash",
                "period_end_month": 6,
                **context,
            }
        ),
        "yoy_percent": "0.000000000000",
        "yoy_status": "comparable",
        "yoy_input_ids": [f"health-{year - 1}", f"health-{year}"],
        "gdp_share_percent": "7.142227925614",
        "gdp_share_status": "aligned",
        "gdp_input_ids": [f"health-{year}", f"gdp-{year}"],
    }


def budget(year: int, **extra: object) -> dict[str, Any]:
    return {
        "year": year,
        "source_object_sha256": "b" * 64,
        "source_vintage": "Budget 2025",
        "functional_classification": "Health",
        "amount_type": "Estimated Actual",
        "total_amount_thousands": Decimal("-12.345"),
        "input_record_ids": [f"budget-{year}"],
        **extra,
    }


def tables() -> dict[str, list[dict[str, Any]]]:
    return {
        "historical_nominal.parquet": [historical(2024)],
        "historical_yoy.parquet": [historical(2024)],
        "health_spending_gdp_share.parquet": [historical(2024)],
        "recent_classification_trends.parquet": [budget(2025)],
        "recent_functional_breakdown.parquet": [budget(2025)],
    }


def test_six_contracts_exact_values_and_no_mutation() -> None:
    source = tables()
    before = copy.deepcopy(source)
    result = build_plot_contracts(source)
    assert source == before
    assert len(result) == 6
    nominal = result["historical_health_spending_nominal.png"]
    assert nominal["input"] == "historical_nominal.parquet"
    assert nominal["ylabel"] == "Health spending (NZD millions, nominal)"
    assert nominal["series"][0]["points"][0] == {
        "x": 2024,
        "y": "605.70000000000005000",
        "input_record_ids": ["health-2024"],
    }
    growth = result["historical_health_spending_yoy_growth.png"]
    assert growth["kind"] == "bar"
    assert growth["series"][0]["points"][0]["y"] == "0.000000000000"
    share = result["health_spending_vs_gdp.png"]
    assert share["series"][0]["points"][0]["input_record_ids"] == [
        "gdp-2024",
        "health-2024",
    ]
    breakdown = result[
        "recent_appropriations_functional_breakdown_2025_Estimated_Actual.png"
    ]
    assert breakdown["kind"] == "barh"
    assert breakdown["series"][0]["points"][0]["y"] == "-12.345"
    assert breakdown["series"][0]["points"][0]["x"] == "Health"
    assert breakdown["filters"] == {"year": 2025, "amount_type": "Estimated Actual"}
    assert result["recent_trends_no_classification.png"]["series"] == []
    assert all(
        plot["rendering"]["numeric_conversion"] == "float_for_display_only"
        for plot in result.values()
    )
    json.dumps(result, allow_nan=False)
    nominal["series"][0]["points"][0]["input_record_ids"].append("changed")
    assert source == before


def test_nulls_are_omitted_and_reason_coded_not_zero_filled() -> None:
    source = tables()
    source["historical_yoy.parquet"][0].update(
        yoy_percent=None, yoy_status="accounting_basis_change"
    )
    source["health_spending_gdp_share.parquet"][0].update(
        gdp_share_percent=None, gdp_share_status="missing_denominator"
    )
    result = build_plot_contracts(source)
    for name, reason in (
        ("historical_health_spending_yoy_growth.png", "accounting_basis_change"),
        ("health_spending_vs_gdp.png", "missing_denominator"),
    ):
        assert result[name]["series"] == []
        assert result[name]["omissions"] == [
            {"record_id": "health-2024", "year": 2024, "reason": reason}
        ]


def test_line_segments_never_bridge_gaps_bases_periods_or_sources() -> None:
    rows = [
        historical(2000),
        historical(2001),
        historical(2003),
        historical(2004, accounting_basis="IFRS"),
        historical(2005, period_end_month=3),
        historical(2006, source_vintage="other"),
        historical(2007, source_object_sha256="c" * 64),
        historical(2008, accounting_basis=None),
        historical(2009, accounting_basis=None),
        historical(2010, period_end_month=None),
        historical(2011, period_end_month=None),
    ]
    source = tables()
    source["historical_nominal.parquet"] = rows
    result = build_plot_contracts(source)
    segments = result["historical_health_spending_nominal.png"]["series"]
    assert sorted(len(series["points"]) for series in segments) == [1] * 9 + [2]
    source["historical_nominal.parquet"] = list(reversed(rows))
    assert build_plot_contracts(source) == result


def test_budget_filters_and_partitioned_trends() -> None:
    source = tables()
    rows = [
        budget(2024),
        budget(2025),
        budget(2027),
        budget(2025, amount_type="Budget"),
        budget(2025, source_vintage="other"),
        budget(2025, source_object_sha256="d" * 64),
        budget(2025, functional_classification="No Functional Classification"),
        budget(2025, functional_classification="Other"),
    ]
    source["recent_classification_trends.parquet"] = rows
    source["recent_functional_breakdown.parquet"] = rows
    result = build_plot_contracts(source)
    health = result["recent_trends_health_classification.png"]
    assert sorted(len(series["points"]) for series in health["series"]) == [
        1,
        1,
        1,
        1,
        2,
    ]
    assert len(result["recent_trends_no_classification.png"]["series"]) == 1
    breakdown = result[
        "recent_appropriations_functional_breakdown_2025_Estimated_Actual.png"
    ]
    assert sum(len(series["points"]) for series in breakdown["series"]) == 5
    assert "fiscal basis unverified" in health["xlabel"]
    for name in source:
        source[name] = list(reversed(source[name]))
    assert build_plot_contracts(source) == result


def test_empty_tables_still_define_all_six_plots() -> None:
    result = build_plot_contracts({name: [] for name in tables()})
    assert len(result) == 6
    assert all(
        plot["series"] == [] and plot["omissions"] == [] for plot in result.values()
    )
