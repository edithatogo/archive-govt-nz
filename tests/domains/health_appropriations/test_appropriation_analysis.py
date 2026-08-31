"""Budget aggregates never mix source vintages or actual/forecast categories."""

from decimal import Decimal, localcontext
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.appropriation_analysis import (
    analyze_appropriations,
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
