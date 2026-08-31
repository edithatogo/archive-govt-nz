"""Exclusive source-derived Gold tables with verified raw-input lineage."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.appropriation_analysis import (
    analyze_appropriations,
)
from archive_govt_nz.domains.health_appropriations.historical_analysis import (
    analyze_historical,
)
from archive_govt_nz.domains.health_appropriations.raw_reader import read_verified_run

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-raw-gold/v1"
_BASE_FIELDS = [
    ("record_id", pa.string()),
    ("year", pa.int32()),
    ("exact_amount", pa.decimal128(38, 17)),
    ("source_context_json", pa.string()),
    ("formula_policy", pa.string()),
    ("rounding_policy", pa.string()),
]
_SCHEMAS = {
    "historical_nominal.parquet": pa.schema(_BASE_FIELDS),
    "historical_yoy.parquet": pa.schema(
        [
            *_BASE_FIELDS,
            ("previous_exact_amount", pa.decimal128(38, 17)),
            ("yoy_percent", pa.string()),
            ("yoy_status", pa.string()),
            ("yoy_input_ids", pa.list_(pa.string())),
        ]
    ),
    "health_spending_gdp_share.parquet": pa.schema(
        [
            *_BASE_FIELDS,
            ("gdp_exact_amount", pa.decimal128(38, 17)),
            ("gdp_share_percent", pa.string()),
            ("gdp_share_status", pa.string()),
            ("gdp_input_ids", pa.list_(pa.string())),
        ]
    ),
}
_BUDGET_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_vintage", pa.string()),
        ("year", pa.int32()),
        ("functional_classification", pa.string()),
        ("amount_type", pa.string()),
        ("unit", pa.string()),
        ("total_amount_thousands", pa.decimal128(38, 3)),
        ("input_record_ids", pa.list_(pa.string())),
        ("departments", pa.list_(pa.string())),
        ("portfolios", pa.list_(pa.string())),
        ("quality_flags", pa.list_(pa.string())),
        ("formula_policy", pa.string()),
        ("period_basis", pa.string()),
        ("classification_mapping", pa.string()),
    ]
)

GOLD_TABLE_SCHEMAS = {
    **_SCHEMAS,
    "recent_classification_trends.parquet": _BUDGET_SCHEMA,
    "recent_functional_breakdown.parquet": _BUDGET_SCHEMA,
}


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, default=str, allow_nan=False
    )


def _table(rows: list[dict[str, Any]], schema: pa.Schema) -> pa.Table:
    projected = []
    for row in rows:
        values = {}
        for field in schema:
            value = row[field.name]
            if pa.types.is_decimal(field.type) and value is not None:
                value = Decimal(value)
            values[field.name] = value
        projected.append(values)
    return pa.Table.from_pylist(projected, schema=schema)


def _prepare(
    run: Path, store: Path, pin: str
) -> tuple[
    dict[str, pa.Table], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]
]:
    by_profile, lineage = read_verified_run(run, store, pin)
    if any(
        "input_profile" in row
        for name in ("budget", "historical")
        for row in by_profile[name]
    ):
        message = "reserved_input_profile_field"
        raise ValueError(message)
    historical = analyze_historical(by_profile["historical"])
    for row in historical:
        row["source_context_json"] = _json(row.pop("source_context"))
    tables = {name: _table(historical, schema) for name, schema in _SCHEMAS.items()}
    budget = analyze_appropriations(by_profile["budget"])
    tables["recent_classification_trends.parquet"] = _table(
        budget["trends"], _BUDGET_SCHEMA
    )
    tables["recent_functional_breakdown.parquet"] = _table(
        budget["breakdown"], _BUDGET_SCHEMA
    )
    selected = [
        {"input_profile": name, **row}
        for name in ("budget", "historical")
        for row in by_profile[name]
    ]
    selected.sort(key=lambda row: (row["input_profile"], row["record_id"]))
    ids = {row["record_id"] for row in selected}
    selected_lineage = [row for row in lineage if row["record_id"] in ids]
    excluded = {
        name: len(rows)
        for name, rows in by_profile.items()
        if name not in {"budget", "historical"}
    }
    return tables, selected, selected_lineage, excluded


def _write_lines(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_json(row) + "\n")


def _export(
    run: Path, store: Path, pin: str, output: Path, *, dry_run: bool
) -> dict[str, Any]:
    if output.is_symlink() or any(
        output.resolve().is_relative_to(root.resolve()) for root in (run, store)
    ):
        message = "output_overlaps_preserved_inputs"
        raise ValueError(message)
    if output.exists():
        message = "existing_gold_use_new_directory"
        raise ValueError(message)
    tables, selected, lineage, excluded = _prepare(run, store, pin)
    receipt = {
        "schema_version": SCHEMA,
        "status": "planned" if dry_run else "passed",
        "raw_manifest_sha256": pin,
        "policy": "source_derived_nominal_budget_period_basis_guarded/v1",
        "selected_facts": len(selected),
        "field_lineage": len(lineage),
        "excluded_profiles": excluded,
        "exclusion_reason": "forecast_summaries_outside_nominal_budget_analyses",
        "row_counts": {name: table.num_rows for name, table in tables.items()},
        "pyarrow_version": pa.__version__,
        "publication_state": "local_validation_only",
    }
    if dry_run:
        return receipt
    output.mkdir(parents=True, exist_ok=False)
    try:
        for name, table in tables.items():
            with (output / name).open("xb") as handle:
                pq.write_table(table, handle, compression="zstd")
        _write_lines(output / "input_records.jsonl", selected)
        _write_lines(output / "field_lineage.jsonl", lineage)
        hashes = {}
        for name in (*tables, "input_records.jsonl", "field_lineage.jsonl"):
            with (output / name).open("rb") as handle:
                hashes[name] = hashlib.file_digest(handle, "sha256").hexdigest()
        receipt["output_sha256"] = hashes
        _write_lines(output / "MANIFEST.json", [receipt])
    except Exception as error:
        _write_lines(
            output / "FAILURE.json",
            [
                {
                    "schema_version": SCHEMA,
                    "status": "failed",
                    "error_class": type(error).__name__,
                }
            ],
        )
        raise
    return receipt


def export_gold(
    run: Path, store: Path, pin: str, output: Path, *, dry_run: bool = True
) -> dict[str, Any]:
    """Preflight or create a separate local Gold package; never overwrite or publish."""
    try:
        return _export(run, store, pin, output, dry_run=dry_run)
    except Exception as error:  # noqa: BLE001 - public protocol redaction boundary
        message = "gold_export_failed:" + type(error).__name__
        raise ValueError(message) from None
