"""Explicit legacy-value projections; canonical source facts are never modified."""

from __future__ import annotations

import math
import re
from decimal import Decimal
from typing import Any

_MAX_YEAR = 9999
_MIN_INTEGER = -(2**63)
_MAX_INTEGER = 2**63 - 1
_TARGETS = {
    ("budget", "appropriation_amount"): (
        "recent_health_appropriations",
        "NZD_thousands",
    ),
    ("befu", "health_spending"): (
        "health_spending_summary_befu25_data_expense_tables",
        "NZD_millions",
    ),
    ("hyefu", "health_spending"): (
        "health_spending_summary_hyefu24_data_expense_tables",
        "NZD_millions",
    ),
    ("historical", "health_spending"): ("historical_health_spending", "NZD_millions"),
    ("historical", "nominal_gdp"): ("gdp_historical", "NZD_millions"),
}
_TEXT_FIELDS = (
    "department",
    "appropriation_name",
    "functional_classification",
    "amount_type",
    "portfolio_name",
)


def _amount(amount: Decimal, *, real: bool) -> tuple[int | float, bool]:
    if real:
        value = float(amount)
        if not math.isfinite(value):
            message = "nonfinite_compatibility_amount"
            raise ValueError(message)
        return value, Decimal(value) != amount
    if (
        amount != amount.to_integral_value()
        or not _MIN_INTEGER <= amount <= _MAX_INTEGER
    ):
        message = "nonintegral_or_out_of_range_compatibility_amount"
        raise ValueError(message)
    return int(amount), False


def project_record(profile: str, row: dict[str, Any]) -> dict[str, Any]:
    """Map one canonical fact to legacy columns with a loss-aware sidecar.

    This pure function is not a source verifier or publication action. Callers
    must verify the enclosing raw run and preserve its field-lineage dataset.
    Source context is retained separately because legacy tables cannot encode
    vintage, fiscal period, annotated year labels or decimal representation.
    """
    target = _TARGETS.get((profile, row.get("measure", "")))
    if target is None or row.get("unit") != target[1]:
        message = "unsupported_compatibility_measure_or_unit"
        raise ValueError(message)
    if type(row.get("year")) is not int or not 1 <= row["year"] <= _MAX_YEAR:
        message = "invalid_compatibility_year"
        raise ValueError(message)
    amount = row.get("amount")
    if not isinstance(amount, Decimal) or not amount.is_finite():
        message = "invalid_canonical_amount"
        raise ValueError(message)
    for field, pattern in (
        ("record_id", r"sha256:[0-9a-f]{64}"),
        ("source_object_sha256", r"[0-9a-f]{64}"),
    ):
        if (
            not isinstance(row.get(field), str)
            or re.fullmatch(pattern, row[field]) is None
        ):
            message = "invalid_compatibility_source_identity"
            raise ValueError(message)
    value, changed = _amount(amount, real=target[0] == "historical_health_spending")
    values: list[object] = [row["year"], value]
    if profile == "budget":
        if any(not isinstance(row.get(field), str) for field in _TEXT_FIELDS):
            message = "invalid_compatibility_text"
            raise ValueError(message)
        values = [
            row["year"],
            *(row[field] for field in _TEXT_FIELDS[:3]),
            value,
            *(row[field] for field in _TEXT_FIELDS[3:]),
        ]
    return {
        "table": target[0],
        "record_id": row["record_id"],
        "values": values,
        "exact_amount": str(amount),
        "representation_changed": changed,
        "source_context": {key: value for key, value in row.items() if key != "amount"},
    }
