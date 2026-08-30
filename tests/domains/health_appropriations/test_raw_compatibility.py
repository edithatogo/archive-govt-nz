"""Source-derived compatibility keeps exact decimals beside legacy values."""

from decimal import Decimal
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.raw_compatibility import (
    project_record,
)


def fact(**changes: object) -> dict[str, Any]:
    row = {
        "record_id": "sha256:" + "a" * 64,
        "source_object_sha256": "b" * 64,
        "year": 1976,
        "measure": "health_spending",
        "unit": "NZD_millions",
        "amount": Decimal("605.70000000000005000"),
        "year_label": "1976 (1)",
        "accounting_basis": "Cash",
        "period_end_month": 3,
    }
    row.update(changes)
    return row


def test_historical_projection_preserves_exact_amount() -> None:
    result = project_record("historical", fact())
    assert result["table"] == "historical_health_spending"
    assert result["values"] == [1976, float(Decimal("605.70000000000005"))]
    assert result["exact_amount"] == "605.70000000000005000"
    assert result["representation_changed"] is True
    assert result["source_context"]["year_label"] == "1976 (1)"


@pytest.mark.parametrize("profile", ["befu", "hyefu"])
def test_forecast_projection(profile: str) -> None:
    result = project_record(profile, fact(amount=Decimal("123.000")))
    assert result["table"] == (
        "health_spending_summary_"
        + {"befu": "befu25", "hyefu": "hyefu24"}[profile]
        + "_data_expense_tables"
    )
    assert result["values"] == [1976, 123]
    assert result["representation_changed"] is False


def test_gdp_projection() -> None:
    result = project_record(
        "historical", fact(measure="nominal_gdp", amount=Decimal(456))
    )
    assert result["table"] == "gdp_historical"
    assert result["values"] == [1976, 456]


def test_budget_projection() -> None:
    row = fact(
        measure="appropriation_amount",
        unit="NZD_thousands",
        amount=Decimal(42),
        department="Ministry",
        appropriation_name="Services",
        functional_classification="Health",
        amount_type="Actuals",
        portfolio_name="Health",
    )
    assert project_record("budget", row)["values"] == [
        1976,
        "Ministry",
        "Services",
        "Health",
        42,
        "Actuals",
        "Health",
    ]


@pytest.mark.parametrize(
    "changes",
    [
        {"year": True},
        {"year": 0},
        {"year": 10000},
        {"year": 2020.0},
        {"amount": 1.2},
        {"amount": Decimal("NaN")},
        {"amount": Decimal("Infinity")},
        {"unit": "NZD_thousands"},
        {"measure": "other"},
        {"record_id": "bad"},
        {"source_object_sha256": "bad"},
    ],
)
def test_invalid_facts_rejected(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"invalid_|unsupported_"):
        project_record("historical", fact(**changes))


@pytest.mark.parametrize(
    "amount", [Decimal("1.2"), Decimal(2**63), Decimal(-(2**63) - 1)]
)
def test_integer_projection_never_coerces(amount: Decimal) -> None:
    with pytest.raises(ValueError, match="nonintegral_or_out_of_range"):
        project_record("befu", fact(amount=amount))


def test_unknown_profile_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported_"):
        project_record("unknown", fact())


def test_float_overflow_rejected() -> None:
    with pytest.raises(ValueError, match="nonfinite_compatibility_amount"):
        project_record("historical", fact(amount=Decimal("1e999")))


def test_budget_missing_text_rejected() -> None:
    with pytest.raises(ValueError, match="invalid_compatibility_text"):
        project_record(
            "budget",
            fact(
                measure="appropriation_amount", unit="NZD_thousands", amount=Decimal(1)
            ),
        )


@pytest.mark.parametrize("year", [1, 9999])
@pytest.mark.parametrize("amount", [Decimal(-(2**63)), Decimal(2**63 - 1)])
def test_exact_integer_boundaries(year: int, amount: Decimal) -> None:
    assert project_record("befu", fact(year=year, amount=amount))["values"] == [
        year,
        int(amount),
    ]


def test_exact_binary_value_and_source_unchanged() -> None:
    row = fact(amount=Decimal("0.5"))
    original = row.copy()
    result = project_record("historical", row)
    assert result["representation_changed"] is False
    assert result["source_context"] == {
        key: value for key, value in original.items() if key != "amount"
    }
    assert result["record_id"] == original["record_id"]
    assert row == original
