"""Exact source-derived Budget classification aggregates with input identities."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

_CONTEXT = Context(prec=80, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.001")
_LIMIT = Decimal("1e17")
_MAX_YEAR = 9999
_GROUP_FIELDS = (
    "source_object_sha256",
    "source_vintage",
    "year",
    "functional_classification",
    "amount_type",
)
_TEXT_FIELDS = (
    "record_id",
    "source_object_sha256",
    "source_vintage",
    "functional_classification",
    "amount_type",
    "department",
    "portfolio_name",
)


def _validate(row: dict[str, Any]) -> None:
    if (
        row["measure"] != "appropriation_amount"
        or row["unit"] != "NZD_thousands"
        or type(row["year"]) is not int
        or not 1 <= row["year"] <= _MAX_YEAR
        or not isinstance(row["amount"], Decimal)
        or not row["amount"].is_finite()
        or row["amount"].copy_abs() >= _LIMIT
        or row["amount"] != row["amount"].quantize(_QUANTUM, context=_CONTEXT)
        or any(not isinstance(row[key], str) or not row[key] for key in _TEXT_FIELDS)
        or not isinstance(row["quality_flags"], list)
        or any(not isinstance(flag, str) for flag in row["quality_flags"])
    ):
        message = "invalid_appropriation_analysis_fact"
        raise ValueError(message)


def analyze_appropriations(
    facts: list[dict[str, Any]], *, breakdown_year: int = 2025
) -> dict[str, list[dict[str, Any]]]:
    """Aggregate verified Budget facts without merging vintages or amount types.

    No file verification, classification crosswalk, or period comparability is
    implied. Source record IDs make every sum reproducible; negative corrections
    remain included. Original flags and contributing departments/portfolios are
    retained. The breakdown explicitly selects only 'Estimated Actual' rows.
    """
    if type(breakdown_year) is not int or not 1 <= breakdown_year <= _MAX_YEAR:
        message = "invalid_breakdown_year"
        raise ValueError(message)
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    identities: set[str] = set()
    for row in facts:
        _validate(row)
        if row["record_id"] in identities:
            message = "duplicate_appropriation_identity"
            raise ValueError(message)
        identities.add(row["record_id"])
        groups.setdefault(tuple(row[field] for field in _GROUP_FIELDS), []).append(row)
    trends = []
    with localcontext(_CONTEXT):
        for key, rows in sorted(groups.items()):
            trends.append(
                {
                    **dict(zip(_GROUP_FIELDS, key, strict=True)),
                    "unit": "NZD_thousands",
                    "total_amount_thousands": str(
                        sum((row["amount"] for row in rows), Decimal(0)).quantize(
                            _QUANTUM
                        )
                    ),
                    "input_record_ids": sorted(row["record_id"] for row in rows),
                    "departments": sorted({row["department"] for row in rows}),
                    "portfolios": sorted({row["portfolio_name"] for row in rows}),
                    "quality_flags": sorted(
                        {flag for row in rows for flag in row["quality_flags"]}
                    ),
                    "formula_policy": (
                        "sum_exact_budget_source_vintage_class_amount_type/v1"
                    ),
                    "period_basis": "unverified",
                    "classification_mapping": "source_labels_only",
                }
            )
    return {
        "trends": trends,
        "breakdown": [
            row.copy()
            for row in trends
            if row["year"] == breakdown_year
            and row["amount_type"] == "Estimated Actual"
        ],
    }
