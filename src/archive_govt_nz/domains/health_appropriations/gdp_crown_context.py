"""Source-bound GDP/Crown metadata and fail-closed native admission policy.

This is not a new workbook adapter. Hashes bind previously reviewed metadata
to originals. Only the GDP wrapper executes an existing numeric preflight;
Crown carrier observations never become facts or qualified formula results.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import gdp
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 1024 * 1024
SOURCE_PINS = {
    "stats": "a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21",
    "fiscal": "de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f",
    "befu": "313ee040abd9a332cc36245da5a0c2cb0d38fe2cedc013d731c1f12db463b0d1",
    "hyefu": "f9f9190a69ce0a7c53b89d690d50170e2a6a457e6821afeb93edc08cef4b9c7d",
}
_SOURCES = {
    "stats": (
        (
            "https://www.stats.govt.nz/assets/Uploads/Gross-domestic-product/"
            "Gross-domestic-product-March-2026-quarter/Download-data/"
            "gross-domestic-product-march-2026-quarter-current-price-income-and-expenditure.xlsx"
        ),
        "StatsNZ-GDP-2026Q1",
    ),
    "fiscal": (
        (
            "https://budget.govt.nz/budget/excel/fiscal-time-series/"
            "fiscaltimeseries1972-2025-year-end25.xlsx"
        ),
        "Fiscal-Time-Series-1972-2025",
    ),
    "befu": (
        "https://budget.govt.nz/budget/excel/befu2026/befu26-data-expense-tables.xlsx",
        "BEFU-2026",
    ),
    "hyefu": (
        "https://budget.govt.nz/budget/excel/hyefu2025/hyefu25-data-expense-tables.xlsx",
        "HYEFU-2025",
    ),
}
_PROFILES: dict[str, dict[str, Any]] = {
    "stats-gdp-2026q1": {
        "source": "stats",
        "family": "gdp",
        "series": "SNEQ / SG03AB01GE00S900 (separate publisher fields)",
        "selector": "Table 1!C27:BJ27",
        "count": 60,
        "label": "Gross domestic product - expenditure measure",
        "unit": "$(million)",
        "carrier": "literal_numeric",
        "periods": "2011Q2-2026Q1; quarter-ending dates; published 2026-06-18",
        "basis": "Actual current prices; Table 2 seasonally adjusted excluded",
        "amount_types": "actual_as_published",
        "gaps": [
            "native_preflight_required",
            "ISO_currency_unqualified",
            "annual_join_unselected",
        ],
    },
    "fiscal-gdp-2025": {
        "source": "fiscal",
        "family": "gdp",
        "series": "Nominal GDP!C3",
        "selector": "Nominal GDP!C5:C58",
        "count": 54,
        "label": "Nominal GDP",
        "unit": "$ millions",
        "carrier": "literal_numeric",
        "periods": "1972-1989 March years; 1990-2025 June years",
        "basis": (
            "nominal; no cross-vintage splicing; 2017-2024 revised versus 2024 edition"
        ),
        "amount_types": "historical_as_published; no explicit Actual/Forecast row",
        "gaps": [
            "native_package_semantic_qualification_separate",
            "native_NZD_millions_not_independent_currency_evidence",
            "period_transition_join_unselected",
        ],
    },
    "fiscal-core-2025": {
        "source": "fiscal",
        "family": "core_crown",
        "series": "Spending!D4",
        "selector": "Spending!D27:D58",
        "count": 32,
        "label": "Core Crown Expenses",
        "unit": "$ millions",
        "carrier": "literal_numeric",
        "periods": (
            "1994-2025 June years; old-GAAP inherits June basis from Spending!A23"
        ),
        "basis": "old-GAAP 1994-1996; IFRS 1997-2004; PBE Standards 2005-2025",
        "amount_types": "historical_as_published; no explicit Actual/Forecast row",
        "gaps": [
            "no_native_Crown_expense_adapter",
            "ISO_currency_unqualified",
            "cross_basis_and_consolidation_equivalence_unqualified",
        ],
    },
    "fiscal-total-2025": {
        "source": "fiscal",
        "family": "total_crown",
        "series": "Spending!E4",
        "selector": "Spending!E30:E58",
        "count": 29,
        "label": "Total Crown Expenses",
        "unit": "$ millions",
        "carrier": "literal_numeric",
        "periods": "1997-2025 June years",
        "basis": (
            "IFRS 1997-2004; PBE Standards 2005-2025; total-Crown restatements A64/A65"
        ),
        "amount_types": "historical_as_published; no explicit Actual/Forecast row",
        "gaps": [
            "no_native_Crown_expense_adapter",
            "ISO_currency_unqualified",
            "cross_basis_and_consolidation_equivalence_unqualified",
        ],
    },
    "befu-core-2026": {
        "source": "befu",
        "family": "core_crown",
        "series": "Core Crown Expense Tables!D26",
        "selector": "Core Crown Expense Tables!F26:O26",
        "count": 10,
        "label": "Core Crown expenses",
        "unit": "($millions)",
        "carrier": "formula_with_numeric_cache_presence_only",
        "periods": (
            "2021-2030; year F5:O5; type F6:O6; financial-year basis unqualified"
        ),
        "basis": "accounting and consolidation basis unqualified; not Health summary",
        "amount_types": "2021-2025 Actual; 2026-2030 Forecast",
        "gaps": [
            "formula_cache_freshness_and_value_unqualified",
            "no_native_Crown_total_adapter",
            "ISO_currency_and_period_basis_unqualified",
        ],
    },
    "hyefu-core-2025": {
        "source": "hyefu",
        "family": "core_crown",
        "series": "Core Crown Expense Tables!D25",
        "selector": "Core Crown Expense Tables!F25:O25",
        "count": 10,
        "label": "Core Crown expenses",
        "unit": "($millions)",
        "carrier": "formula_with_numeric_cache_presence_only",
        "periods": (
            "2021-2030; year F4:O4; type F5:O5; financial-year basis unqualified"
        ),
        "basis": "accounting and consolidation basis unqualified; not Health summary",
        "amount_types": "2021-2025 Actual; 2026-2030 Forecast",
        "gaps": [
            "formula_cache_freshness_and_value_unqualified",
            "no_native_Crown_total_adapter",
            "ISO_currency_and_period_basis_unqualified",
        ],
    },
}


def context_register() -> dict[str, Any]:
    """Return detached, deterministic metadata; never original values."""
    return {
        "schema_version": "archive-govt-nz.gdp-crown-context/v1",
        "profiles": [
            {
                "id": key,
                **copy.deepcopy(profile),
                "source_sha256": SOURCE_PINS[profile["source"]],
                "source_url": _SOURCES[profile["source"]][0],
                "source_vintage": _SOURCES[profile["source"]][1],
                "source_capture_observed_at": "2026-08-29T09:00:17Z",
                "currency": None,
                "rights": "not_evaluated",
                "analytical_selection": "not_selected",
            }
            for key, profile in _PROFILES.items()
        ],
    }


def _require(condition: object) -> None:
    if not condition:
        message = "gdp_crown_contract"
        raise ValueError(message)


def expected_gdp_receipt() -> dict[str, Any]:
    """Describe the native preflight contract, not proof of its execution."""
    context = source_context(
        SOURCE_PINS["stats"], *_SOURCES["stats"], "2026-08-29T09:00:17Z"
    )
    return {
        "schema_version": "archive-govt-nz.health-gdp-extraction/v1",
        "transformation_id": gdp.TRANSFORMATION,
        "status": "planned",
        **context,
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "currency": None,
        "counts": {"facts": 60, "lineage": 900, "dispositions": 2287},
    }


def qualify_context(
    profile_id: str,
    original: bytes,
    *,
    native_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure hash-bound metadata qualification; no workbook execution or writes.

    Matching a caller-supplied receipt is explicitly not execution attestation.
    Crown and historical GDP never inherit a quarterly-GDP or Health receipt.
    """
    _require(profile_id in _PROFILES)
    _require(type(original) is bytes and len(original) <= MAX_BYTES)
    profile = next(
        row for row in context_register()["profiles"] if row["id"] == profile_id
    )
    _require(hashlib.sha256(original).hexdigest() == profile["source_sha256"])
    admission = "not_admitted"
    if native_receipt is not None:
        _require(profile_id == "stats-gdp-2026q1")
        _require(
            json.dumps(native_receipt, sort_keys=True, allow_nan=False)
            == json.dumps(expected_gdp_receipt(), sort_keys=True, allow_nan=False)
        )
        admission = "native_receipt_matched"
    return {
        **profile,
        "context_qualification": "reviewed_metadata_hash_bound",
        "numeric_admission": admission,
        "native_receipt": copy.deepcopy(native_receipt),
        "receipt_evidence": "caller_supplied_not_execution_attestation",
        "promotion": "not_performed",
    }


def preflight_stats_gdp(source: Path, probe_output: Path) -> dict[str, Any]:
    """Execute the existing GDP adapter read-only, then qualify its receipt."""
    native = gdp.normalize_gdp(
        source,
        probe_output,
        expected_sha256=SOURCE_PINS["stats"],
        source_locator=_SOURCES["stats"][0],
        source_vintage=_SOURCES["stats"][1],
        observed_at="2026-08-29T09:00:17Z",
        dry_run=True,
    )
    payload = verified_snapshot(source, SOURCE_PINS["stats"], max_bytes=MAX_BYTES)
    result = qualify_context("stats-gdp-2026q1", payload, native_receipt=native)
    result["numeric_admission"] = "native_source_preflight_passed"
    result["receipt_evidence"] = "executed_read_only_existing_adapter"
    result["gaps"].remove("native_preflight_required")
    return result
