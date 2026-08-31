"""Every original and donor row receives an explicit comparison outcome."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations.historical_reconciliation import (
    compare_historical,
)


def _fact(year: int, value: str, label: str | None = None) -> dict[str, object]:
    return {
        "year": year,
        "amount": Decimal(value),
        "year_label": label or str(year),
        "measure": "health_spending",
        "record_id": f"record-{year}",
        "source_object_sha256": "a" * 64,
    }


def _lineage(year: int) -> dict[str, object]:
    return {
        "record_id": f"record-{year}",
        "source_object_sha256": "a" * 64,
        "field": "amount",
        "source_coordinate": f"'Spending'!H{year}",
    }


def test_complete_union_and_explicit_differences() -> None:
    facts = [
        _fact(1975, "1"),
        _fact(1976, "605.70000000000005"),
        _fact(1977, "2", "1977†"),
    ]
    oracle = {
        "health_spending": [(1975, "1"), (1976, "605.7"), (1978, "3")],
        "nominal_gdp": [],
    }
    result = compare_historical(
        facts, [_lineage(year) for year in (1975, 1976, 1977)], oracle
    )
    assert [row["status"] for row in result] == [
        "exact_match",
        "value_difference",
        "source_only",
        "donor_only",
    ]
    assert result[1]["delta"] == "5E-14"
    assert result[2]["reason"] == "annotated_year_absent_from_donor"
    assert result[2]["source_coordinate"] == "'Spending'!H1977"
    assert result[3]["source_record_id"] is None
    assert result[0]["source_value"] == "1"
    assert result[0]["donor_value"] == "1"
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas/health-historical-reconciliation-v1.schema.json"
        ).read_text()
    )
    Draft202012Validator.check_schema(schema)
    for row in result:
        Draft202012Validator(schema).validate(row)


def test_unannotated_source_only_and_gdp() -> None:
    fact = {**_fact(2000, "1"), "measure": "nominal_gdp"}
    result = compare_historical(
        [fact], [_lineage(2000)], {"health_spending": [], "nominal_gdp": []}
    )
    assert result[0]["reason"] == "source_year_absent_from_donor"


@pytest.mark.parametrize("year", [True, 0, 10000, "1975"])
def test_invalid_years_rejected(year: object) -> None:
    fact = {**_fact(1975, "1"), "year": year}
    with pytest.raises(ValueError, match="reconciliation_year"):
        compare_historical(
            [fact], [_lineage(1975)], {"health_spending": [], "nominal_gdp": []}
        )


def test_non_amount_lineage_is_not_used() -> None:
    lineage = [_lineage(1975), {**_lineage(1975), "field": "year"}]
    result = compare_historical(
        [_fact(1975, "1")],
        lineage,
        {"health_spending": [(1975, "1")], "nominal_gdp": []},
    )
    assert result[0]["status"] == "exact_match"


def test_unknown_oracle_measures_rejected() -> None:
    with pytest.raises(ValueError, match="reconciliation_oracle_measures"):
        compare_historical([], [], {})


@pytest.mark.parametrize("value", ["invalid", "1e50", "1e-18"])
def test_invalid_oracle_number_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="reconciliation_donor"):
        compare_historical(
            [], [], {"health_spending": [(1975, value)], "nominal_gdp": []}
        )


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate_source",
        "duplicate_donor",
        "missing_lineage",
        "duplicate_lineage",
        "wrong_lineage_object",
        "unknown_measure",
        "null_amount",
        "nonfinite_donor",
    ],
)
def test_invalid_reconciliation_fails_closed(fault: str) -> None:
    facts = [_fact(1975, "1")]
    lineage = [_lineage(1975)]
    oracle = {"health_spending": [(1975, "1")], "nominal_gdp": []}
    if fault == "duplicate_source":
        facts *= 2
    elif fault == "duplicate_donor":
        oracle["health_spending"] *= 2
    elif fault == "missing_lineage":
        lineage = []
    elif fault == "duplicate_lineage":
        lineage *= 2
    elif fault == "wrong_lineage_object":
        lineage[0]["source_object_sha256"] = "b" * 64
    elif fault == "unknown_measure":
        facts[0]["measure"] = "other"
    elif fault == "null_amount":
        facts[0]["amount"] = None
    else:
        oracle["health_spending"] = [(1975, "NaN")]
    with pytest.raises(ValueError, match="reconciliation"):
        compare_historical(facts, lineage, oracle)
