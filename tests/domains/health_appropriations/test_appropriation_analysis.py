"""Budget aggregates never mix source vintages or actual/forecast categories."""

from decimal import Decimal, localcontext
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.appropriation_analysis import (
    analyze_appropriations,
    compare_budget_to_estimated_actual,
)


def fact(identity: str, value: str, **extra: object) -> dict[str, Any]:
    return {
        "record_id": identity,
        "source_object_sha256": "a" * 64,
        "source_vintage": "Budget-2025",
        "year": 2025,
        "measure": "appropriation_amount",
        "amount": Decimal(value),
        "unit": "NZD_thousands",
        "functional_classification": "Health",
        "amount_type": "Estimated Actual",
        "department": "Ministry of Health",
        "portfolio_name": "Minister of Health",
        "quality_flags": ["financial_year_basis_unverified"],
        **extra,
    }


def test_exact_aggregation_and_explicit_breakdown() -> None:
    rows = [
        fact("a", "100.001"),
        fact("b", "0.002"),
        fact("c", "5", amount_type="Budget"),
    ]
    result = analyze_appropriations(rows)
    assert result == analyze_appropriations(list(reversed(rows)))
    assert len(result["trends"]) == 2
    assert len(result["breakdown"]) == 1
    row = result["breakdown"][0]
    assert row["total_amount_thousands"] == "100.003"
    assert row["input_record_ids"] == ["a", "b"]
    assert row["quality_flags"] == ["financial_year_basis_unverified"]
    assert row["departments"] == ["Ministry of Health"]
    assert row["portfolios"] == ["Minister of Health"]
    assert rows[0]["amount"] == Decimal("100.001")
    with localcontext() as context:
        context.prec = 2
        assert analyze_appropriations(rows) == result
    assert analyze_appropriations(rows, breakdown_year=2024)["breakdown"] == []


@pytest.mark.parametrize(
    "change",
    [
        {"year": 2024},
        {"source_vintage": "Budget-2024"},
        {"source_object_sha256": "b" * 64},
        {"functional_classification": "Other"},
        {"amount_type": "Actuals"},
    ],
)
def test_group_boundaries(change: dict[str, object]) -> None:
    assert (
        len(
            analyze_appropriations([fact("a", "1"), fact("b", "2", **change)])["trends"]
        )
        == 2
    )


@pytest.mark.parametrize(
    "change",
    [
        {"record_id": ""},
        {"source_vintage": None},
        {"source_object_sha256": 1},
        {"functional_classification": None},
        {"amount_type": ""},
        {"department": None},
        {"portfolio_name": None},
        {"measure": "health_spending"},
        {"unit": "NZD_millions"},
        {"year": True},
        {"year": 0},
        {"year": 10000},
        {"amount": 1},
        {"amount": Decimal("NaN")},
        {"amount": Decimal("Infinity")},
        {"amount": Decimal("1e17")},
        {"amount": Decimal("-1e17")},
        {"amount": Decimal("0.0001")},
        {"quality_flags": "flag"},
        {"quality_flags": [1]},
    ],
)
def test_invalid_fact(change: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="invalid_appropriation"):
        analyze_appropriations([fact("a", "1", **change)])


def test_duplicate_identity() -> None:
    with pytest.raises(ValueError, match="duplicate_appropriation"):
        analyze_appropriations([fact("a", "1"), fact("a", "2")])


def test_empty_and_negative_corrections() -> None:
    assert analyze_appropriations([]) == {"trends": [], "breakdown": []}
    result = analyze_appropriations(
        [fact("a", "1"), fact("b", "-2", quality_flags=["correction"])]
    )
    assert result["trends"][0]["total_amount_thousands"] == "-1.000"
    assert result["trends"][0]["quality_flags"] == [
        "correction",
        "financial_year_basis_unverified",
    ]


@pytest.mark.parametrize("year", [True, 0, 10000])
def test_invalid_breakdown_year(year: int) -> None:
    with pytest.raises(ValueError, match="invalid_breakdown_year"):
        analyze_appropriations([], breakdown_year=year)


def test_boundary_values() -> None:
    result = analyze_appropriations(
        [
            fact("a", "99999999999999999.999", year=1),
            fact("b", "-99999999999999999.999", year=9999),
        ]
    )
    assert len(result["trends"]) == 2


def test_budget_estimated_actual_comparison_is_exact_and_source_bounded() -> None:
    rows = [
        fact("budget-a", "100.001", amount_type="Budget"),
        fact("budget-b", "0.002", amount_type="Budget"),
        fact("actual", "97.500", amount_type="Estimated Actual"),
        fact("forecast", "80", amount_type="Forecast"),
        fact(
            "other-edition-budget",
            "10",
            amount_type="Budget",
            source_vintage="Budget-2024",
        ),
    ]
    rows.append(
        fact(
            "other-edition-actual",
            "11",
            amount_type="Estimated Actual",
            source_vintage="Budget-2024",
        )
    )

    compared = compare_budget_to_estimated_actual(rows)
    assert compared == compare_budget_to_estimated_actual(list(reversed(rows)))
    assert len(compared) == 2
    current = compared[0]
    assert current["source_vintage"] == "Budget-2024"
    assert current["budget_amount"] == "10.000"
    assert current["estimated_actual_amount"] == "11.000"
    assert current["estimated_minus_budget"] == "1.000"
    assert current["comparison_status"] == "both_source_labels_present"
    assert current["budget_input_record_ids"] == ["other-edition-budget"]
    assert current["estimated_actual_input_record_ids"] == ["other-edition-actual"]
    assert current["period_basis"] == "unverified"
    assert compared[1]["source_vintage"] == "Budget-2025"
    assert compared[1]["budget_amount"] == "100.003"
    assert compared[1]["estimated_minus_budget"] == "-2.503"
    assert compared[1]["estimated_actual_input_record_ids"] == ["actual"]


@pytest.mark.parametrize(
    ("rows", "status"),
    [
        ([fact("budget", "10", amount_type="Budget")], "missing_estimated_actual"),
        (
            [fact("actual", "10", amount_type="Estimated Actual")],
            "missing_budget",
        ),
    ],
)
def test_budget_estimated_actual_comparison_keeps_unmatched_groups(
    rows: list[dict[str, Any]], status: str
) -> None:
    result = compare_budget_to_estimated_actual(rows)
    assert len(result) == 1
    assert result[0]["comparison_status"] == status
    assert result[0]["estimated_minus_budget"] is None


def test_budget_estimated_actual_comparison_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="duplicate_appropriation_identity"):
        compare_budget_to_estimated_actual(
            [fact("same", "1", amount_type="Budget"), fact("same", "2")]
        )
