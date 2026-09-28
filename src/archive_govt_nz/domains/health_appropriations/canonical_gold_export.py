"""Exclusive local Gold derivatives from verified canonical history packages."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

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
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_OUTPUT_BYTES = 128 * 1024 * 1024
MAX_PACKAGES = 32
SCHEMA = "archive-govt-nz.health-canonical-gold/v2"
_TABLES = {
    "historical_observations.parquet": "observations",
    "historical_coverage.parquet": "coverage",
    "nominal_budget.parquet": "budget",
    "nominal_revenue.parquet": "revenue",
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
        else:
            _require(name.endswith(".png"))
            media_type = "image/png"
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
    ):
        table = tables.get(table_name)
        if table is None:
            continue
        for row in table.to_pylist():
            ids = row.get("input_record_ids")
            if ids is None:
                ids = [row.get("input_record_id")]
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
            "classification_drift",
            "revision_reconciliation",
            "cross_source_reconciliation",
        ],
    }


def _source_drillthrough(
    tables: dict[str, pa.Table], outputs: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Map each admitted input identity to exact, hash-pinned Gold rows."""
    by_record: dict[str, list[dict[str, Any]]] = {}
    for output_name, table_name in sorted(_TABLES.items()):
        table = tables.get(table_name)
        output = outputs.get(output_name)
        if table is None or output is None:
            continue
        for row_index, row in enumerate(table.to_pylist()):
            record_ids = row.get("input_record_ids")
            if record_ids is None:
                record_ids = [row.get("input_record_id")]
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
    return {
        "schema_version": "archive-govt-nz.health-source-drillthrough/v1",
        "scope": "exact_row_lineage_lookup_only",
        "row_identity": "output_sha256_and_zero_based_sorted_row_index",
        "cross_source_join": "not_performed",
        "records": [
            {
                "input_record_id": record_id,
                "output_rows": sorted(
                    output_rows,
                    key=lambda item: (item["output_name"], item["row_index"]),
                ),
            }
            for record_id, output_rows in sorted(by_record.items())
        ],
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
    crate = payloads["ro-crate-metadata.json"]
    outputs["ro-crate-metadata.json"] = {
        "sha256": hashlib.sha256(crate).hexdigest(),
        "bytes": len(crate),
        "kind": "ro_crate_metadata",
        "standards_profile": "RO-Crate 1.1",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    return outputs


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


def _preflight(packages: tuple[CanonicalPackageInput, ...], output: Path) -> None:
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


def _readback(path: Path, payload: bytes, table: pa.Table | None = None) -> None:
    _require(path.is_file() and not path.is_symlink())
    with path.open("rb") as stream:
        observed = stream.read(MAX_OUTPUT_BYTES + 1)
    _require(observed == payload)
    if table is not None:
        restored = pq.read_table(BytesIO(observed))
        _require(restored.cast(table.schema).equals(table, check_metadata=True))


def _export(
    packages: tuple[CanonicalPackageInput, ...], output: Path, *, write: bool
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
    _preflight(packages, output)
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
    payloads = {
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
    payloads.update(plot_payloads)
    payloads["ro-crate-metadata.json"] = _encoded(_ro_crate_metadata(payloads))
    quality_report = _quality_report(tables, product_report)
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES)
    outputs = _output_inventory(payloads, tables)
    receipt = {
        "schema_version": SCHEMA,
        "status": "dry_run" if not write else "complete",
        "package_marker_sha256": sorted(
            marker
            for query_receipt in query_receipts
            for marker in query_receipt["package_marker_sha256"]
        ),
        "input_records": sum(
            query_receipt["input_records"] for query_receipt in query_receipts
        ),
        "products": product_report,
        "outputs": outputs,
        "source_drillthrough": _source_drillthrough(tables, outputs),
        "temporal_coverage_report": build_temporal_coverage_report(tables),
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
    packages: tuple[CanonicalPackageInput, ...], output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build source-separated historical, appropriation and revenue Gold tables.

    Each product is queried independently from pinned canonical packages. This
    never joins source families, pools vintages, nets revenue, or publishes.
    """
    try:
        return _export(packages, output, write=write)
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
