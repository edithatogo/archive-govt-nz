"""Pure source-derived nominal analytics; no cross-basis growth or implicit joins."""

from __future__ import annotations

from calendar import monthrange
from copy import deepcopy
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

_CONTEXT = Context(prec=80, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000000000001")
_MAX_AMOUNT = Decimal("1e21")
_SOURCE_QUANTUM = Decimal("1e-17")
_MAX_YEAR = 9999


def _validate(row: dict[str, Any]) -> None:
    if (
        row["measure"] not in {"health_spending", "nominal_gdp"}
        or row["unit"] != "NZD_millions"
        or type(row["year"]) is not int
        or not 1 <= row["year"] <= _MAX_YEAR
        or not isinstance(row["amount"], Decimal)
        or not row["amount"].is_finite()
        or row["amount"].copy_abs() >= _MAX_AMOUNT
        or row["amount"] != row["amount"].quantize(_SOURCE_QUANTUM, context=_CONTEXT)
        or (
            row.get("accounting_basis") is not None
            and not isinstance(row["accounting_basis"], str)
        )
        or any(
            not isinstance(row[key], str) or not row[key]
            for key in ("record_id", "source_object_sha256", "source_vintage")
        )
    ):
        message = "invalid_historical_analysis_fact"
        raise ValueError(message)
    end = row.get("valid_time_end")
    month = row.get("period_end_month")
    if (end is not None or month is not None) and (
        type(end) is not date
        or type(month) is not int
        or end.year != row["year"]
        or end.month != month
        or end.day != monthrange(end.year, end.month)[1]
    ):
        message = "inconsistent_historical_period"
        raise ValueError(message)


def _key(row: dict[str, Any]) -> tuple[str, str, int]:
    return row["source_object_sha256"], row["source_vintage"], row["year"]


def _growth_status(current: dict[str, Any], previous: dict[str, Any] | None) -> str:  # noqa: PLR0911 - ordered, independently reason-coded comparability gates
    if previous is None:
        return "no_previous_observation"
    if current["year"] != previous["year"] + 1:
        return "year_gap"
    if (
        current.get("period_end_month") is None
        or previous.get("period_end_month") is None
    ):
        return "period_unverified"
    if current["period_end_month"] != previous["period_end_month"]:
        return "period_change"
    if not current.get("accounting_basis") or not previous.get("accounting_basis"):
        return "accounting_basis_unverified"
    if current["accounting_basis"] != previous["accounting_basis"]:
        return "accounting_basis_change"
    if previous["amount"] <= 0:
        return "nonpositive_previous_amount"
    return "comparable"


def _share_status(current: dict[str, Any], denominator: dict[str, Any] | None) -> str:
    if denominator is None:
        return "missing_denominator"
    if (
        current.get("valid_time_end") is None
        or denominator.get("valid_time_end") is None
    ):
        return "period_unverified"
    if current["valid_time_end"] != denominator["valid_time_end"]:
        return "period_mismatch"
    if denominator["amount"] <= 0:
        return "nonpositive_denominator"
    return "aligned"


def _percent(numerator: Decimal, denominator: Decimal, *, growth: bool) -> str:
    with localcontext(_CONTEXT):
        value = (numerator / denominator - int(growth)) * 100
        return str(value.quantize(_QUANTUM))


def analyze_historical(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Analyze validated historical facts, keeping vintages and source objects apart.

    This is a pure computation, not a file verifier. Callers must verify raw-run
    hashes and lineage before persistence. Percentages use independent 80-digit
    Decimal arithmetic rounded half-even to 12 decimal places; exact input values
    and source IDs remain available. Missing comparisons are never zero-filled.
    GDP accounting basis need not equal Health's; GDP must share the source,
    vintage, currency unit and exact period end. Period starts remain unverified.
    """
    indexed: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    ids: set[str] = set()
    for row in facts:
        _validate(row)
        key = (*_key(row), row["measure"])
        if key in indexed or row["record_id"] in ids:
            message = "duplicate_historical_identity"
            raise ValueError(message)
        indexed[key] = row
        ids.add(row["record_id"])
    history: dict[tuple[str, str], dict[str, Any]] = {}
    result = []
    for key, row in sorted(indexed.items()):
        if row["measure"] != "health_spending":
            continue
        series = key[:2]
        previous = history.get(series)
        denominator = indexed.get((*_key(row), "nominal_gdp"))
        growth_status = _growth_status(row, previous)
        share_status = _share_status(row, denominator)
        result.append(
            {
                "record_id": row["record_id"],
                "year": row["year"],
                "exact_amount": str(row["amount"]),
                "source_context": deepcopy(
                    {k: v for k, v in row.items() if k != "amount"}
                ),
                "yoy_status": growth_status,
                "yoy_percent": _percent(row["amount"], previous["amount"], growth=True)
                if growth_status == "comparable" and previous is not None
                else None,
                "yoy_input_ids": [previous["record_id"], row["record_id"]]
                if previous is not None
                else [row["record_id"]],
                "previous_exact_amount": str(previous["amount"])
                if previous is not None
                else None,
                "gdp_share_status": share_status,
                "gdp_share_percent": _percent(
                    row["amount"], denominator["amount"], growth=False
                )
                if share_status == "aligned" and denominator is not None
                else None,
                "gdp_input_ids": [row["record_id"], denominator["record_id"]]
                if denominator is not None
                else [row["record_id"]],
                "gdp_exact_amount": str(denominator["amount"])
                if denominator is not None
                else None,
                "formula_policy": "nominal_historical_period_basis_guarded/v1",
                "rounding_policy": "decimal80_half_even_percent_12dp",
            }
        )
        history[series] = row
    return result
