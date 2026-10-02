"""Exclusive local Gold derivatives from verified canonical history packages."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    crown_expense_canonical_projection,
    fiscal_crown_canonical_projection,
    hyefu_crown_expense_canonical_projection,
)
from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    query_historical_observations,
    query_nominal_budget,
    query_nominal_revenue,
    summarize_historical_coverage,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (
    build_discrete_plots,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_verified_canonical_tables,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    MohGoldInput,
    project_moh_indicators,
)
from archive_govt_nz.domains.health_appropriations.pharmac_canonical_projection import (
    project_pharmac_cpb,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_OUTPUT_BYTES = 128 * 1024 * 1024
MAX_PACKAGES = 32
MIN_DISTINCT_CLASSIFICATION_LABELS = 2
MIN_REVISION_VINTAGES = 2
SCHEMA = "archive-govt-nz.health-canonical-gold/v2"


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


def _source_drillthrough(
    tables: dict[str, pa.Table],
    outputs: dict[str, dict[str, Any]],
    packages: tuple[CanonicalPackageInput, ...],
) -> dict[str, Any]:
    """Link Gold rows to canonical source coordinates and exact source objects."""
    coordinates_by_record: dict[str, list[dict[str, Any]]] = {}
    for package in packages:
        canonical, _receipt = read_verified_canonical_tables(package)
        for lineage in canonical["field_lineage"].to_pylist():
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
        if table is None or output is None:
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
    return {
        "schema_version": "archive-govt-nz.health-revision-reconciliation/v1",
        "scope": (
            "same_recordset_measure_source_label_and_exact_context_period_"
            "across_observed_vintages"
        ),
        "key_fields": list(context_fields),
        "completeness": "historical_budget_revenue_product_rows",
        "shared_series_period_count": shared_groups,
        "unchanged_series_period_count": unchanged_groups,
        "ambiguous_series_period_count": ambiguous_groups,
        "changed_candidate_count": len(candidates),
        "difference_interpretation": "not_assessed",
        "other_product_revisions": "not_assessed",
        "cross_source_comparison": "not_performed",
        "product_revisions": {"budget": budget_report, "revenue": revenue_report},
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
            groups.setdefault(key, {}).setdefault(vintage, []).append(
                {"value": value, "record_ids": sorted(ids)}
            )

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
        candidates.append(
            {
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
        )
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


def _build_payloads(
    tables: dict[str, pa.Table],
    products: dict[str, dict[str, Any]],
    query_receipts: list[dict[str, Any]],
) -> tuple[
    dict[str, bytes], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
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
    payloads["historical_revision_reconciliation.json"] = _encoded(revision_report)
    payloads["ro-crate-metadata.json"] = _encoded(_ro_crate_metadata(payloads))
    return (
        payloads,
        plot_report,
        temporal_report,
        classification_drift_report,
        revision_report,
    )


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
            and package.kind in {"historical", "budget", "revenue"}
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
    product_report: dict[str, dict[str, Any]] = {}
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
    ) = _build_payloads(tables, product_report, query_receipts)
    package_markers = _package_markers(query_receipts)
    quality_report = _quality_report(tables, product_report)
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES)
    outputs = _output_inventory(payloads, tables)
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
        "source_drillthrough": _source_drillthrough(tables, outputs, packages),
        "temporal_coverage_report": temporal_report,
        "classification_drift_report": classification_drift_report,
        "revision_reconciliation_report": revision_report,
        "plot_report": plot_report,
        "quality_report": quality_report,
        "period_ordering": "tokens_preserved_and_sorted_as_strings",
        "cross_source_join": "not_performed",
        "vintage_pooling": "not_performed",
        "report_scope": "exact_canonical_inputs_and_source_separated_outputs",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    marker = _encoded(receipt)
    _require(sum(map(len, payloads.values())) + len(marker) <= MAX_OUTPUT_BYTES)
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
