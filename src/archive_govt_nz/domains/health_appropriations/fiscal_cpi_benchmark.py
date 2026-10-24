"""Source-qualified household CPI benchmark with explicit fiscal averaging."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    cpi_canonical_projection as cpi,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_share_analysis as fiscal,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
        CanonicalPackageInput,
    )

FORMULA_POLICY = "fiscal-2025-cpi2026q2-equal-quarter-FY2025/v1"
CPI_DEFINITION_SHA256 = (
    "41762ffc6eedc186942f15c83101c56aea33b64fd3f236cede1b17502c546594"
)
CPI_DEFINITION_URL = "https://datainfoplus.stats.govt.nz/item/nz.govt.stats/4fb499ed-5453-4a7f-bb87-5a3835184f79"
BENCHMARK_START = date(2024, 7, 1)
BENCHMARK_END = date(2025, 6, 30)
_CONTEXT = Context(prec=80, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("1e-12")
_ERROR = "fiscal_cpi_benchmark_invalid"
_QUARTERS = 4
_FIRST_HEALTH = 1972
_LAST_HEALTH = 2025
_FIRST_JUNE = 1990
_MARCH = 3
_MAX_HEALTH = 54
_MAX_CPI = 500
_GST_INCLUSIVE_YEARS = range(1987, 1994)
_REFERENCE_END = date(2017, 6, 30)
_REFERENCE_VALUE = Decimal(1000)
SCHEMA = pa.schema(
    [
        ("measure", pa.string()),
        ("period_start", pa.date32()),
        ("period_end", pa.date32()),
        ("numerator_id", pa.string()),
        ("numerator_source_time_status", pa.string()),
        ("health_source_sha256", pa.string()),
        ("health_vintage", pa.string()),
        ("cpi_source_sha256", pa.string()),
        ("cpi_vintage", pa.string()),
        ("nominal_amount_millions", pa.decimal128(38, 18)),
        ("period_cpi_ids", pa.list_(pa.field("element", pa.string()))),
        ("period_cpi_source_time_statuses", pa.list_(pa.field("element", pa.string()))),
        ("period_cpi_mean", pa.decimal128(38, 20)),
        ("benchmark_period_start", pa.date32()),
        ("benchmark_period_end", pa.date32()),
        ("benchmark_cpi_ids", pa.list_(pa.field("element", pa.string()))),
        (
            "benchmark_cpi_source_time_statuses",
            pa.list_(pa.field("element", pa.string())),
        ),
        ("benchmark_cpi_mean", pa.decimal128(38, 20)),
        ("cpi_benchmark_millions", pa.decimal128(38, 12)),
        ("unit", pa.string()),
        ("accounting_basis", pa.string()),
        ("numerator_coverage", pa.string()),
        ("numerator_gst_basis", pa.string()),
        ("fiscal_source_quality_flags", pa.list_(pa.field("element", pa.string()))),
        ("cpi_source_quality_flags", pa.list_(pa.field("element", pa.string()))),
        ("fiscal_period_evidence_sha256", pa.string()),
        ("cpi_definition_evidence_sha256", pa.string()),
        ("formula_policy", pa.string()),
        ("status", pa.string()),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.fiscal-health-cpi-benchmark/v1",
        b"weighting": b"four_quarter_index_levels_equal_weight",
        b"scope": (
            b"household_CPI_benchmark_not_health_input_costs_GST_effects_retained"
        ),
    },
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def quarter_ends(start: date) -> list[date]:
    """Return four complete calendar quarters beginning at a quarter boundary."""
    _require(type(start) is date and start.day == 1 and start.month in (1, 4, 7, 10))
    result = []
    for offset in range(_QUARTERS):
        month_number = start.month - 1 + _MARCH * offset
        year = start.year + month_number // 12
        month = month_number % 12 + _MARCH
        result.append(date(year, month, 31 if month in (3, 12) else 30))
    return result


def _index_key(row: dict[str, Any]) -> date:
    end = row["valid_time_end"]
    amount = row["amount"]
    _require(
        type(end) is date
        and end.month in (3, 6, 9, 12)
        and end.day == (31 if end.month in (3, 12) else 30)
        and row["valid_time_start"] == date(end.year, end.month - 2, 1)
        and row["valid_time_status"] == "source_quarter_ended"
        and row["source_object_sha256"] == cpi.SOURCE_SHA256
        and row["source_vintage"] == cpi.SOURCE_VINTAGE
        and row["measure"] == "consumer_price_index_all_groups"
        and row["unit"] == "Index"
        and type(row["record_id"]) is str
        and bool(row["record_id"])
    )
    if amount is not None:
        _require(
            isinstance(amount, Decimal)
            and amount.is_finite()
            and amount.copy_abs() < Decimal("1e15")
            and amount == amount.quantize(Decimal("1e-18"), context=_CONTEXT)
        )
    return end


def _health_end(row: dict[str, Any]) -> date:
    end = row["period_end"]
    amount = row["numerator_amount"]
    _require(type(end) is date and _FIRST_HEALTH <= end.year <= _LAST_HEALTH)
    _require(
        end
        == (date(end.year, 3, 31) if end.year < _FIRST_JUNE else date(end.year, 6, 30))
    )
    _require(
        row["period_start"] == date(end.year - 1, 4 if end.month == _MARCH else 7, 1)
    )
    _require(
        row["source_object_sha256"] == fiscal.SOURCE_SHA256
        and row["source_vintage"] == fiscal.VINTAGE
        and row["measure"] == "health_share_gdp"
        and row["formula_policy"] == fiscal.FORMULA_POLICY
        and row["period_definition_evidence_sha256"] == fiscal.PERIOD_EVIDENCE_SHA256
        and row["numerator_source_time_status"] == "end_known_start_unknown"
        and type(row["numerator_id"]) is str
        and bool(row["numerator_id"])
        and isinstance(amount, Decimal)
        and amount.is_finite()
        and amount.copy_abs() < Decimal("1e20")
        and amount == amount.quantize(Decimal("1e-18"), context=_CONTEXT)
    )
    return end


def _mean(rows: list[dict[str, Any] | None]) -> tuple[str, Decimal | None]:
    if any(row is None or row["amount"] is None for row in rows):
        return "missing", None
    amounts = [row["amount"] for row in rows if row is not None]
    if any(amount <= 0 for amount in amounts):
        return "nonpositive", None
    with localcontext(_CONTEXT):
        return "available", sum(amounts, Decimal(0)) / _QUARTERS


def _value(
    amount: Decimal,
    period: tuple[str, Decimal | None],
    benchmark: tuple[str, Decimal | None],
) -> tuple[str, Decimal | None]:
    for role, value in (("benchmark", benchmark), ("period", period)):
        if value[0] != "available":
            return f"{value[0]}_{role}_cpi", None
    if amount < 0:
        return "negative_numerator", None
    _require(period[1] is not None and benchmark[1] is not None)
    with localcontext(_CONTEXT):
        result = (
            amount * cast("Decimal", benchmark[1]) / cast("Decimal", period[1])
        ).quantize(_QUANTUM)
    if result.copy_abs() >= Decimal("1e26"):
        return "unrepresentable_benchmark", None
    return "calculated", result


def derive_fiscal_cpi_benchmark(
    qualified_health: list[dict[str, Any]], indexes: list[dict[str, Any]]
) -> pa.Table:
    """Calculate qualified rows; callers verify packages and definition evidence.

    Equal-quarter averaging is this local policy, not a publisher annual series.
    The benchmark preserves GST effects and historical CPI-method changes; it
    does not estimate health input costs or repair original reporting breaks.
    """
    _require(len(qualified_health) <= _MAX_HEALTH and len(indexes) <= _MAX_CPI)
    indexed: dict[date, dict[str, Any]] = {}
    ids: set[str] = set()
    for row in indexes:
        end = _index_key(row)
        _require(end not in indexed and row["record_id"] not in ids)
        indexed[end] = row
        ids.add(row["record_id"])
    benchmark_rows = [indexed.get(end) for end in quarter_ends(BENCHMARK_START)]
    benchmark_mean = _mean(benchmark_rows)
    seen: set[date] = set()
    result = []
    for row in qualified_health:
        end = _health_end(row)
        _require(end not in seen and row["numerator_id"] not in ids)
        seen.add(end)
        ids.add(row["numerator_id"])
        period_rows = [indexed.get(end) for end in quarter_ends(row["period_start"])]
        period_mean = _mean(period_rows)
        status, value = _value(row["numerator_amount"], period_mean, benchmark_mean)
        result.append(
            {
                "measure": "health_spending_household_cpi_benchmark",
                "period_start": row["period_start"],
                "period_end": end,
                "numerator_id": row["numerator_id"],
                "numerator_source_time_status": row["numerator_source_time_status"],
                "health_source_sha256": fiscal.SOURCE_SHA256,
                "health_vintage": fiscal.VINTAGE,
                "cpi_source_sha256": cpi.SOURCE_SHA256,
                "cpi_vintage": cpi.SOURCE_VINTAGE,
                "nominal_amount_millions": row["numerator_amount"],
                "period_cpi_ids": [
                    item["record_id"] if item else None for item in period_rows
                ],
                "period_cpi_source_time_statuses": [
                    item["valid_time_status"] if item else None for item in period_rows
                ],
                "period_cpi_mean": period_mean[1],
                "benchmark_period_start": BENCHMARK_START,
                "benchmark_period_end": BENCHMARK_END,
                "benchmark_cpi_ids": [
                    item["record_id"] if item else None for item in benchmark_rows
                ],
                "benchmark_cpi_source_time_statuses": [
                    item["valid_time_status"] if item else None
                    for item in benchmark_rows
                ],
                "benchmark_cpi_mean": benchmark_mean[1],
                "cpi_benchmark_millions": value,
                "unit": "source_millions_at_FY2025_household_CPI_benchmark",
                "accounting_basis": row["accounting_basis"],
                "numerator_coverage": row["numerator_coverage"],
                "numerator_gst_basis": "inclusive"
                if end.year in _GST_INCLUSIVE_YEARS
                else "exclusive",
                "fiscal_source_quality_flags": row["source_quality_flags"],
                "cpi_source_quality_flags": sorted(
                    {
                        flag
                        for item in [*period_rows, *benchmark_rows]
                        if item
                        for flag in item["quality_flags"]
                    }
                ),
                "fiscal_period_evidence_sha256": fiscal.PERIOD_EVIDENCE_SHA256,
                "cpi_definition_evidence_sha256": CPI_DEFINITION_SHA256,
                "formula_policy": FORMULA_POLICY,
                "status": status,
            }
        )
    return pa.Table.from_pylist(
        sorted(result, key=lambda item: item["period_end"]), schema=SCHEMA
    )


@dataclass(frozen=True)
class CpiInput:
    """Bind one pinned CPI Silver package to its Bronze CAS."""

    silver_root: Path
    manifest_sha256: str
    cas_root: Path


def query_fiscal_cpi_benchmark(
    package: CanonicalPackageInput,
    *,
    fiscal_period_evidence: Path,
    cpi_definition_evidence: Path,
    cpi_input: CpiInput,
) -> tuple[pa.Table, dict[str, Any]]:
    """Verify exact inputs and metadata, then derive a local consumer benchmark."""
    _require(
        not cpi_definition_evidence.is_symlink() and cpi_definition_evidence.is_file()
    )
    _require(
        hashlib.sha256(cpi_definition_evidence.read_bytes()).hexdigest()
        == CPI_DEFINITION_SHA256
    )
    shares, fiscal_receipt = fiscal.query_fiscal_health_shares(
        package, period_evidence=fiscal_period_evidence
    )
    indexes, _lineage, cpi_receipt = cpi.project_cpi(
        cpi_input.silver_root, cpi_input.manifest_sha256, cpi_input.cas_root
    )
    rows = indexes.to_pylist()
    reference = [row for row in rows if row["valid_time_end"] == _REFERENCE_END]
    _require(len(reference) == 1 and reference[0]["amount"] == _REFERENCE_VALUE)
    table = derive_fiscal_cpi_benchmark(
        [row for row in shares.to_pylist() if row["measure"] == "health_share_gdp"],
        rows,
    )
    return table, {
        "schema_version": "archive-govt-nz.fiscal-health-cpi-benchmark/v1",
        "formula_policy": FORMULA_POLICY,
        "fiscal_input": fiscal_receipt,
        "cpi_input": cpi_receipt,
        "cpi_definition_evidence_sha256": CPI_DEFINITION_SHA256,
        "cpi_definition_url": CPI_DEFINITION_URL,
        "evidence_kind": "retained_web_tool_text_observation",
        "index_reference_qualification": (
            "official_metadata_2017Q2_1000_and_source_point_match"
        ),
        "weighting": "equal_weight_four_complete_quarters",
        "benchmark_period": {"start": str(BENCHMARK_START), "end": str(BENCHMARK_END)},
        "cross_vintage_policy": "explicit_pinned_fiscal2025_cpi2026q2_pair",
        "gst_effects": "not_removed",
        "historical_seasonal_component_changes": "not_removed",
        "health_input_cost_deflator": "not_asserted",
        "rounding": "decimal80_half_even_millions_12dp",
        "counts": dict(sorted(Counter(table["status"].to_pylist()).items())),
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
