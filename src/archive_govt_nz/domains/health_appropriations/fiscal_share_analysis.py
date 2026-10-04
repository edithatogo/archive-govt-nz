"""Read-only, source-qualified Health shares within one Fiscal 2025 workbook."""

from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    fiscal_crown_canonical_projection,
)
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_SHA256,
    VINTAGE,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_verified_canonical_tables,
)

FORMULA_POLICY = "fiscal-2025-source-period-health-shares/v1"
PERIOD_EVIDENCE_URL = (
    "https://www.treasury.govt.nz/publications/information-release/"
    "data-fiscal-time-series-historical-fiscal-indicators"
)
_CONTEXT = Context(prec=80, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("1e-12")
_MAX_ROWS = 200
_FIRST_YEAR = 1972
_LAST_YEAR = 2025
_MARCH = 3
_FIRST_JUNE_YEAR = 1990
_FIRST_CORE_YEAR = 1994
_FIRST_TOTAL_YEAR = 1997
_FIRST_PBE_YEAR = 2005
_ERROR = "fiscal_share_input_invalid"
_DENOMINATORS = (
    ("nominal_gdp", "health_share_gdp", "domestic_economy"),
    ("core_crown_expenses", "health_share_core_crown", "core_crown"),
    ("total_crown_expenses", "health_share_total_crown", "total_crown"),
)
SHARE_SCHEMA = pa.schema(
    [
        ("measure", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_vintage", pa.string()),
        ("period_start", pa.date32()),
        ("period_end", pa.date32()),
        ("numerator_id", pa.string()),
        ("denominator_id", pa.string()),
        ("numerator_amount", pa.decimal128(38, 18)),
        ("denominator_amount", pa.decimal128(38, 18)),
        ("input_scale", pa.string()),
        ("numerator_coverage", pa.string()),
        ("denominator_coverage", pa.string()),
        ("accounting_basis", pa.string()),
        ("denominator_accounting_basis", pa.string()),
        ("percent", pa.decimal128(38, 12)),
        ("status", pa.string()),
        ("source_quality_flags", pa.list_(pa.field("element", pa.string()))),
        ("formula_policy", pa.string()),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.fiscal-health-shares/v1",
        b"period_rule": b"treasury-fiscal-1972-2025-March-June-years/v1",
    },
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _basis(year: int) -> str:
    if year < _FIRST_CORE_YEAR:
        return "Cash"
    if year < _FIRST_TOTAL_YEAR:
        return "old-GAAP"
    return "IFRS" if year < _FIRST_PBE_YEAR else "PBE Standards"


def _validate(row: dict[str, Any], measures: set[str]) -> tuple[date, str]:
    end = row["valid_time_end"]
    measure = row["measure"]
    amount = row["amount"]
    crown = measure in {"core_crown_expenses", "total_crown_expenses"}
    _require(
        row["source_object_sha256"] == SOURCE_SHA256
        and row["source_vintage"] == VINTAGE
        and measure in measures
        and type(row["record_id"]) is str
        and bool(row["record_id"])
        and type(end) is date
        and _FIRST_YEAR <= end.year <= _LAST_YEAR
        and row["unit"] == ("$ millions" if crown else "NZD_millions")
        and isinstance(amount, Decimal)
        and amount.is_finite()
        and amount.copy_abs() < Decimal("1e20")
    )
    expected = (
        date(end.year, 3, 31) if end.year < _FIRST_JUNE_YEAR else date(end.year, 6, 30)
    )
    _require(end == expected)
    _require(amount == amount.quantize(Decimal("1e-18"), context=_CONTEXT))
    if measure != "nominal_gdp":
        _require(row["accounting_basis"] == _basis(end.year))
    if crown:
        _require(
            end.year
            >= (
                _FIRST_CORE_YEAR
                if measure == "core_crown_expenses"
                else _FIRST_TOTAL_YEAR
            )
        )
    return end, measure


def _value(
    numerator: Decimal, denominator: dict[str, Any] | None
) -> tuple[str, Decimal | None]:
    if denominator is None:
        return "missing_denominator", None
    if numerator < 0:
        return "negative_numerator", None
    amount: Decimal = denominator["amount"]
    if amount <= 0:
        return "nonpositive_denominator", None
    with localcontext(_CONTEXT):
        percent = (numerator / amount * 100).quantize(_QUANTUM)
    if percent.copy_abs() >= Decimal("1e26"):
        return "unrepresentable_percentage", None
    return "calculated", percent


def derive_fiscal_health_shares(
    health: list[dict[str, Any]],
    gdp: list[dict[str, Any]],
    crowns: list[dict[str, Any]],
) -> pa.Table:
    """Pure arithmetic over qualified rows; callers must verify input packages.

    Dates follow Treasury's March/June fiscal-year definition for this exact
    workbook. Ratios use its shared dollar-million scale, so ISO currency is
    not inferred. Total Crown shares retain the core Health numerator scope;
    they are not total-Crown Health expenditure. Reporting bases are retained
    per observation and are never spliced or pooled across years or vintages.
    """
    _require(len(health) + len(gdp) + len(crowns) <= _MAX_ROWS)
    indexed: dict[tuple[date, str], dict[str, Any]] = {}
    ids: set[str] = set()
    for group, measures in (
        (health, {"health_spending"}),
        (gdp, {"nominal_gdp"}),
        (crowns, {"core_crown_expenses", "total_crown_expenses"}),
    ):
        for row in group:
            key = _validate(row, measures)
            _require(key not in indexed and row["record_id"] not in ids)
            indexed[key] = row
            ids.add(row["record_id"])
    results = []
    for row in sorted(health, key=lambda item: item["valid_time_end"]):
        end = row["valid_time_end"]
        start = date(end.year - 1, 4 if end.month == _MARCH else 7, 1)
        coverage = (
            "cash_health_function"
            if end.year < _FIRST_CORE_YEAR
            else "core_crown_health_function"
        )
        for denominator_measure, measure, denominator_coverage in _DENOMINATORS:
            denominator = indexed.get((end, denominator_measure))
            status, percent = _value(row["amount"], denominator)
            results.append(
                {
                    "measure": measure,
                    "source_object_sha256": SOURCE_SHA256,
                    "source_vintage": VINTAGE,
                    "period_start": start,
                    "period_end": end,
                    "numerator_id": row["record_id"],
                    "denominator_id": denominator["record_id"] if denominator else None,
                    "numerator_amount": row["amount"],
                    "denominator_amount": denominator["amount"]
                    if denominator
                    else None,
                    "input_scale": "same_source_dollar_millions",
                    "numerator_coverage": coverage,
                    "denominator_coverage": denominator_coverage,
                    "accounting_basis": row["accounting_basis"],
                    "denominator_accounting_basis": denominator["accounting_basis"]
                    if denominator
                    else None,
                    "percent": percent,
                    "status": status,
                    "source_quality_flags": sorted(
                        set(row["quality_flags"])
                        | set(denominator["quality_flags"] if denominator else [])
                    ),
                    "formula_policy": FORMULA_POLICY,
                }
            )
    return pa.Table.from_pylist(results, schema=SHARE_SCHEMA)


def query_fiscal_health_shares(
    package: CanonicalPackageInput,
) -> tuple[pa.Table, dict[str, Any]]:
    """Verify a historical canonical package and its exact original before use."""
    _require(package.kind == "historical")
    canonical, input_receipt = read_verified_canonical_tables(package)
    crowns, _lineage, crown_receipt = (
        fiscal_crown_canonical_projection.project_fiscal_crown(package.original)
    )
    table = derive_fiscal_health_shares(
        canonical["health_spending_fact"].to_pylist(),
        canonical["fiscal_context_fact"].to_pylist(),
        crowns.to_pylist(),
    )
    return table, {
        "schema_version": "archive-govt-nz.fiscal-health-shares/v1",
        "canonical_input": input_receipt,
        "crown_input": crown_receipt,
        "source_object_sha256": SOURCE_SHA256,
        "source_vintage": VINTAGE,
        "period_definition_source_url": PERIOD_EVIDENCE_URL,
        "formula_policy": FORMULA_POLICY,
        "rounding": "decimal80_half_even_percent_12dp",
        "counts": dict(sorted(Counter(table["status"].to_pylist()).items())),
        "rights": "not_evaluated",
        "publication": "not_performed",
        "cross_vintage_join": "not_performed",
    }
