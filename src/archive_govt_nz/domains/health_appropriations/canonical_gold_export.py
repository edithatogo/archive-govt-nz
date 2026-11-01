"""Exclusive local Gold derivatives from verified canonical history packages."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    biff8_canonical,
    crown_expense_canonical_projection,
    fiscal_crown_canonical_projection,
    hyefu_crown_expense_canonical_projection,
    moh_indicators,
    pharmac,
    pharmac_canonical_projection,
)
from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    NOMINAL_BUDGET_SCHEMA,
    NOMINAL_REVENUE_SCHEMA,
    query_historical_observations,
    query_nominal_budget,
    query_nominal_revenue,
    summarize_historical_coverage,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (
    build_discrete_plots,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_verification import (
    MAX_MANIFEST_BYTES,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_verified_canonical_tables,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    MohGoldInput,
    project_moh_indicators,
    read_verified_moh_tables,
)
from archive_govt_nz.domains.health_appropriations.pharmac_canonical_projection import (
    project_pharmac_cpb,
    read_verified_pharmac_tables,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

MAX_OUTPUT_BYTES = 128 * 1024 * 1024
MAX_PACKAGES = 32
MIN_DISTINCT_CLASSIFICATION_LABELS = 2
MIN_REVISION_VINTAGES = 2
MIN_OVERLAP_PRODUCTS = 2
_PRODUCT_REVISION_WITNESS_FIELDS = {
    "biff8_budget": ("canonical_stored_integer", "numeric_evidence_id"),
    "biff8_revenue": ("canonical_stored_integer", "numeric_evidence_id"),
}
SCHEMA = "archive-govt-nz.health-canonical-gold/v2"
_CROWN_RECONCILIATION_SCHEMA = (
    "archive-govt-nz.health-crown-projection-gold-reconciliation/v1"
)


@dataclass(frozen=True)
class PharmacGoldInput:
    """Explicit verified Pharmac canonical projection and Bronze CAS binding."""

    root: Path
    manifest_sha256: str
    source_cas_root: Path
    source_sha256: str


@dataclass(frozen=True)
class CrownGoldInput:
    """Pinned BEFU and HYEFU Silver inputs with a shared immutable Bronze CAS."""

    befu_root: Path
    befu_manifest_sha256: str
    hyefu_root: Path
    hyefu_manifest_sha256: str
    source_cas_root: Path


@dataclass(frozen=True)
class FiscalCrownGoldInput:
    """Pinned Bronze source for the historical Fiscal Crown projection."""

    source_path: Path


@dataclass(frozen=True)
class GoldInputs:
    """Optional source-bound domain inputs included in one Gold build."""

    pharmac: PharmacGoldInput | None = None
    moh: MohGoldInput | None = None
    crown: CrownGoldInput | None = None
    fiscal_crown: FiscalCrownGoldInput | None = None


EMPTY_GOLD_INPUTS = GoldInputs()


_CROWN_FACT_ROWS = 10
_CROWN_LINEAGE_ROWS = 80
_FISCAL_CROWN_FACT_ROWS = 61
_FISCAL_CROWN_LINEAGE_ROWS = 671
_FISCAL_CORE_ROWS = 32
_FISCAL_TOTAL_ROWS = 29

_TABLES = {
    "historical_observations.parquet": "observations",
    "historical_coverage.parquet": "coverage",
    "nominal_budget.parquet": "budget",
    "nominal_revenue.parquet": "revenue",
    "canonical_input_lineage.parquet": "canonical_input_lineage",
    "biff8_budget.parquet": "biff8_budget",
    "biff8_budget_lineage.parquet": "biff8_budget_lineage",
    "biff8_budget_numeric.parquet": "biff8_budget_numeric",
    "biff8_revenue.parquet": "biff8_revenue",
    "biff8_revenue_lineage.parquet": "biff8_revenue_lineage",
    "biff8_revenue_numeric.parquet": "biff8_revenue_numeric",
    "nominal_pharmaceutical_budget.parquet": "pharmac",
    "pharmaceutical_budget_lineage.parquet": "pharmac_lineage",
    "published_health_indicators.parquet": "moh",
    "published_health_indicator_lineage.parquet": "moh_lineage",
    "crown_expense_befu_2026.parquet": "crown_befu",
    "crown_expense_befu_2026_lineage.parquet": "crown_befu_lineage",
    "crown_expense_hyefu_2025.parquet": "crown_hyefu",
    "crown_expense_hyefu_2025_lineage.parquet": "crown_hyefu_lineage",
    "historical_fiscal_crown.parquet": "fiscal_crown",
    "historical_fiscal_crown_lineage.parquet": "fiscal_crown_lineage",
}


def _require(condition: object) -> None:
    if not condition:
        message = "canonical_gold_export_invalid"
        raise ValueError(message)


def _encoded(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _table_bytes(table: pa.Table) -> bytes:
    buffer = BytesIO()
    pq.write_table(
        table, buffer, compression="zstd", use_dictionary=False, version="2.6"
    )
    return buffer.getvalue()


def _ro_crate_metadata(payloads: dict[str, bytes]) -> dict[str, Any]:
    """Describe actual Gold payload bytes without licensing or publication claims."""
    parts: list[dict[str, str]] = []
    files: list[dict[str, Any]] = []
    for name, payload in sorted(payloads.items()):
        if name.endswith(".parquet"):
            media_type = "application/vnd.apache.parquet"
        elif name.endswith(".png"):
            media_type = "image/png"
        elif name.endswith(".json"):
            media_type = "application/json"
        else:
            _require(name.endswith(".md"))
            media_type = "text/markdown"
        parts.append({"@id": name})
        files.append(
            {
                "@id": name,
                "@type": "File",
                "contentSize": len(payload),
                "encodingFormat": media_type,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Health Appropriations canonical Gold local package",
                "description": (
                    "A source-separated local analytical derivative. Inclusion "
                    "in this inventory does not evaluate rights or perform publication."
                ),
                "version": SCHEMA,
                "hasPart": parts,
            },
            *files,
        ],
    }


def _dataset_card(
    products: dict[str, dict[str, Any]],
    temporal_report: dict[str, Any],
    package_markers: list[str],
) -> bytes:
    rows = [
        "# Health Appropriations canonical Gold dataset card",
        "",
        "This local derivative preserves source-separated products. It does not",
        "assess analytical completeness, establish rights, or perform publication.",
        "",
        "## Products",
        "",
        "| Product | Input records | Output rows | Exact-context temporal groups |",
        "| --- | ---: | ---: | ---: |",
    ]
    groups = temporal_report["groups"]
    for name, details in sorted(products.items()):
        row_count = details.get("observation_rows", details.get("output_rows", 0))
        output_names = {
            "historical": "historical_observations.parquet",
            "budget": "nominal_budget.parquet",
            "revenue": "nominal_revenue.parquet",
            "biff8_budget": "biff8_budget.parquet",
            "biff8_revenue": "biff8_revenue.parquet",
            "pharmac": "nominal_pharmaceutical_budget.parquet",
            "moh": "published_health_indicators.parquet",
            "crown_befu": "crown_expense_befu_2026.parquet",
            "crown_hyefu": "crown_expense_hyefu_2025.parquet",
            "fiscal_crown": "historical_fiscal_crown.parquet",
        }
        group_count = sum(
            group["output_name"] == output_names[name] for group in groups
        )
        rows.append(
            f"| {name} | {details['input_records']} | {row_count} | {group_count} |"
        )
    rows.extend(
        [
            "",
            "## Input package marker SHA-256 pins",
            "",
            *[f"- `{marker}`" for marker in sorted(package_markers)],
            "",
            "## Assessment boundaries",
            "",
            "- Analytical completeness: not evaluated.",
            "- Source health: unresolved.",
            "- Budget/revenue label-change candidates: observed only;",
            "  mapping not inferred.",
            "- Other classification drift: unresolved.",
            "- Historical revision candidates are observed only; reasons for change",
            "  are not assessed.",
            "- Full revision reconciliation: unresolved.",
            "- Cross-source reconciliation: not performed.",
            "- Rights: not evaluated.",
            "- Publication: not performed.",
            "",
        ]
    )
    return "\n".join(rows).encode("utf-8")


def _quality_report(
    tables: dict[str, pa.Table], product_report: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Reconcile input identity coverage without asserting analytical completeness."""
    lineage: dict[str, list[str]] = {}
    for product, table_name in (
        ("historical", "observations"),
        ("historical", "coverage"),
        ("budget", "budget"),
        ("revenue", "revenue"),
        ("biff8_budget", "biff8_budget"),
        ("biff8_revenue", "biff8_revenue"),
        ("pharmac", "pharmac"),
        ("moh", "moh"),
        ("crown_befu", "crown_befu"),
        ("crown_hyefu", "crown_hyefu"),
        ("fiscal_crown", "fiscal_crown"),
    ):
        table = tables.get(table_name)
        if table is None:
            continue
        for row in table.to_pylist():
            ids = row.get("input_record_ids")
            if ids is None:
                record_id = row.get("input_record_id")
                if record_id is None:
                    record_id = row.get("record_id")
                ids = [record_id]
            for record_id in ids:
                _require(type(record_id) is str and bool(record_id))
                lineage.setdefault(record_id, []).append(product)
    return {
        "schema_version": "archive-govt-nz.health-canonical-gold-quality/v1",
        "input_record_count": len(lineage),
        "input_records_with_product": len(lineage),
        "unaccounted_input_records": 0,
        "products": {
            name: {
                "output_rows": details.get(
                    "observation_rows",
                    details.get("output_rows", 0),
                ),
                "input_record_count": details["input_records"],
                "cross_source_join": "not_performed",
                "vintage_pooling": "not_performed",
                "analytical_completeness": "not_evaluated",
            }
            for name, details in sorted(product_report.items())
        },
        "input_record_products": {
            record_id: sorted(set(products))
            for record_id, products in sorted(lineage.items())
        },
        "unresolved_reports": [
            "source_health",
            "revision_reconciliation",
            "cross_source_reconciliation",
        ],
    }


_BUDGET_RECONCILIATION_FIELDS = (
    "source_vintage",
    "period_token",
    "amount_type",
    "unit",
    "vote",
    "department",
    "portfolio",
    "source_label",
)
_REVENUE_RECONCILIATION_FIELDS = (
    "source_vintage",
    "period_token",
    "amount_type",
    "unit",
    "vote",
    "department",
    "revenue_type",
    "source_label",
)
_PHARMAC_RECONCILIATION_FIELDS = (
    "source_vintage",
    "period_token",
    "amount_type",
    "unit",
    "source_label",
    "funding_regime",
)


def build_budget_input_total_reconciliation(
    packages: tuple[CanonicalPackageInput, ...], gold: pa.Table
) -> dict[str, Any]:
    """Tie Budget Gold totals to their exact pinned canonical input records."""
    _require(
        isinstance(packages, tuple)
        and 0 < len(packages) <= MAX_PACKAGES
        and all(package.kind == "budget" for package in packages)
        and gold.schema.equals(NOMINAL_BUDGET_SCHEMA, check_metadata=True)
    )
    source: dict[str, dict[str, Any]] = {}
    package_markers: list[str] = []
    for package in packages:
        canonical, receipt = read_verified_canonical_tables(package)
        facts = canonical["appropriation_fact"]
        package_markers.append(receipt["marker_sha256"])
        for row in facts.to_pylist():
            record_id = row["record_id"]
            _require(
                type(record_id) is str and bool(record_id) and record_id not in source
            )
            _require(isinstance(row["amount"], Decimal) and row["amount"].is_finite())
            source[record_id] = row

    rows = []
    consumed: set[str] = set()
    for output in gold.to_pylist():
        ids = output["input_record_ids"]
        _require(
            isinstance(ids, list)
            and bool(ids)
            and ids == sorted(set(ids))
            and not consumed.intersection(ids)
        )
        selected = [source.get(record_id) for record_id in ids]
        _require(all(row is not None for row in selected))
        inputs = [row for row in selected if row is not None]
        _require(
            all(
                all(
                    row[field] == output[field]
                    for field in _BUDGET_RECONCILIATION_FIELDS
                )
                for row in inputs
            )
        )
        with localcontext() as context:
            context.prec = 50
            total = sum((row["amount"] for row in inputs), Decimal(0))
        _require(
            output["input_count"] == len(inputs) and output["total_amount"] == total
        )
        consumed.update(ids)
        rows.append(
            {
                **{field: output[field] for field in _BUDGET_RECONCILIATION_FIELDS},
                "input_record_count": len(inputs),
                "input_record_ids": ids,
                "canonical_input_total": str(total),
                "gold_output_total": str(output["total_amount"]),
                "status": "exact_match",
            }
        )
    _require(consumed == set(source) and len(rows) == gold.num_rows)
    return {
        "schema_version": "archive-govt-nz.health-budget-input-total-reconciliation/v1",
        "scope": "pinned_canonical_appropriation_facts_to_budget_gold_rows",
        "source_package_marker_sha256": sorted(package_markers),
        "period_basis": "literal_source_token_only",
        "unit_currency_and_price_basis": "source_context_preserved_currency_unknown",
        "vintage_pooling": "not_performed",
        "donor_control": "not_performed",
        "official_source_control": "not_performed",
        "cross_source_comparison": "not_performed",
        "group_count": len(rows),
        "input_record_count": len(source),
        "status": "exact_canonical_input_totals_reconciled",
        "groups": rows,
    }


def build_revenue_input_total_reconciliation(
    packages: tuple[CanonicalPackageInput, ...], gold: pa.Table
) -> dict[str, Any]:
    """Tie source-separated revenue Gold observations to pinned canonical facts."""
    _require(
        isinstance(packages, tuple)
        and 0 < len(packages) <= MAX_PACKAGES
        and all(package.kind == "revenue" for package in packages)
        and gold.schema.equals(NOMINAL_REVENUE_SCHEMA, check_metadata=True)
    )
    source: dict[str, dict[str, Any]] = {}
    package_markers: list[str] = []
    for package in packages:
        canonical, receipt = read_verified_canonical_tables(package)
        package_markers.append(receipt["marker_sha256"])
        for row in canonical["revenue_fact"].to_pylist():
            record_id = row["record_id"]
            _require(
                type(record_id) is str and bool(record_id) and record_id not in source
            )
            _require(isinstance(row["amount"], Decimal) and row["amount"].is_finite())
            source[record_id] = row

    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    consumed: set[str] = set()
    for output in gold.to_pylist():
        record_id = output["input_record_id"]
        _require(type(record_id) is str and record_id not in consumed)
        input_row = source.get(record_id)
        _require(input_row is not None)
        row = cast("dict[str, Any]", input_row)
        _require(
            all(row[field] == output[field] for field in _REVENUE_RECONCILIATION_FIELDS)
            and row["amount"] == output["amount"]
        )
        key = tuple(output[field] for field in _REVENUE_RECONCILIATION_FIELDS)
        _require(all(type(value) is str and bool(value) for value in key))
        group = grouped.setdefault(
            key,
            {
                **dict(zip(_REVENUE_RECONCILIATION_FIELDS, key, strict=True)),
                "input_record_ids": [],
                "canonical_input_total": Decimal(0),
                "gold_output_total": Decimal(0),
            },
        )
        group["input_record_ids"].append(record_id)
        with localcontext() as context:
            context.prec = 50
            group["canonical_input_total"] += row["amount"]
            group["gold_output_total"] += output["amount"]
        consumed.add(record_id)
    _require(consumed == set(source) and bool(grouped))
    groups = []
    for _, group in sorted(grouped.items()):
        record_ids = sorted(group["input_record_ids"])
        _require(group["canonical_input_total"] == group["gold_output_total"])
        groups.append(
            {
                **{field: group[field] for field in _REVENUE_RECONCILIATION_FIELDS},
                "input_record_count": len(record_ids),
                "input_record_ids": record_ids,
                "canonical_input_total": str(group["canonical_input_total"]),
                "gold_output_total": str(group["gold_output_total"]),
                "status": "exact_match",
            }
        )
    return {
        "schema_version": (
            "archive-govt-nz.health-revenue-input-total-reconciliation/v1"
        ),
        "scope": "pinned_canonical_revenue_facts_to_revenue_gold_rows",
        "source_package_marker_sha256": sorted(package_markers),
        "period_basis": "literal_source_token_only",
        "unit_currency_and_price_basis": "source_context_preserved_currency_unknown",
        "revenue_netting": "not_performed",
        "vintage_pooling": "not_performed",
        "donor_control": "not_performed",
        "official_source_control": "not_performed",
        "cross_source_comparison": "not_performed",
        "group_count": len(groups),
        "input_record_count": len(source),
        "status": "exact_canonical_input_totals_reconciled",
        "groups": groups,
    }


def build_pharmac_input_total_reconciliation(
    pharmac_input: PharmacGoldInput,
    source_facts: pa.Table,
    gold: pa.Table,
) -> dict[str, Any]:
    """Tie every Pharmac Gold allocation to its pinned, verified Silver fact."""
    _require(
        isinstance(pharmac_input, PharmacGoldInput)
        and source_facts.schema.equals(pharmac.FACT_SCHEMA, check_metadata=True)
        and gold.schema.equals(
            recordset_schema("pharmaceutical_budget_fact"), check_metadata=True
        )
    )
    source_rows = source_facts.to_pylist()
    source = {row["record_id"]: row for row in source_rows}
    _require(len(source) == len(source_rows) and bool(source))
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    consumed: set[str] = set()
    for output in gold.to_pylist():
        source_id = output["source_record_id"]
        _require(type(source_id) is str and source_id not in consumed)
        input_row = source.get(source_id)
        _require(input_row is not None)
        row = cast("dict[str, Any]", input_row)
        expected_regime = (
            "government_appropriation_allocated_to_pharmac"
            if row["period_start"] >= date(2022, 7, 1)
            else "district_health_board_budget_holder"
        )
        _require(
            output["record_id"] == pharmac_canonical_projection._canonical_id(source_id)  # noqa: SLF001
            and output["source_object_sha256"] == row["source_object_sha256"]
            and output["source_observation_id"] == row["source_observation_id"]
            and output["source_vintage"] == row["source_vintage"]
            and output["period_token"] == row["period_token"]
            and output["amount_type"] == row["amount_type"]
            and output["unit"] == row["unit"]
            and output["source_label"] == row["series_caption"]
            and output["budget_scope"] == row["series_caption"]
            and output["funding_regime"] == expected_regime
            and output["amount"] == row["amount"]
            and output["measure"] == "pharmaceutical_budget_allocation"
        )
        key = tuple(output[field] for field in _PHARMAC_RECONCILIATION_FIELDS)
        _require(all(type(value) is str and bool(value) for value in key))
        group = grouped.setdefault(
            key,
            {
                **dict(zip(_PHARMAC_RECONCILIATION_FIELDS, key, strict=True)),
                "input_record_ids": [],
                "gold_record_ids": [],
                "canonical_input_total": Decimal(0),
                "gold_output_total": Decimal(0),
            },
        )
        group["input_record_ids"].append(source_id)
        group["gold_record_ids"].append(output["record_id"])
        with localcontext() as context:
            context.prec = 50
            group["canonical_input_total"] += row["amount"]
            group["gold_output_total"] += output["amount"]
        consumed.add(source_id)
    _require(consumed == set(source) and bool(grouped) and gold.num_rows == len(source))
    groups = []
    for _, group in sorted(grouped.items()):
        input_ids = sorted(group["input_record_ids"])
        gold_ids = sorted(group["gold_record_ids"])
        _require(group["canonical_input_total"] == group["gold_output_total"])
        groups.append(
            {
                **{field: group[field] for field in _PHARMAC_RECONCILIATION_FIELDS},
                "input_record_count": len(input_ids),
                "input_record_ids": input_ids,
                "gold_record_ids": gold_ids,
                "canonical_input_total": str(group["canonical_input_total"]),
                "gold_output_total": str(group["gold_output_total"]),
                "status": "exact_match",
            }
        )
    return {
        "schema_version": (
            "archive-govt-nz.health-pharmac-input-total-reconciliation/v1"
        ),
        "scope": "pinned_pharmac_silver_facts_to_pharmac_gold_rows",
        "source_package_marker_sha256": [pharmac_input.manifest_sha256],
        "source_object_sha256": pharmac_input.source_sha256,
        "period_basis": "literal_source_token_only",
        "unit_currency_and_price_basis": (
            "source_context_preserved_currency_and_price_basis_unqualified"
        ),
        "published_change_recalculation": "not_performed",
        "actual_expenditure": "not_asserted",
        "funding_regime_pooling": "not_performed",
        "donor_control": "not_performed",
        "official_source_control": "not_performed",
        "cross_source_comparison": "not_performed",
        "group_count": len(groups),
        "input_record_count": len(source),
        "status": "exact_canonical_input_totals_reconciled",
        "groups": groups,
    }


def build_moh_input_gold_reconciliation(
    moh_input: MohGoldInput, source_facts: pa.Table, gold: pa.Table
) -> dict[str, Any]:
    """Prove row-for-row MoH Silver-to-Gold preservation without pooling measures."""
    _require(
        isinstance(moh_input, MohGoldInput)
        and source_facts.schema.equals(moh_indicators.FACT_SCHEMA)
        and gold.schema.equals(moh_indicators.FACT_SCHEMA)
    )
    source_rows = source_facts.to_pylist()
    gold_rows = gold.to_pylist()
    source = {row["record_id"]: row for row in source_rows}
    _require(len(source) == len(source_rows) == len(gold_rows) and bool(source))
    consumed: set[str] = set()
    by_profile: dict[str, dict[str, Any]] = {}
    for output in gold_rows:
        record_id = output["record_id"]
        _require(type(record_id) is str and record_id not in consumed)
        original = source.get(record_id)
        _require(original is not None and output == original)
        profile = output["profile"]
        group = by_profile.setdefault(
            profile, {"profile": profile, "record_ids": [], "row_count": 0}
        )
        group["record_ids"].append(record_id)
        group["row_count"] += 1
        consumed.add(record_id)
    _require(
        consumed == set(source) and set(by_profile) == set(moh_indicators.PROFILES)
    )
    for group in by_profile.values():
        group["record_ids"].sort()
        group["status"] = "exact_row_match"
    return {
        "schema_version": "archive-govt-nz.health-moh-input-gold-reconciliation/v1",
        "scope": "pinned_moh_silver_facts_to_gold_rows",
        "source_package_marker_sha256": sorted(
            item.manifest_sha256 for item in moh_input.packages
        ),
        "source_object_sha256": sorted(
            item.source_sha256 for item in moh_input.packages
        ),
        "measure_pooling": "not_performed",
        "period_alignment": "literal_source_token_only",
        "cross_source_comparison": "not_performed",
        "rights_state": "not_evaluated",
        "row_count": len(source),
        "status": "exact_source_rows_preserved",
        "profiles": [by_profile[key] for key in sorted(by_profile)],
    }


def build_crown_projection_gold_reconciliation(
    tables: dict[str, pa.Table],
) -> dict[str, Any]:
    """Account for exact Bronze-verified Crown projection rows in Gold."""
    definitions = {
        "crown_befu": "crown_expense_befu_2026.parquet",
        "crown_hyefu": "crown_expense_hyefu_2025.parquet",
        "fiscal_crown": "historical_fiscal_crown.parquet",
    }
    families: list[dict[str, Any]] = []
    for family, filename in definitions.items():
        table = tables.get(family)
        if table is None:
            continue
        rows = table.to_pylist()
        _require(bool(rows))
        source_ids: set[str] = set()
        output_ids: set[str] = set()
        source_objects: set[str] = set()
        controls = []
        for row in rows:
            source_id = row.get("source_record_id")
            output_id = row.get("record_id")
            token = row.get("value_token")
            amount = row.get("amount")
            _require(
                type(source_id) is str
                and bool(source_id)
                and source_id not in source_ids
                and type(output_id) is str
                and bool(output_id)
                and output_id not in output_ids
                and type(token) is str
                and bool(token)
                and isinstance(amount, Decimal)
                and amount.is_finite()
            )
            try:
                source_amount = Decimal(token)
            except InvalidOperation as exc:
                message = "canonical_gold_export_invalid"
                raise ValueError(message) from exc
            _require(source_amount.is_finite() and source_amount == amount)
            source_ids.add(source_id)
            output_ids.add(output_id)
            source_object = row.get("source_object_sha256")
            _require(type(source_object) is str and bool(source_object))
            source_objects.add(source_object)
            controls.append(
                {
                    "source_record_id": source_id,
                    "gold_record_id": output_id,
                    "source_object_sha256": row["source_object_sha256"],
                    "source_vintage": row["source_vintage"],
                    "period_token": row["period_token"],
                    "measure": row["measure"],
                    "amount_type": row["amount_type"],
                    "unit": row["unit"],
                    "source_value_token": token,
                    "gold_amount": str(amount),
                    "status": "exact_numeric_value_match",
                }
            )
        families.append(
            {
                "product": family,
                "gold_table": filename,
                "row_count": len(rows),
                "source_record_count": len(source_ids),
                "source_object_sha256": sorted(source_objects),
                "status": "exact_source_rows_preserved",
                "rows": sorted(controls, key=lambda item: item["gold_record_id"]),
            }
        )
    _require(bool(families))
    return {
        "schema_version": _CROWN_RECONCILIATION_SCHEMA,
        "scope": "verified_bronze_projection_value_tokens_to_crown_gold_rows",
        "source_object_sha256": sorted(
            {
                source_hash
                for family in families
                for source_hash in family["source_object_sha256"]
            }
        ),
        "period_alignment": "literal_source_tokens_only",
        "currency_and_accounting_basis": "source_context_preserved_unqualified",
        "cross_vintage_comparison": "not_performed",
        "core_total_crown_comparison": "not_performed",
        "aggregation": "not_performed",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
        "row_count": sum(item["row_count"] for item in families),
        "status": "exact_source_rows_preserved",
        "families": families,
    }


def _add_legacy_lineage_companion(
    packages: tuple[CanonicalPackageInput, ...], tables: dict[str, pa.Table]
) -> None:
    """Keep complete legacy links when the expanded cohort needs compact lookups."""
    if not any(package.kind in biff8_canonical.KINDS for package in packages):
        return
    lineages = [
        read_verified_canonical_tables(package)[0]["field_lineage"]
        for package in packages
        if package.kind not in biff8_canonical.KINDS
    ]
    if lineages:
        tables["canonical_input_lineage"] = pa.concat_tables(lineages).sort_by(
            [("lineage_id", "ascending")]
        )


def _inline_source_links(
    package: CanonicalPackageInput, canonical: dict[str, pa.Table], *, compact: bool
) -> list[dict[str, Any]]:
    rows = biff8_canonical.gold_inline_lineage(package.kind, canonical["field_lineage"])
    if compact and package.kind not in biff8_canonical.KINDS:
        return [
            row
            for row in rows
            if row["field"] in {"amount", "value", "unit", "period_token"}
        ]
    return rows


def _coordinate_evidence(
    kind: str, lineage: dict[str, Any], *, compact: bool
) -> dict[str, Any]:
    if compact and kind not in biff8_canonical.KINDS:
        return {
            "full_lineage_output": "canonical_input_lineage.parquet",
            "canonical_lineage_id": lineage["lineage_id"],
        }
    return biff8_canonical.drillthrough_evidence(kind, lineage)


def _source_drillthrough(
    tables: dict[str, pa.Table],
    outputs: dict[str, dict[str, Any]],
    packages: tuple[CanonicalPackageInput, ...],
) -> dict[str, Any]:
    """Link Gold rows to canonical source coordinates and exact source objects."""
    coordinates_by_record: dict[str, list[dict[str, Any]]] = {}
    for package in packages:
        canonical, _receipt = read_verified_canonical_tables(package)
        compact = "canonical_input_lineage" in tables
        for lineage in _inline_source_links(package, canonical, compact=compact):
            target_id = lineage["target_record_id"]
            locator = lineage["source_locator"]
            coordinate = lineage["source_coordinate"]
            _require(
                type(target_id) is str
                and bool(target_id)
                and type(locator) is str
                and bool(locator)
                and type(coordinate) is str
                and bool(coordinate)
            )
            item = {
                "field": lineage["field"],
                "source_coordinate": coordinate,
                "source_object_sha256": lineage["source_object_sha256"],
                "source_locator_sha256": hashlib.sha256(
                    locator.encode("utf-8")
                ).hexdigest(),
                "source_vintage": lineage["source_vintage"],
                "rights_state": lineage["rights_state"],
            }
            item.update(_coordinate_evidence(package.kind, lineage, compact=compact))
            coordinates_by_record.setdefault(target_id, []).append(item)
    for items in coordinates_by_record.values():
        items.sort(
            key=lambda item: (
                item["source_vintage"],
                item["source_object_sha256"],
                item["source_coordinate"],
                item["field"],
            )
        )

    by_record: dict[str, list[dict[str, Any]]] = {}
    for output_name, table_name in sorted(_TABLES.items()):
        table = tables.get(table_name)
        output = outputs.get(output_name)
        if (
            table is None
            or output is None
            or table_name == "canonical_input_lineage"
            or biff8_canonical.is_companion(table_name)
        ):
            continue
        for row_index, row in enumerate(table.to_pylist()):
            record_ids = row.get("input_record_ids")
            if record_ids is None:
                record_id = row.get("input_record_id")
                if record_id is None:
                    record_id = row.get("record_id", row.get("target_record_id"))
                record_ids = [record_id]
            _require(isinstance(record_ids, list) and bool(record_ids))
            for record_id in record_ids:
                _require(type(record_id) is str and bool(record_id))
                by_record.setdefault(record_id, []).append(
                    {
                        "output_name": output_name,
                        "output_sha256": output["sha256"],
                        "row_index": row_index,
                    }
                )
    _add_pharmac_coordinates(tables, coordinates_by_record)
    _add_moh_coordinates(tables, coordinates_by_record)
    _add_crown_coordinates(tables, coordinates_by_record)
    _add_fiscal_crown_coordinates(tables, coordinates_by_record)
    return {
        "schema_version": "archive-govt-nz.health-source-drillthrough/v2",
        "scope": "exact_row_and_source_coordinate_lookup_only",
        "row_identity": "output_sha256_and_zero_based_sorted_row_index",
        "cross_source_join": "not_performed",
        "records": [
            {
                "input_record_id": record_id,
                "source_coordinates": coordinates_by_record.get(record_id, []),
                "output_rows": sorted(
                    output_rows,
                    key=lambda item: (item["output_name"], item["row_index"]),
                ),
            }
            for record_id, output_rows in sorted(by_record.items())
        ],
    }


def _add_pharmac_coordinates(
    tables: dict[str, pa.Table],
    coordinates_by_record: dict[str, list[dict[str, Any]]],
) -> None:
    pharmac = tables.get("pharmac")
    lineage = tables.get("pharmac_lineage")
    if pharmac is None or lineage is None:
        return
    source_by_record = {row["record_id"]: row for row in pharmac.to_pylist()}
    for item in lineage.to_pylist():
        record_id = item["target_record_id"]
        source = source_by_record[record_id]
        locator = source["source_locator"]
        coordinate = {
            "field": item["field"],
            "source_coordinate": item["source_coordinate"],
            "source_object_sha256": source["source_object_sha256"],
            "source_locator_sha256": hashlib.sha256(
                locator.encode("utf-8")
            ).hexdigest(),
            "source_vintage": source["source_vintage"],
            "rights_state": source["rights_state"],
        }
        coordinates_by_record.setdefault(record_id, []).append(coordinate)
    for items in coordinates_by_record.values():
        items.sort(
            key=lambda item: (
                item["source_vintage"],
                item["source_object_sha256"],
                item["source_coordinate"],
                item["field"],
            )
        )


def _add_moh_coordinates(
    tables: dict[str, pa.Table],
    coordinates_by_record: dict[str, list[dict[str, Any]]],
) -> None:
    lineage = tables.get("moh_lineage")
    if lineage is None:
        return
    for row in lineage.to_pylist():
        record_id = row["record_id"]
        locator = row["source_locator"]
        coordinates_by_record.setdefault(record_id, []).append(
            {
                "field": row["field"],
                "source_coordinate": row["source_coordinate"],
                "source_object_sha256": row["source_object_sha256"],
                "source_locator_sha256": hashlib.sha256(
                    locator.encode("utf-8")
                ).hexdigest(),
                "source_vintage": "MoH-HAIR-2024",
                "rights_state": "not_evaluated",
            }
        )


def _add_crown_coordinates(
    tables: dict[str, pa.Table],
    coordinates_by_record: dict[str, list[dict[str, Any]]],
) -> None:
    for family in ("crown_befu", "crown_hyefu"):
        facts = tables.get(family)
        lineage = tables.get(f"{family}_lineage")
        if facts is None or lineage is None:
            continue
        sources = {row["record_id"]: row for row in facts.to_pylist()}
        for row in lineage.to_pylist():
            record_id = row["target_record_id"]
            source = sources[record_id]
            locator = source["source_locator"]
            coordinates_by_record.setdefault(record_id, []).append(
                {
                    "field": row["field"],
                    "source_coordinate": row["source_coordinate"],
                    "source_object_sha256": source["source_object_sha256"],
                    "source_locator_sha256": hashlib.sha256(
                        locator.encode("utf-8")
                    ).hexdigest(),
                    "source_vintage": source["source_vintage"],
                    "rights_state": source["rights_state"],
                }
            )
    for items in coordinates_by_record.values():
        items.sort(
            key=lambda item: (
                item["source_vintage"],
                item["source_object_sha256"],
                item["source_coordinate"],
                item["field"],
            )
        )


def _add_fiscal_crown_coordinates(
    tables: dict[str, pa.Table],
    coordinates_by_record: dict[str, list[dict[str, Any]]],
) -> None:
    lineage = tables.get("fiscal_crown_lineage")
    if lineage is None:
        return
    for row in lineage.to_pylist():
        record_id = row["target_record_id"]
        locator = row["source_locator"]
        coordinates_by_record.setdefault(record_id, []).append(
            {
                "field": row["field"],
                "source_coordinate": row["source_coordinate"],
                "source_object_sha256": row["source_object_sha256"],
                "source_locator_sha256": hashlib.sha256(
                    locator.encode("utf-8")
                ).hexdigest(),
                "source_vintage": row["source_vintage"],
                "rights_state": row["rights_state"],
            }
        )
    for items in coordinates_by_record.values():
        items.sort(
            key=lambda item: (
                item["source_vintage"],
                item["source_object_sha256"],
                item["source_coordinate"],
                item["field"],
            )
        )


def _add_pharmac_product(
    pharmac_input: PharmacGoldInput | None,
    tables: dict[str, pa.Table],
    product_report: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if pharmac_input is None:
        return None
    facts, lineage, receipt = project_pharmac_cpb(
        pharmac_input.root,
        pharmac_input.manifest_sha256,
        pharmac_input.source_cas_root,
        pharmac_input.source_sha256,
    )
    tables["pharmac"] = facts
    # Silver lineage rows contain null shared-envelope fields. Export only the
    # populated source-coordinate columns into the standalone Gold lineage table.
    tables["pharmac_lineage"] = lineage.select(
        [
            "target_record_id",
            "field",
            "source_coordinate",
            "raw_value",
            "normalized_value",
            "rule",
        ]
    )
    query_receipts.append(
        {
            "input_records": receipt["input_records"],
            "package_marker_sha256": [pharmac_input.manifest_sha256],
        }
    )
    product_report["pharmac"] = {
        "input_records": receipt["input_records"],
        "output_rows": facts.num_rows,
        "aggregation": "none_source_record_rows_preserved",
        "budget_scope": "published_pharmaceutical_budget_allocation",
        "funding_regimes": sorted({row["funding_regime"] for row in facts.to_pylist()}),
        "actual_expenditure": "not_asserted",
        "vintage_pooling": "not_performed",
    }
    return receipt


def _add_moh_product(
    moh_input: MohGoldInput | None,
    tables: dict[str, pa.Table],
    product_report: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if moh_input is None:
        return None
    facts, lineage, receipt = project_moh_indicators(moh_input)
    tables["moh"] = facts
    tables["moh_lineage"] = lineage
    query_receipts.append(
        {
            "input_records": receipt["input_records"],
            "package_marker_sha256": [
                item.manifest_sha256 for item in moh_input.packages
            ],
        }
    )
    product_report["moh"] = {
        "input_records": receipt["input_records"],
        "output_rows": facts.num_rows,
        "aggregation": receipt["aggregation"],
        "published_measure": "real_nominal_and_per_capita_labels_preserved",
        "unit_price_base_denominator": "unknown_not_inferred",
        "actual_expenditure": "not_asserted",
        "rights_state": "not_evaluated",
        "vintage_pooling": "not_performed",
    }
    return receipt


def _add_crown_products(
    crown_input: CrownGoldInput | None,
    tables: dict[str, pa.Table],
    product_report: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if crown_input is None:
        return None
    families = (
        (
            "crown_befu",
            crown_input.befu_root,
            crown_input.befu_manifest_sha256,
            crown_expense_canonical_projection.project_befu_core_expense,
            "BEFU-2026",
        ),
        (
            "crown_hyefu",
            crown_input.hyefu_root,
            crown_input.hyefu_manifest_sha256,
            hyefu_crown_expense_canonical_projection.project_hyefu_core_expense,
            "HYEFU-2025",
        ),
    )
    receipts: dict[str, dict[str, Any]] = {}
    for family, silver_root, marker, project, vintage in families:
        facts, lineage, receipt = project(
            silver_root, marker, crown_input.source_cas_root
        )
        _require(
            facts.num_rows == _CROWN_FACT_ROWS
            and lineage.num_rows == _CROWN_LINEAGE_ROWS
        )
        _require(all(row["source_vintage"] == vintage for row in facts.to_pylist()))
        _require(len({row["record_id"] for row in facts.to_pylist()}) == facts.num_rows)
        tables[family] = facts
        tables[f"{family}_lineage"] = lineage.select(
            [
                "target_record_id",
                "field",
                "source_coordinate",
                "raw_value",
                "normalized_value",
                "rule",
            ]
        )
        query_receipts.append(
            {
                "input_records": receipt["input_records"],
                "package_marker_sha256": [marker],
            }
        )
        product_report[family] = {
            "input_records": receipt["input_records"],
            "output_rows": facts.num_rows,
            "aggregation": "none_source_record_rows_preserved",
            "source_vintage": vintage,
            "measure": "core_crown_expense_formula_cache",
            "currency_and_accounting_basis": "unknown_not_inferred",
            "financial_year_boundaries": "unqualified_year_labels_preserved",
            "rights_state": "not_evaluated",
            "actual_expenditure": "not_asserted",
            "cross_vintage_comparison": "not_performed",
            "vintage_pooling": "not_performed",
        }
        receipts[family] = receipt
    _require(
        {row["record_id"] for row in tables["crown_befu"].to_pylist()}.isdisjoint(
            row["record_id"] for row in tables["crown_hyefu"].to_pylist()
        )
    )
    return {
        "befu": receipts["crown_befu"],
        "hyefu": receipts["crown_hyefu"],
        "cross_source_join": "not_performed",
        "cross_vintage_comparison": "not_performed",
    }


def _add_fiscal_crown_product(
    fiscal_input: FiscalCrownGoldInput | None,
    tables: dict[str, pa.Table],
    product_report: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if fiscal_input is None:
        return None
    facts, lineage, receipt = fiscal_crown_canonical_projection.project_fiscal_crown(
        fiscal_input.source_path
    )
    _require(
        facts.num_rows == _FISCAL_CROWN_FACT_ROWS
        and lineage.num_rows == _FISCAL_CROWN_LINEAGE_ROWS
        and receipt["core_crown_records"] == _FISCAL_CORE_ROWS
        and receipt["total_crown_records"] == _FISCAL_TOTAL_ROWS
    )
    fact_rows = facts.to_pylist()
    _require(len({row["record_id"] for row in fact_rows}) == facts.num_rows)
    _require(
        {row["measure"] for row in fact_rows}
        == {"core_crown_expenses", "total_crown_expenses"}
    )
    tables["fiscal_crown"] = facts
    tables["fiscal_crown_lineage"] = lineage.select(
        [
            "target_record_id",
            "field",
            "source_coordinate",
            "raw_value",
            "normalized_value",
            "rule",
            "source_object_sha256",
            "source_locator",
            "source_vintage",
            "rights_state",
        ]
    )
    query_receipts.append(
        {
            "input_records": receipt["input_records"],
            "package_marker_sha256": [receipt["source_object_sha256"]],
        }
    )
    product_report["fiscal_crown"] = {
        "input_records": receipt["input_records"],
        "output_rows": facts.num_rows,
        "lineage_rows": lineage.num_rows,
        "aggregation": "none_source_record_rows_preserved",
        "measure_families": {
            "core_crown_expenses": _FISCAL_CORE_ROWS,
            "total_crown_expenses": _FISCAL_TOTAL_ROWS,
        },
        "currency": "unknown_not_inferred",
        "financial_year_start": "unqualified",
        "accounting_basis": "source_label_retained",
        "rights_state": "not_evaluated",
        "cross_measure_comparison": "not_performed",
    }
    return receipt


def _add_crown_gold_products(
    inputs: GoldInputs,
    tables: dict[str, pa.Table],
    product_report: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "crown": _add_crown_products(
            inputs.crown, tables, product_report, query_receipts
        ),
        "fiscal_crown": _add_fiscal_crown_product(
            inputs.fiscal_crown, tables, product_report, query_receipts
        ),
    }


def _output_inventory(
    payloads: dict[str, bytes], tables: dict[str, pa.Table]
) -> dict[str, dict[str, Any]]:
    outputs = {
        name: {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "rows": tables[_TABLES[name]].num_rows,
        }
        for name, payload in sorted(payloads.items())
        if name in _TABLES
    }
    outputs.update(
        {
            name: {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "kind": "plot_png",
                "display_only": True,
            }
            for name, payload in sorted(payloads.items())
            if name not in _TABLES and name.endswith(".png")
        }
    )
    for name, kind, profile in (
        ("dataset-card.md", "dataset_card", None),
        ("historical_revision_reconciliation.json", "report", None),
        ("cross_source_period_overlap.json", "report", None),
        ("ro-crate-metadata.json", "ro_crate_metadata", "RO-Crate 1.1"),
    ):
        payload = payloads[name]
        outputs[name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "kind": kind,
            **({"standards_profile": profile} if profile else {}),
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    if "budget_input_total_reconciliation.json" in payloads:
        payload = payloads["budget_input_total_reconciliation.json"]
        outputs["budget_input_total_reconciliation.json"] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "kind": "report",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    if "revenue_input_total_reconciliation.json" in payloads:
        payload = payloads["revenue_input_total_reconciliation.json"]
        outputs["revenue_input_total_reconciliation.json"] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "kind": "report",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    if "pharmac_input_total_reconciliation.json" in payloads:
        payload = payloads["pharmac_input_total_reconciliation.json"]
        outputs["pharmac_input_total_reconciliation.json"] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "kind": "report",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    if "moh_input_gold_reconciliation.json" in payloads:
        payload = payloads["moh_input_gold_reconciliation.json"]
        outputs["moh_input_gold_reconciliation.json"] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "kind": "report",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    if "crown_projection_gold_reconciliation.json" in payloads:
        payload = payloads["crown_projection_gold_reconciliation.json"]
        outputs["crown_projection_gold_reconciliation.json"] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "kind": "report",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    return outputs


def _package_markers(query_receipts: list[dict[str, Any]]) -> list[str]:
    return sorted(
        marker
        for query_receipt in query_receipts
        for marker in query_receipt["package_marker_sha256"]
    )


def build_temporal_coverage_report(tables: dict[str, pa.Table]) -> dict[str, Any]:
    """List observed period tokens by exact source context without gap inference."""
    definitions = {
        "historical_observations.parquet": (
            "observations",
            (
                "source_vintage",
                "recordset",
                "measure",
                "unit",
                "currency",
                "price_basis",
                "base_period",
                "denominator_definition",
                "institutional_coverage",
                "accounting_basis",
                "source_label",
                "source_locator",
            ),
        ),
        "nominal_budget.parquet": (
            "budget",
            (
                "source_vintage",
                "amount_type",
                "unit",
                "vote",
                "department",
                "portfolio",
                "source_label",
            ),
        ),
        "nominal_revenue.parquet": (
            "revenue",
            (
                "source_vintage",
                "amount_type",
                "unit",
                "vote",
                "department",
                "revenue_type",
                "source_label",
            ),
        ),
        "nominal_pharmaceutical_budget.parquet": (
            "pharmac",
            (
                "source_vintage",
                "amount_type",
                "unit",
                "budget_scope",
                "funding_regime",
            ),
        ),
        "published_health_indicators.parquet": (
            "moh",
            (
                "source_vintage",
                "profile",
                "source_label",
                "price_basis",
                "per_capita",
                "unit",
                "price_base",
                "denominator",
            ),
        ),
        "crown_expense_befu_2026.parquet": (
            "crown_befu",
            (
                "source_vintage",
                "observation_context",
                "measure",
                "amount_type",
                "unit",
                "currency",
                "institutional_coverage",
                "accounting_basis",
                "source_label",
                "source_locator",
            ),
        ),
        "crown_expense_hyefu_2025.parquet": (
            "crown_hyefu",
            (
                "source_vintage",
                "observation_context",
                "measure",
                "amount_type",
                "unit",
                "currency",
                "institutional_coverage",
                "accounting_basis",
                "source_label",
                "source_locator",
            ),
        ),
        "historical_fiscal_crown.parquet": (
            "fiscal_crown",
            (
                "source_vintage",
                "observation_context",
                "measure",
                "amount_type",
                "unit",
                "currency",
                "institutional_coverage",
                "accounting_basis",
                "source_label",
                "source_locator",
            ),
        ),
    }
    for kind in biff8_canonical.KINDS:
        definitions[kind + ".parquet"] = (
            kind,
            (
                "source_vintage",
                "recordset",
                "source_object_sha256",
                "source_label",
                "amount_type",
                "unit",
                "currency",
                "value_basis",
            ),
        )
    groups: list[dict[str, Any]] = []
    for output_name, (table_name, context_fields) in definitions.items():
        table = tables.get(table_name)
        if table is None:
            continue
        grouped: dict[tuple[Any, ...], dict[str, int]] = {}
        for row in table.to_pylist():
            period = row["period_token"]
            _require(type(period) is str and bool(period))
            context = tuple(row[field] for field in context_fields)
            periods = grouped.setdefault(context, {})
            periods[period] = periods.get(period, 0) + 1
        for context, periods in sorted(
            grouped.items(),
            key=lambda item: tuple("" if value is None else value for value in item[0]),
        ):
            groups.append(
                {
                    "output_name": output_name,
                    "context": dict(zip(context_fields, context, strict=True)),
                    "observed_periods": [
                        {"period_token": token, "observation_count": periods[token]}
                        for token in sorted(periods)
                    ],
                }
            )
    return {
        "schema_version": "archive-govt-nz.health-temporal-coverage/v1",
        "scope": "observed_period_tokens_by_exact_source_context",
        "ordering": "period_tokens_sorted_as_strings",
        "gap_inference": "not_performed",
        "cross_source_join": "not_performed",
        "vintage_pooling": "not_performed",
        "groups": groups,
    }


def build_cross_source_period_overlap_report(
    tables: dict[str, pa.Table],
) -> dict[str, Any]:
    """List literal period-token overlaps without joining or comparing values."""
    definitions = {
        "historical": ("observations", "input_record_id"),
        "budget": ("budget", "input_record_ids"),
        "revenue": ("revenue", "input_record_id"),
        "pharmac": ("pharmac", "record_id"),
        "moh": ("moh", "record_id"),
        "crown_befu": ("crown_befu", "record_id"),
        "crown_hyefu": ("crown_hyefu", "record_id"),
        "fiscal_crown": ("fiscal_crown", "record_id"),
        "biff8_budget": ("biff8_budget", "record_id"),
        "biff8_revenue": ("biff8_revenue", "record_id"),
    }
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for product, (table_name, id_field) in definitions.items():
        table = tables.get(table_name)
        if table is None:
            continue
        for row in table.to_pylist():
            period = row.get("period_token")
            vintage = row.get("source_vintage")
            unit = row.get("unit")
            identities = row.get(id_field)
            record_ids = identities if id_field == "input_record_ids" else [identities]
            _require(
                type(period) is str
                and bool(period)
                and type(vintage) is str
                and bool(vintage)
                and (unit is None or (type(unit) is str and bool(unit)))
                and (
                    isinstance(record_ids, list)
                    and bool(record_ids)
                    and all(
                        type(record_id) is str and record_id for record_id in record_ids
                    )
                )
            )
            group = groups.setdefault(period, {}).setdefault(
                product,
                {
                    "row_count": 0,
                    "source_vintages": set(),
                    "units": set(),
                    "input_record_ids": set(),
                },
            )
            group["row_count"] += 1
            group["source_vintages"].add(vintage)
            group["units"].add(unit if unit is not None else "unknown_not_asserted")
            group["input_record_ids"].update(record_ids)
    overlaps = []
    for period in sorted(groups):
        products = groups[period]
        if len(products) < MIN_OVERLAP_PRODUCTS:
            continue
        overlaps.append(
            {
                "period_token": period,
                "status": "literal_period_token_overlap_candidate",
                "product_groups": [
                    {
                        "product": product,
                        "row_count": details["row_count"],
                        "source_vintages": sorted(details["source_vintages"]),
                        "units": sorted(details["units"]),
                        "input_record_ids": sorted(details["input_record_ids"]),
                    }
                    for product, details in sorted(products.items())
                ],
                "comparability": "not_assessed",
                "numeric_variance": "not_computed",
            }
        )
    return {
        "schema_version": "archive-govt-nz.health-cross-source-period-overlap/v1",
        "scope": "observed_canonical_product_rows_only",
        "match_basis": "literal_period_token_only",
        "completeness": "observed_rows_only",
        "comparability": "not_assessed",
        "numeric_variance": "not_computed",
        "cross_source_join": "not_performed",
        "overlap_group_count": len(overlaps),
        "groups": overlaps,
    }


def build_classification_drift_report(
    tables: dict[str, pa.Table],
) -> dict[str, Any]:
    """Report label changes within explicit source dimensions, without mapping.

    Only Budget and revenue labels are assessed. A candidate is emitted when
    one exact dimensional key has multiple observed source labels across the
    supplied vintages. This flags a review lead; it does not assert semantic
    equivalence, mapping, completeness, or approved classification drift.
    """
    definitions = {
        "nominal_budget.parquet": (
            "budget",
            ("period_token", "amount_type", "unit", "vote", "department", "portfolio"),
        ),
        "nominal_revenue.parquet": (
            "revenue",
            (
                "period_token",
                "amount_type",
                "unit",
                "vote",
                "department",
                "revenue_type",
            ),
        ),
    }
    candidates: list[dict[str, Any]] = []
    for output_name, (table_name, key_fields) in definitions.items():
        table = tables.get(table_name)
        if table is None:
            continue
        grouped: dict[tuple[Any, ...], dict[str, set[str]]] = {}
        for row in table.to_pylist():
            label = row.get("source_label")
            vintage = row.get("source_vintage")
            _require(type(label) is str and bool(label))
            _require(type(vintage) is str and bool(vintage))
            key = tuple(row[field] for field in key_fields)
            labels = grouped.setdefault(key, {})
            labels.setdefault(vintage, set()).add(label)
        for key, labels_by_vintage in sorted(
            grouped.items(),
            key=lambda item: tuple("" if v is None else v for v in item[0]),
        ):
            all_labels = sorted(
                {label for labels in labels_by_vintage.values() for label in labels}
            )
            if len(all_labels) < MIN_DISTINCT_CLASSIFICATION_LABELS:
                continue
            candidates.append(
                {
                    "output_name": output_name,
                    "key": dict(zip(key_fields, key, strict=True)),
                    "labels_by_vintage": {
                        vintage: sorted(labels)
                        for vintage, labels in sorted(labels_by_vintage.items())
                    },
                    "observed_labels": all_labels,
                    "status": "source_label_change_candidate",
                    "mapping": "not_inferred",
                    "semantic_equivalence": "not_assessed",
                }
            )
    return {
        "schema_version": "archive-govt-nz.health-classification-drift/v1",
        "scope": "same_source_family_and_exact_dimensions_across_observed_vintages",
        "source_families": ["budget", "revenue"],
        "completeness": "observed_rows_only",
        "threshold": "at_least_two_distinct_source_labels_for_one_exact_key",
        "mapping": "not_inferred",
        "cross_source_comparison": "not_performed",
        "candidates": candidates,
    }


def build_revision_reconciliation_report(
    tables: dict[str, pa.Table],
) -> dict[str, Any]:
    """List exact-context value-change candidates without explaining them."""
    table = tables.get("observations")
    context_fields = (
        "recordset",
        "measure",
        "source_label",
        "unit",
        "currency",
        "price_basis",
        "base_period",
        "denominator_definition",
        "institutional_coverage",
        "accounting_basis",
        "period_token",
    )
    groups: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = {}
    if table is not None:
        for row in table.to_pylist():
            vintage = row.get("source_vintage")
            record_id = row.get("input_record_id")
            amount = row.get("amount")
            _require(
                type(vintage) is str
                and bool(vintage)
                and type(record_id) is str
                and bool(record_id)
                and isinstance(amount, Decimal)
                and amount.is_finite()
            )
            key = tuple(row.get(field) for field in context_fields)
            groups.setdefault(key, {}).setdefault(vintage, []).append(
                {"amount": amount, "input_record_id": record_id}
            )

    candidates: list[dict[str, Any]] = []
    unchanged_groups = 0
    ambiguous_groups = 0
    shared_groups = 0
    for key, vintage_rows in sorted(
        groups.items(),
        key=lambda item: tuple(
            "" if value is None else str(value) for value in item[0]
        ),
    ):
        if len(vintage_rows) < MIN_REVISION_VINTAGES:
            continue
        shared_groups += 1
        if any(len(rows) != 1 for rows in vintage_rows.values()):
            ambiguous_groups += 1
            continue
        values = {
            vintage: rows[0]["amount"] for vintage, rows in sorted(vintage_rows.items())
        }
        if len(set(values.values())) == 1:
            unchanged_groups += 1
            continue
        context = dict(zip(context_fields, key, strict=True))
        candidates.append(
            {
                **context,
                "status": "historical_value_change_candidate",
                "values_by_vintage": {
                    vintage: str(value) for vintage, value in values.items()
                },
                "input_record_ids_by_vintage": {
                    vintage: rows[0]["input_record_id"]
                    for vintage, rows in sorted(vintage_rows.items())
                },
                "interpretation": "not_assessed",
            }
        )
    budget_report = _product_revision_report(
        tables.get("budget"),
        product="budget",
        key_fields=(
            "period_token",
            "amount_type",
            "unit",
            "vote",
            "department",
            "portfolio",
            "source_label",
        ),
        value_field="total_amount",
        record_ids_field="input_record_ids",
    )
    revenue_report = _product_revision_report(
        tables.get("revenue"),
        product="revenue",
        key_fields=(
            "period_token",
            "amount_type",
            "unit",
            "vote",
            "department",
            "revenue_type",
            "source_label",
        ),
        value_field="amount",
        record_ids_field="input_record_id",
    )
    biff8_budget_report = _product_revision_report(
        tables.get("biff8_budget"),
        product="biff8_budget",
        key_fields=(
            "period_token",
            "measure",
            "amount_type",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "source_label",
            "vote",
            "appropriation",
            "department",
            "portfolio",
            "value_basis",
        ),
        value_field="amount",
        record_ids_field="record_id",
    )
    biff8_revenue_report = _product_revision_report(
        tables.get("biff8_revenue"),
        product="biff8_revenue",
        key_fields=(
            "period_token",
            "measure",
            "amount_type",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "source_label",
            "vote",
            "department",
            "revenue_type",
            "source_application_id",
            "value_basis",
        ),
        value_field="amount",
        record_ids_field="record_id",
    )
    pharmac_report = _product_revision_report(
        tables.get("pharmac"),
        product="pharmac",
        key_fields=(
            "period_token",
            "measure",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "amount_type",
            "source_label",
            "budget_scope",
            "funding_regime",
        ),
        value_field="amount",
        record_ids_field="record_id",
    )
    moh_report = _product_revision_report(
        tables.get("moh"),
        product="moh",
        key_fields=(
            "period_token",
            "profile",
            "source_label",
            "price_basis",
            "per_capita",
            "unit",
            "price_base",
            "denominator",
        ),
        value_field="amount",
        record_ids_field="record_id",
    )
    crown_tables = [
        tables[name]
        for name in ("crown_befu", "crown_hyefu", "fiscal_crown")
        if name in tables
    ]
    crown_table = pa.concat_tables(crown_tables) if crown_tables else None
    crown_report = _product_revision_report(
        crown_table,
        product="crown",
        key_fields=(
            "period_token",
            "measure",
            "amount_type",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "source_label",
            "institutional_coverage",
            "accounting_basis",
        ),
        value_field="amount",
        record_ids_field="record_id",
    )
    return {
        "schema_version": "archive-govt-nz.health-revision-reconciliation/v1",
        "scope": (
            "same_recordset_measure_source_label_and_exact_context_period_"
            "across_observed_vintages"
        ),
        "key_fields": list(context_fields),
        "completeness": (
            "historical_budget_revenue_biff8_budget_biff8_revenue_"
            "pharmac_moh_crown_product_rows"
        ),
        "shared_series_period_count": shared_groups,
        "unchanged_series_period_count": unchanged_groups,
        "ambiguous_series_period_count": ambiguous_groups,
        "changed_candidate_count": len(candidates),
        "difference_interpretation": "not_assessed",
        "other_product_revisions": "not_assessed",
        "cross_source_comparison": "not_performed",
        "product_revisions": {
            "budget": budget_report,
            "revenue": revenue_report,
            "biff8_budget": biff8_budget_report,
            "biff8_revenue": biff8_revenue_report,
            "pharmac": pharmac_report,
            "moh": moh_report,
            "crown": crown_report,
        },
        "candidates": candidates,
    }


def _product_revision_report(
    table: pa.Table | None,
    *,
    product: str,
    key_fields: tuple[str, ...],
    value_field: str,
    record_ids_field: str,
) -> dict[str, Any]:
    """Compare exact source dimensions and period tokens within one mart."""
    witness_fields = _PRODUCT_REVISION_WITNESS_FIELDS.get(product, ())
    groups: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = {}
    if table is not None:
        for row in table.to_pylist():
            vintage = row.get("source_vintage")
            value = row.get(value_field)
            record_ids = row.get(record_ids_field)
            ids = record_ids if record_ids_field == "input_record_ids" else [record_ids]
            _require(
                type(vintage) is str
                and bool(vintage)
                and isinstance(value, Decimal)
                and value.is_finite()
                and isinstance(ids, list)
                and bool(ids)
                and all(type(record_id) is str and record_id for record_id in ids)
            )
            key = tuple(row.get(field) for field in key_fields)
            row_data = {"value": value, "record_ids": sorted(ids)}
            if witness_fields:
                row_data["witnesses"] = {
                    field: row.get(field) for field in witness_fields
                }
            groups.setdefault(key, {}).setdefault(vintage, []).append(row_data)

    candidates: list[dict[str, Any]] = []
    shared = unchanged = ambiguous = 0
    for key, vintage_rows in sorted(
        groups.items(),
        key=lambda item: tuple(
            "" if value is None else str(value) for value in item[0]
        ),
    ):
        if len(vintage_rows) < MIN_REVISION_VINTAGES:
            continue
        shared += 1
        if any(len(rows) != 1 for rows in vintage_rows.values()):
            ambiguous += 1
            continue
        values = {
            vintage: rows[0]["value"] for vintage, rows in sorted(vintage_rows.items())
        }
        if len(set(values.values())) == 1:
            unchanged += 1
            continue
        candidate = {
            **dict(zip(key_fields, key, strict=True)),
            "status": f"{product}_value_change_candidate",
            "values_by_vintage": {
                vintage: str(value) for vintage, value in values.items()
            },
            "input_record_ids_by_vintage": {
                vintage: rows[0]["record_ids"]
                for vintage, rows in sorted(vintage_rows.items())
            },
            "interpretation": "not_assessed",
        }
        if witness_fields:
            candidate["witnesses_by_vintage"] = {
                vintage: rows[0]["witnesses"]
                for vintage, rows in sorted(vintage_rows.items())
            }
        candidates.append(candidate)
    return {
        "scope": "same_literal_source_dimensions_and_period_token_within_product",
        "key_fields": list(key_fields),
        "completeness": "observed_rows_only",
        "shared_series_period_count": shared,
        "unchanged_series_period_count": unchanged,
        "ambiguous_series_period_count": ambiguous,
        "changed_candidate_count": len(candidates),
        "interpretation": "not_assessed",
        "candidates": candidates,
    }


def _preflight(
    packages: tuple[CanonicalPackageInput, ...],
    output: Path,
    inputs: GoldInputs,
) -> None:
    _require(not output.exists() and not output.is_symlink())
    _require(output.parent.is_dir() and not output.parent.is_symlink())
    target = output.resolve()
    for package in packages:
        for protected in (
            package.root,
            package.original,
            package.raw_root,
        ):
            resolved = protected.resolve()
            _require(
                not target.is_relative_to(resolved)
                and not resolved.is_relative_to(target)
            )
    if inputs.pharmac is not None:
        for protected in (
            inputs.pharmac.root,
            inputs.pharmac.source_cas_root,
        ):
            resolved = protected.resolve()
            _require(
                not target.is_relative_to(resolved)
                and not resolved.is_relative_to(target)
            )
    if inputs.moh is not None:
        protected_roots = [inputs.moh.source_cas_root]
        protected_roots.extend(item.root for item in inputs.moh.packages)
        for protected in protected_roots:
            resolved = protected.resolve()
            _require(
                not target.is_relative_to(resolved)
                and not resolved.is_relative_to(target)
            )
    if inputs.crown is not None:
        for protected in (
            inputs.crown.befu_root,
            inputs.crown.hyefu_root,
            inputs.crown.source_cas_root,
        ):
            resolved = protected.resolve()
            _require(
                not target.is_relative_to(resolved)
                and not resolved.is_relative_to(target)
            )
    if inputs.fiscal_crown is not None:
        resolved = inputs.fiscal_crown.source_path.resolve()
        _require(
            not target.is_relative_to(resolved) and not resolved.is_relative_to(target)
        )


def _readback(path: Path, payload: bytes, table: pa.Table | None = None) -> None:
    _require(path.is_file() and not path.is_symlink())
    with path.open("rb") as stream:
        observed = stream.read(MAX_OUTPUT_BYTES + 1)
    _require(observed == payload)
    if table is not None:
        restored = pq.read_table(BytesIO(observed))
        _require(restored.cast(table.schema).equals(table, check_metadata=True))


def _build_payloads(  # noqa: PLR0913, PLR0917 - explicit product input set
    tables: dict[str, pa.Table],
    products: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
    packages: tuple[CanonicalPackageInput, ...],
    pharmac_input: PharmacGoldInput | None,
    moh_input: MohGoldInput | None,
) -> tuple[
    dict[str, bytes],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    _add_legacy_lineage_companion(packages, tables)
    table_payloads = {
        filename: _table_bytes(tables[key])
        for filename, key in _TABLES.items()
        if key in tables
    }
    plot_payloads, plot_report = build_discrete_plots(
        {
            filename: tables[key].to_pylist()
            for filename, key in _TABLES.items()
            if key in tables
        }
    )
    payloads = {**table_payloads, **plot_payloads}
    temporal_report = build_temporal_coverage_report(tables)
    package_markers = _package_markers(query_receipts)
    payloads["dataset-card.md"] = _dataset_card(
        products, temporal_report, package_markers
    )
    classification_drift_report = build_classification_drift_report(tables)
    revision_report = build_revision_reconciliation_report(tables)
    cross_source_report = build_cross_source_period_overlap_report(tables)
    payloads["historical_revision_reconciliation.json"] = _encoded(revision_report)
    payloads["cross_source_period_overlap.json"] = _encoded(cross_source_report)
    budget_packages = tuple(package for package in packages if package.kind == "budget")
    if budget_packages:
        budget_reconciliation = build_budget_input_total_reconciliation(
            budget_packages, tables["budget"]
        )
        products["budget"]["input_total_reconciliation"] = budget_reconciliation
        payloads["budget_input_total_reconciliation.json"] = _encoded(
            budget_reconciliation
        )
    revenue_packages = tuple(
        package for package in packages if package.kind == "revenue"
    )
    if revenue_packages:
        revenue_reconciliation = build_revenue_input_total_reconciliation(
            revenue_packages, tables["revenue"]
        )
        products["revenue"]["input_total_reconciliation"] = revenue_reconciliation
        payloads["revenue_input_total_reconciliation.json"] = _encoded(
            revenue_reconciliation
        )
    if pharmac_input is not None:
        source_facts, _, _ = read_verified_pharmac_tables(
            pharmac_input.root,
            pharmac_input.manifest_sha256,
            pharmac_input.source_cas_root,
            pharmac_input.source_sha256,
        )
        pharmac_reconciliation = build_pharmac_input_total_reconciliation(
            pharmac_input, source_facts, tables["pharmac"]
        )
        products["pharmac"]["input_total_reconciliation"] = pharmac_reconciliation
        payloads["pharmac_input_total_reconciliation.json"] = _encoded(
            pharmac_reconciliation
        )
    if moh_input is not None:
        source_facts, _ = read_verified_moh_tables(
            moh_input.packages, moh_input.source_cas_root
        )
        moh_reconciliation = build_moh_input_gold_reconciliation(
            moh_input, source_facts, tables["moh"]
        )
        products["moh"]["input_gold_reconciliation"] = moh_reconciliation
        payloads["moh_input_gold_reconciliation.json"] = _encoded(moh_reconciliation)
    if any(name in tables for name in ("crown_befu", "crown_hyefu", "fiscal_crown")):
        crown_reconciliation = build_crown_projection_gold_reconciliation(tables)
        for family in crown_reconciliation["families"]:
            products[family["product"]]["projection_gold_reconciliation"] = (
                crown_reconciliation
            )
        payloads["crown_projection_gold_reconciliation.json"] = _encoded(
            crown_reconciliation
        )
    payloads["ro-crate-metadata.json"] = _encoded(_ro_crate_metadata(payloads))
    return (
        payloads,
        plot_report,
        temporal_report,
        classification_drift_report,
        revision_report,
        cross_source_report,
    )


def _drillthrough_payloads(
    payloads: dict[str, bytes],
    tables: dict[str, pa.Table],
    packages: tuple[CanonicalPackageInput, ...],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Keep complete multi-vintage provenance outside the bounded manifest."""
    outputs = _output_inventory(payloads, tables)
    drillthrough = _source_drillthrough(tables, outputs, packages)
    if any(
        len(set(tables[kind]["source_vintage"].to_pylist())) > 1
        for kind in biff8_canonical.KINDS
        if kind in tables
    ):
        name = "source_drillthrough.json"
        payloads[name] = _encoded(drillthrough)
        # Rebuild the crate inventory without its own previous metadata file.
        del payloads["ro-crate-metadata.json"]
        payloads["ro-crate-metadata.json"] = _encoded(_ro_crate_metadata(payloads))
        outputs = _output_inventory(payloads, tables)
        binding = {
            "sha256": hashlib.sha256(payloads[name]).hexdigest(),
            "bytes": len(payloads[name]),
            "kind": "source_drillthrough",
        }
        outputs[name] = binding
        drillthrough = {
            "schema_version": "archive-govt-nz.health-source-drillthrough/v3",
            "output_name": name,
            "sha256": binding["sha256"],
            "bytes": binding["bytes"],
            "record_count": len(drillthrough["records"]),
            "scope": "complete_v2_records_in_verified_companion",
        }
    return outputs, drillthrough


def _export(
    packages: tuple[CanonicalPackageInput, ...],
    output: Path,
    *,
    write: bool,
    inputs: GoldInputs = EMPTY_GOLD_INPUTS,
) -> dict[str, Any]:
    _require(type(write) is bool)
    _require(
        isinstance(packages, tuple)
        and 0 < len(packages) <= MAX_PACKAGES
        and all(
            isinstance(package, CanonicalPackageInput)
            and package.kind
            in {"historical", "budget", "revenue", *biff8_canonical.KINDS}
            for package in packages
        )
    )
    _preflight(packages, output, inputs)
    selected: dict[str, tuple[CanonicalPackageInput, ...]] = {
        kind: tuple(package for package in packages if package.kind == kind)
        for kind in ("historical", "budget", "revenue")
    }
    tables: dict[str, pa.Table] = {}
    query_receipts: list[dict[str, Any]] = []
    product_report = biff8_canonical.initialize_gold(packages, tables, query_receipts)
    for kind, query in (
        ("historical", query_historical_observations),
        ("budget", query_nominal_budget),
        ("revenue", query_nominal_revenue),
    ):
        family_packages = selected[kind]
        if not family_packages:
            continue
        table, query_receipt = query(family_packages)
        query_receipts.append(query_receipt)
        if kind == "historical":
            coverage = summarize_historical_coverage(table)
            tables.update({"observations": table, "coverage": coverage})
            product_report[kind] = {
                "input_records": query_receipt["input_records"],
                "observation_rows": table.num_rows,
                "coverage_rows": coverage.num_rows,
                "cross_source_join": "not_performed",
                "vintage_pooling": "not_performed",
            }
        else:
            tables[kind] = table
            default_aggregation = "none"
            if kind == "budget":
                default_aggregation = "sum_within_exact_source_labels_and_unit"
            product_report[kind] = {
                "input_records": query_receipt["input_records"],
                "output_rows": table.num_rows,
                "aggregation": query_receipt.get("aggregation", default_aggregation),
                "netting": query_receipt.get("netting", "not_applicable"),
                "vintage_pooling": "not_performed",
            }
    pharmac_receipt = _add_pharmac_product(
        inputs.pharmac, tables, product_report, query_receipts
    )
    moh_receipt = _add_moh_product(inputs.moh, tables, product_report, query_receipts)
    crown_receipts = _add_crown_gold_products(
        inputs, tables, product_report, query_receipts
    )
    (
        payloads,
        plot_report,
        temporal_report,
        classification_drift_report,
        revision_report,
        cross_source_report,
    ) = _build_payloads(
        tables, product_report, query_receipts, packages, inputs.pharmac, inputs.moh
    )
    package_markers = _package_markers(query_receipts)
    quality_report = _quality_report(tables, product_report)
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES)
    outputs, drillthrough = _drillthrough_payloads(payloads, tables, packages)
    receipt = {
        "schema_version": SCHEMA,
        "status": "dry_run" if not write else "complete",
        "package_marker_sha256": package_markers,
        "input_records": sum(
            query_receipt["input_records"] for query_receipt in query_receipts
        ),
        "products": product_report,
        "pharmac_projection": pharmac_receipt,
        "moh_projection": moh_receipt,
        "crown_projection": crown_receipts["crown"],
        "fiscal_crown_projection": crown_receipts["fiscal_crown"],
        "outputs": outputs,
        "source_drillthrough": drillthrough,
        "temporal_coverage_report": temporal_report,
        "classification_drift_report": classification_drift_report,
        "revision_reconciliation_report": revision_report,
        "cross_source_period_overlap_report": cross_source_report,
        "budget_input_total_reconciliation_report": product_report.get(
            "budget", {}
        ).get("input_total_reconciliation"),
        "revenue_input_total_reconciliation_report": product_report.get(
            "revenue", {}
        ).get("input_total_reconciliation"),
        "pharmac_input_total_reconciliation_report": product_report.get(
            "pharmac", {}
        ).get("input_total_reconciliation"),
        "moh_input_gold_reconciliation_report": product_report.get("moh", {}).get(
            "input_gold_reconciliation"
        ),
        "crown_projection_gold_reconciliation_report": next(
            (
                product.get("projection_gold_reconciliation")
                for name, product in product_report.items()
                if name in {"crown_befu", "crown_hyefu", "fiscal_crown"}
                and "projection_gold_reconciliation" in product
            ),
            None,
        ),
        "plot_report": plot_report,
        "quality_report": quality_report,
        "period_ordering": (
            "canonical_period_labels_sorted_as_strings"
            if any(package.kind in biff8_canonical.KINDS for package in packages)
            else "tokens_preserved_and_sorted_as_strings"
        ),
        "cross_source_join": "not_performed",
        "vintage_pooling": "not_performed",
        "report_scope": "exact_canonical_inputs_and_source_separated_outputs",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    marker = _encoded(receipt)
    _require(
        len(marker) <= MAX_MANIFEST_BYTES
        and sum(map(len, payloads.values())) + len(marker) <= MAX_OUTPUT_BYTES
    )
    if not write:
        receipt["planned_outputs"] = receipt.pop("outputs")
        return receipt

    output.mkdir()
    try:
        for name, payload in payloads.items():
            with (output / name).open("xb") as stream:
                _require(stream.write(payload) == len(payload))
        _require({path.name for path in output.iterdir()} == set(payloads))
        for name, payload in payloads.items():
            table_name = _TABLES.get(name)
            _readback(
                output / name,
                payload,
                tables[table_name] if table_name is not None else None,
            )
        with (output / "MANIFEST.json").open("xb") as stream:
            _require(stream.write(marker) == len(marker))
        _readback(output / "MANIFEST.json", marker)
        _require(
            {path.name for path in output.iterdir()} == {*payloads, "MANIFEST.json"}
        )
    except (OSError, ValueError, TypeError, pa.ArrowException) as error:
        with (
            suppress(OSError, ValueError, TypeError),
            (output / "FAILURE.json").open("xb") as stream,
        ):
            stream.write(
                _encoded(
                    {
                        "schema_version": SCHEMA,
                        "status": "incomplete",
                        "error_type": type(error).__name__,
                        "publication": "not_performed",
                    }
                )
            )
        raise
    return receipt


def export_historical_gold(
    packages: tuple[CanonicalPackageInput, ...], output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build a dry-run-first, verified observation mart and coverage report.

    The output is a local derivative only. Every input package and its original
    remain protected, and the manifest does not assert rights or publication.
    """
    try:
        _require(
            isinstance(packages, tuple)
            and all(package.kind == "historical" for package in packages)
        )
        return _export(packages, output, write=write)
    except OSError, ValueError, TypeError, KeyError, AttributeError, pa.ArrowException:
        message = "canonical_gold_export_invalid"
        raise ValueError(message) from None


def export_canonical_gold(
    packages: tuple[CanonicalPackageInput, ...],
    output: Path,
    *,
    write: bool = False,
    inputs: GoldInputs = EMPTY_GOLD_INPUTS,
) -> dict[str, Any]:
    """Build source-separated historical, appropriation and revenue Gold tables.

    Each product is queried independently from pinned canonical packages. This
    never joins source families, pools vintages, nets revenue, or publishes.
    """
    try:
        _require(isinstance(inputs, GoldInputs))
        return _export(
            packages,
            output,
            write=write,
            inputs=inputs,
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        pa.ArrowException,
    ):
        message = "canonical_gold_export_invalid"
        raise ValueError(message) from None
