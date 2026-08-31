"""Historical analytics retain exact inputs and make missing comparisons explicit."""

from datetime import date
from decimal import Decimal, localcontext
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations.historical_analysis import (
    analyze_historical,
)


def fact(
    observation_year: int,
    amount: str,
    measure: str = "health_spending",
    **extra: object,
) -> dict[str, Any]:
    return {
        "record_id": f"{measure}-{observation_year}",
        "source_object_sha256": "a" * 64,
        "source_vintage": "fiscal-2024",
        "year": observation_year,
        "measure": measure,
        "amount": Decimal(amount),
        "unit": "NZD_millions",
        "period_end_month": 6,
        "valid_time_end": date(observation_year, 6, 30),
        "accounting_basis": "Cash" if measure == "health_spending" else None,
        "quality_flags": ["period_start_not_provided"],
        **extra,
    }


def test_exact_nominal_growth_share_and_input_preservation() -> None:
    rows = [fact(2023, "100"), fact(2024, "125"), fact(2024, "500", "nominal_gdp")]
    result = analyze_historical(rows)
    assert result == analyze_historical(list(reversed(rows)))
    first, last = result
    assert first["yoy_percent"] is None
    assert first["yoy_status"] == "no_previous_observation"
    assert first["gdp_share_status"] == "missing_denominator"
    assert last["exact_amount"] == "125"
    assert last["yoy_percent"] == "25.000000000000"
    assert last["gdp_share_percent"] == "25.000000000000"
    assert last["yoy_input_ids"] == ["health_spending-2023", "health_spending-2024"]
    assert last["gdp_input_ids"] == ["health_spending-2024", "nominal_gdp-2024"]
    assert last["source_context"]["quality_flags"] == ["period_start_not_provided"]
    assert rows[1]["amount"] == Decimal(125)
    assert "yoy_percent" not in rows[1]


@pytest.mark.parametrize(
    ("change", "status"),
    [
        ({"accounting_basis": "IFRS"}, "accounting_basis_change"),
        ({"accounting_basis": None}, "accounting_basis_unverified"),
        ({"period_end_month": 3, "valid_time_end": date(2024, 3, 31)}, "period_change"),
        ({"period_end_month": None, "valid_time_end": None}, "period_unverified"),
        ({"year": 2025, "valid_time_end": date(2025, 6, 30)}, "year_gap"),
    ],
)
def test_growth_breaks(change: dict[str, Any], status: str) -> None:
    rows = [fact(2023, "100"), fact(2024, "125", **change)]
    last = analyze_historical(rows)[-1]
    assert last["yoy_percent"] is None
    assert last["yoy_status"] == status


def test_decimal_context_cannot_change_results() -> None:
    rows = [fact(2023, "3"), fact(2024, "4")]
    expected = analyze_historical(rows)
    with localcontext() as context:
        context.prec = 2
        assert analyze_historical(rows) == expected
    assert expected[-1]["yoy_percent"] == "33.333333333333"


@pytest.mark.parametrize("value", ["0", "-1"])
def test_nonpositive_previous(value: str) -> None:
    row = analyze_historical([fact(2023, value), fact(2024, "1")])[-1]
    assert row["yoy_status"] == "nonpositive_previous_amount"
    assert row["yoy_percent"] is None


@pytest.mark.parametrize(
    ("changes", "status"),
    [
        ({"amount": Decimal(0)}, "nonpositive_denominator"),
        ({"amount": Decimal(-1)}, "nonpositive_denominator"),
        ({"period_end_month": None, "valid_time_end": None}, "period_unverified"),
        (
            {"period_end_month": 3, "valid_time_end": date(2024, 3, 31)},
            "period_mismatch",
        ),
        ({"source_vintage": "another-vintage"}, "missing_denominator"),
        ({"source_object_sha256": "b" * 64}, "missing_denominator"),
    ],
)
def test_denominator_gates(changes: dict[str, object], status: str) -> None:
    result = analyze_historical(
        [fact(2024, "1"), {**fact(2024, "3", "nominal_gdp"), **changes}]
    )
    assert result[0]["gdp_share_status"] == status
    assert result[0]["gdp_share_percent"] is None


@pytest.mark.parametrize("key", ["source_vintage", "source_object_sha256"])
def test_never_splice_source_or_vintage(key: str) -> None:
    rows = [fact(2023, "1"), fact(2024, "2", **{key: "different"})]
    assert all(
        row["yoy_status"] == "no_previous_observation"
        for row in analyze_historical(rows)
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"measure": "real_health"},
        {"unit": "NZD_thousands"},
        {"year": True},
        {"year": 0},
        {"year": 10000},
        {"amount": 1},
        {"amount": Decimal("NaN")},
        {"amount": Decimal("Infinity")},
        {"amount": Decimal("-Infinity")},
        {"amount": Decimal("1e21")},
        {"amount": Decimal("-1e21")},
        {"amount": Decimal("1e-18")},
        {"record_id": ""},
        {"source_vintage": None},
        {"source_object_sha256": 1},
        {"valid_time_end": "2024-06-30"},
        {"period_end_month": True},
        {"valid_time_end": date(2023, 6, 30)},
        {"period_end_month": 3},
        {"period_end_month": None},
        {"valid_time_end": None},
    ],
)
def test_invalid_facts_fail(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="historical"):
        analyze_historical([{**fact(2024, "1"), **changes}])


@pytest.mark.parametrize("same_id", [False, True])
def test_duplicate_keys_or_ids_rejected(*, same_id: bool) -> None:
    first = fact(2024, "1")
    second = (
        fact(2023, "2", record_id=first["record_id"])
        if same_id
        else fact(2024, "2", record_id="other")
    )
    with pytest.raises(ValueError, match="duplicate_historical_identity"):
        analyze_historical([first, second])


def test_missing_context_on_previous_and_current() -> None:
    for changes, expected in [
        ({"period_end_month": None, "valid_time_end": None}, "period_unverified"),
        ({"accounting_basis": None}, "accounting_basis_unverified"),
    ]:
        result = analyze_historical([{**fact(2023, "1"), **changes}, fact(2024, "2")])
        assert result[-1]["yoy_status"] == expected
    result = analyze_historical(
        [
            fact(2024, "1", period_end_month=None, valid_time_end=None),
            fact(2024, "2", "nominal_gdp"),
        ]
    )
    assert result[0]["gdp_share_status"] == "period_unverified"


def test_empty_and_gdp_only() -> None:
    assert analyze_historical([]) == []
    assert analyze_historical([fact(2024, "1", "nominal_gdp")]) == []


def test_exact_precision_and_independent_output_context() -> None:
    source = fact(1976, "605.70000000000005000")
    result = analyze_historical([source])[0]
    assert result["exact_amount"] == "605.70000000000005000"
    result["source_context"]["quality_flags"].append("not-in-original")
    assert source["quality_flags"] == ["period_start_not_provided"]


def test_amount_and_year_boundaries() -> None:
    rows = [
        fact(1, "0.00000000000000001"),
        fact(9999, "999999999999999999999.99999999999999999"),
    ]
    assert len(analyze_historical(rows)) == 2
    assert analyze_historical(rows)[-1]["yoy_status"] == "year_gap"


@pytest.mark.parametrize(
    "changes", [{"valid_time_end": date(2024, 6, 29)}, {"accounting_basis": 1}]
)
def test_invalid_semantic_context(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="historical"):
        analyze_historical([{**fact(2024, "1"), **changes}])


@given(
    st.integers(min_value=1, max_value=1_000_000),
    st.integers(min_value=1, max_value=10),
)
@settings(max_examples=30, deadline=None)
def test_generated_exact_integer_growth(previous: int, factor: int) -> None:
    result = analyze_historical(
        [fact(2023, str(previous)), fact(2024, str(previous * factor))]
    )
    assert Decimal(result[-1]["yoy_percent"]) == (factor - 1) * 100
