"""Compare overlapping GDP vintages without interpreting their differences."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from archive_govt_nz.domains.health_appropriations import (
    gdp,
)
from archive_govt_nz.domains.health_appropriations import (
    gdp_canonical_projection as projection,
)

_ERROR = "gdp_vintage_comparison_invalid"
_OVERLAP_COUNT = len(gdp.PROFILE_PERIODS[gdp.VINTAGE])
_MEASURE = "gross_domestic_product_expenditure_actual_current_prices"
_COMMON_MEANING = (
    "unit",
    "price_basis",
    "amount_type",
    "institutional_coverage",
    "accounting_basis",
    "seasonal_adjustment",
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _index(
    rows: list[dict[str, Any]], vintage: str, transformation: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        _require(
            row.get("recordset") == "fiscal_context_fact"
            and row.get("source_vintage") == vintage
            and row.get("transformation_id") == transformation
            and row.get("measure") == _MEASURE
            and row.get("currency") is None
            and row.get("base_period") is None
            and row.get("denominator_definition") is None
            and row.get("rights_state") == "not_evaluated"
            and row.get("valid_time_status") == "source_quarter_ended"
        )
        for key in _COMMON_MEANING:
            _require(row.get(key) == rows[0].get(key))
        token = row.get("period_token")
        value = row.get("amount")
        _require(isinstance(token, str))
        if not isinstance(token, str) or token in result:
            raise ValueError(_ERROR)
        _require(isinstance(value, Decimal) and value.is_finite())
        value_token = row.get("value_token")
        if not isinstance(value_token, str):
            raise TypeError(_ERROR)
        try:
            _require(Decimal(value_token) == value)
        except Exception as exc:
            raise ValueError(_ERROR) from exc
        result[token] = row
    return result


def compare_gdp_vintages(
    march_rows: list[dict[str, Any]], june_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare exact overlap under shared series identity; do not explain changes."""
    _require(len(march_rows) == len(gdp.PROFILE_PERIODS[gdp.VINTAGE]))
    _require(len(june_rows) == len(gdp.PROFILE_PERIODS[gdp.JUNE_VINTAGE]))
    march = _index(
        march_rows,
        projection.SOURCE_VINTAGE,
        projection.TRANSFORMATION,
    )
    june = _index(
        june_rows,
        projection.JUNE_SOURCE_VINTAGE,
        projection.JUNE_TRANSFORMATION,
    )
    overlap = sorted(march.keys() & june.keys())
    _require(len(overlap) == _OVERLAP_COUNT)
    _require(set(march) <= set(june) and len(june) == len(march) + 1)

    changes: list[dict[str, str]] = []
    unchanged: list[str] = []
    for token in overlap:
        old, new = march[token], june[token]
        _require(old["unit"] == new["unit"])
        _require(old["source_label"] == new["source_label"])
        _require(old["valid_time_start"] == new["valid_time_start"])
        _require(old["valid_time_end"] == new["valid_time_end"])
        old_amount, new_amount = old["amount"], new["amount"]
        if old_amount == new_amount:
            unchanged.append(token)
        else:
            changes.append(
                {
                    "period_token": token,
                    "march_value": str(old_amount),
                    "june_value": str(new_amount),
                    "delta": str(new_amount - old_amount),
                }
            )

    comparison_bytes = json.dumps(
        changes, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "schema_version": "archive-govt-nz.health-gdp-vintage-comparison/v1",
        "status": "verified_source_vintage_comparison",
        "march_source_vintage": projection.SOURCE_VINTAGE,
        "june_source_vintage": projection.JUNE_SOURCE_VINTAGE,
        "march_source_sha256": projection.SOURCE_SHA256,
        "june_source_sha256": projection.JUNE_SOURCE_SHA256,
        "march_transformation_id": projection.TRANSFORMATION,
        "june_transformation_id": projection.JUNE_TRANSFORMATION,
        "march_period_count": len(march),
        "june_period_count": len(june),
        "overlap_count": len(overlap),
        "unchanged_period_count": len(unchanged),
        "changed_period_count": len(changes),
        "changed_period_tokens": [row["period_token"] for row in changes],
        "difference_payload_sha256": hashlib.sha256(comparison_bytes).hexdigest(),
        "comparison_basis": "exact canonical Decimal values in matching period tokens",
        "difference_interpretation": "not_assessed",
        "currency": "unresolved",
        "rights_state": "not_evaluated",
        "denominator_selection": "not_performed",
        "analytical_admission": "not_performed",
        "publication": "not_performed",
    }
