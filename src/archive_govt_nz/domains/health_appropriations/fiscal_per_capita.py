"""Explicit Fiscal 2025 spending / annual June mean resident population policy."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    fiscal_share_analysis as fiscal,
)
from archive_govt_nz.domains.health_appropriations import (
    population_annual_canonical_projection as population,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
        CanonicalPackageInput,
    )

FORMULA_POLICY = "fiscal-2025-population-20260818-june-mean/v1"
POPULATION_PERIOD_EVIDENCE_SHA256 = (
    "431274ff6064c04ea74f7cd8f6e2ab0c0dfa025a0bc3e72ad1aa3adf97c5c967"
)
POPULATION_PERIOD_URL = (
    "https://datainfoplus.stats.govt.nz/item/nz.govt.stats/"
    "4c9f3523-5386-4ce0-a8bd-993bb905f119/201"
)
_CONTEXT = Context(prec=80, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("1e-12")
_FIRST_YEAR = 1991
_LAST_YEAR = 2026
_ERROR = "fiscal_per_capita_invalid"
_JUNE = 6
_HEALTH_FIRST_YEAR = 1972
_HEALTH_LAST_YEAR = 2025
_FIRST_JUNE_YEAR = 1990
_MARCH = 3
_MAX_HEALTH = 54
_MAX_POPULATION = 36
_MILLION = Decimal(1000000)
SCHEMA = pa.schema(
    [
        ("measure", pa.string()),
        ("period_start", pa.date32()),
        ("period_end", pa.date32()),
        ("numerator_id", pa.string()),
        ("population_id", pa.string()),
        ("health_source_sha256", pa.string()),
        ("health_vintage", pa.string()),
        ("population_source_sha256", pa.string()),
        ("population_vintage", pa.string()),
        ("health_amount_millions", pa.decimal128(38, 18)),
        ("mean_population", pa.decimal128(38, 18)),
        ("source_dollars_per_mean_resident", pa.decimal128(38, 12)),
        ("unit", pa.string()),
        ("accounting_basis", pa.string()),
        ("numerator_coverage", pa.string()),
        ("fiscal_source_quality_flags", pa.list_(pa.field("element", pa.string()))),
        ("population_source_quality_flags", pa.list_(pa.field("element", pa.string()))),
        ("fiscal_period_evidence_sha256", pa.string()),
        ("population_period_evidence_sha256", pa.string()),
        ("formula_policy", pa.string()),
        ("status", pa.string()),
    ],
    metadata={b"schema_version": b"archive-govt-nz.fiscal-health-per-capita/v1"},
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _population_key(row: dict[str, Any]) -> tuple[date, date]:
    end = row["valid_time_end"]
    start = row["valid_time_start"]
    amount = row["amount"]
    _require(
        type(end) is date
        and _FIRST_YEAR <= end.year <= _LAST_YEAR
        and end == date(end.year, 6, 30)
        and start == date(end.year - 1, 7, 1)
        and row["source_object_sha256"] == population.SOURCE_SHA256
        and row["source_vintage"] == population.SOURCE_VINTAGE
        and row["measure"] == "estimated_resident_population_mean_year_ended"
        and row["source_label"] == "Total All Ages"
        and row["unit"] == "persons"
        and row["period_token"] == f"FY{end.year}"
        and row["valid_time_status"] == "source_mean_year_ended"
        and type(row["record_id"]) is str
        and bool(row["record_id"])
    )
    if amount is not None:
        _require(
            isinstance(amount, Decimal)
            and amount.is_finite()
            and amount.copy_abs() < Decimal("1e12")
            and amount == amount.to_integral_value()
        )
    return start, end


def _rate(
    row: dict[str, Any], resident: dict[str, Any] | None
) -> tuple[str, Decimal | None]:
    if row["period_end"].month != _JUNE:
        return "unsupported_march_period", None
    if resident is None or resident["amount"] is None:
        return "missing_population", None
    if resident["amount"] <= 0:
        return "nonpositive_population", None
    if row["numerator_amount"] < 0:
        return "negative_numerator", None
    with localcontext(_CONTEXT):
        rate = (row["numerator_amount"] * _MILLION / resident["amount"]).quantize(
            _QUANTUM
        )
    return "calculated", rate


def derive_fiscal_per_capita(
    qualified_health: list[dict[str, Any]], residents: list[dict[str, Any]]
) -> pa.Table:
    """Calculate qualified rows; callers must verify packages and period evidence."""
    _require(len(qualified_health) <= _MAX_HEALTH and len(residents) <= _MAX_POPULATION)
    indexed: dict[tuple[date, date], dict[str, Any]] = {}
    ids: set[str] = set()
    for row in residents:
        key = _population_key(row)
        _require(key not in indexed and row["record_id"] not in ids)
        indexed[key] = row
        ids.add(row["record_id"])
    result = []
    periods: set[date] = set()
    for row in qualified_health:
        end = row["period_end"]
        amount = row["numerator_amount"]
        _require(
            type(end) is date
            and _HEALTH_FIRST_YEAR <= end.year <= _HEALTH_LAST_YEAR
            and type(row["numerator_id"]) is str
            and bool(row["numerator_id"])
        )
        _require(
            row["source_object_sha256"] == fiscal.SOURCE_SHA256
            and row["source_vintage"] == fiscal.VINTAGE
            and row["measure"] == "health_share_gdp"
            and row["formula_policy"] == fiscal.FORMULA_POLICY
            and row["period_definition_evidence_sha256"]
            == fiscal.PERIOD_EVIDENCE_SHA256
            and row["numerator_id"] not in ids
            and end not in periods
            and isinstance(amount, Decimal)
            and amount.is_finite()
            and amount.copy_abs() < Decimal("1e20")
            and amount == amount.quantize(Decimal("1e-18"), context=_CONTEXT)
        )
        _require(
            end
            == (
                date(end.year, 3, 31)
                if end.year < _FIRST_JUNE_YEAR
                else date(end.year, 6, 30)
            )
        )
        _require(
            row["period_start"]
            == date(end.year - 1, 4 if end.month == _MARCH else 7, 1)
        )
        ids.add(row["numerator_id"])
        periods.add(end)
        resident = indexed.get((row["period_start"], row["period_end"]))
        status, rate = _rate(row, resident)
        result.append(
            {
                "measure": "health_spending_per_mean_resident",
                "period_start": row["period_start"],
                "period_end": row["period_end"],
                "numerator_id": row["numerator_id"],
                "population_id": resident["record_id"] if resident else None,
                "health_source_sha256": fiscal.SOURCE_SHA256,
                "health_vintage": fiscal.VINTAGE,
                "population_source_sha256": population.SOURCE_SHA256,
                "population_vintage": population.SOURCE_VINTAGE,
                "health_amount_millions": row["numerator_amount"],
                "mean_population": resident["amount"] if resident else None,
                "source_dollars_per_mean_resident": rate,
                "unit": "source_dollars_per_mean_resident",
                "accounting_basis": row["accounting_basis"],
                "numerator_coverage": row["numerator_coverage"],
                "fiscal_source_quality_flags": row["source_quality_flags"],
                "population_source_quality_flags": resident["quality_flags"]
                if resident
                else [],
                "fiscal_period_evidence_sha256": fiscal.PERIOD_EVIDENCE_SHA256,
                "population_period_evidence_sha256": POPULATION_PERIOD_EVIDENCE_SHA256,
                "formula_policy": FORMULA_POLICY,
                "status": status,
            }
        )
    return pa.Table.from_pylist(
        sorted(result, key=lambda row: row["period_end"]), schema=SCHEMA
    )


@dataclass(frozen=True)
class PopulationInput:
    """Bind an explicit population Silver package to its Bronze CAS."""

    silver_root: Path
    manifest_sha256: str
    cas_root: Path


def query_fiscal_per_capita(
    package: CanonicalPackageInput,
    *,
    fiscal_period_evidence: Path,
    population_period_evidence: Path,
    population_input: PopulationInput,
) -> tuple[pa.Table, dict[str, Any]]:
    """Select this exact source pair locally; retain both vintages and flags.

    This is a derived nominal spending rate, not an individual's health cost.
    It does not assert an ISO currency, uniform census base, licensing or
    publication. Revised population estimates are an explicit policy input.
    """
    _require(
        not population_period_evidence.is_symlink()
        and population_period_evidence.is_file()
    )
    _require(
        hashlib.sha256(population_period_evidence.read_bytes()).hexdigest()
        == POPULATION_PERIOD_EVIDENCE_SHA256
    )
    shares, fiscal_receipt = fiscal.query_fiscal_health_shares(
        package, period_evidence=fiscal_period_evidence
    )
    residents, _lineage, population_receipt = population.project_population_annual(
        population_input.silver_root,
        population_input.manifest_sha256,
        population_input.cas_root,
    )
    health = [row for row in shares.to_pylist() if row["measure"] == "health_share_gdp"]
    table = derive_fiscal_per_capita(health, residents.to_pylist())
    return table, {
        "schema_version": "archive-govt-nz.fiscal-health-per-capita/v1",
        "formula_policy": FORMULA_POLICY,
        "fiscal_input": fiscal_receipt,
        "population_input": population_receipt,
        "population_period_source_url": POPULATION_PERIOD_URL,
        "population_period_evidence_sha256": POPULATION_PERIOD_EVIDENCE_SHA256,
        "evidence_kind": "retained_web_tool_text_observation",
        "denominator_selection": "exact_annual_june_mean_total_all_ages",
        "cross_vintage_policy": "explicit_pinned_fiscal2025_population20260818_pair",
        "rounding": "decimal80_half_even_source_dollars_12dp",
        "counts": dict(sorted(Counter(table["status"].to_pylist()).items())),
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
