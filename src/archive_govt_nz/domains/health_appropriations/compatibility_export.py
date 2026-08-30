"""Exclusive, hash-pinned compatibility exports from canonical raw-run Parquet."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from contextlib import closing
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.raw_compatibility import (
    project_record,
)
from archive_govt_nz.domains.health_appropriations.rebuild import (
    PROFILES,
    verify_rebuild,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-raw-compatibility/v1"
_MAX_BYTES = 64 * 1024 * 1024
_MAX_ROWS = 100_000
_MAX_EXPANDED_BYTES = 256 * 1024 * 1024
_DEFINITIONS = {
    "gdp_historical": "Year INTEGER, NominalGDPMillions INTEGER",
    "health_spending_summary_befu25_data_expense_tables": (
        "Year INTEGER, HealthSpendingMillions INTEGER"
    ),
    "health_spending_summary_hyefu24_data_expense_tables": (
        "Year INTEGER, HealthSpendingMillions INTEGER"
    ),
    "historical_health_spending": "Year INTEGER, HealthSpendingMillions REAL",
    "recent_health_appropriations": (
        "Year INTEGER, Department TEXT, AppropriationName TEXT, "
        "FunctionalClassification TEXT, AmountThousands INTEGER, "
        "AmountType TEXT, PortfolioName TEXT"
    ),
}


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, default=str, allow_nan=False
    )


def _read_rows(path: Path, digest: str) -> list[dict[str, Any]]:
    payload = verified_snapshot(path, digest, max_bytes=_MAX_BYTES)
    with pq.ParquetFile(BytesIO(payload)) as file:
        metadata = file.metadata
        expanded = sum(
            metadata.row_group(i).total_byte_size
            for i in range(metadata.num_row_groups)
        )
        if metadata.num_rows > _MAX_ROWS or expanded > _MAX_EXPANDED_BYTES:
            message = "parquet_resource_limit"
            raise ValueError(message)
        return file.read().to_pylist()


def _validate_stage(
    facts: list[dict[str, Any]], lineage: list[dict[str, Any]], receipt: dict[str, Any]
) -> None:
    by_id = {row["record_id"]: row for row in facts}
    if not facts or len(by_id) != len(facts):
        message = "empty_or_duplicate_facts"
        raise ValueError(message)
    for row in facts:
        if any(
            row[key] != receipt[key]
            for key in ("source_object_sha256", "source_locator", "source_vintage")
        ):
            message = "fact_context_mismatch"
            raise ValueError(message)
    amounts: Counter[str] = Counter()
    for row in lineage:
        fact = by_id[row["record_id"]]
        if (
            any(
                row[key] != fact[key]
                for key in ("source_object_sha256", "source_locator")
            )
            or not isinstance(row["source_coordinate"], str)
            or not row["source_coordinate"]
        ):
            message = "lineage_context_mismatch"
            raise ValueError(message)
        if row["field"] == "amount":
            amounts[row["record_id"]] += 1
            if Decimal(row["normalized_value"]) != fact["amount"]:
                message = "amount_lineage_mismatch"
                raise ValueError(message)
    if any(amounts[record_id] != 1 for record_id in by_id):
        message = "missing_or_duplicate_amount_lineage"
        raise ValueError(message)


def _prepare(
    run: Path, store: Path, pin: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    receipt = verify_rebuild(run, store, pin)
    records, all_lineage = [], []
    for name, profile in PROFILES.items():
        stage = run / name
        manifest = json.loads(
            verified_snapshot(
                stage / "MANIFEST.json", receipt["stages"][name], max_bytes=_MAX_BYTES
            )
        )
        facts = _read_rows(
            stage / profile.outputs[0], manifest["output_sha256"][profile.outputs[0]]
        )
        lineage = _read_rows(
            stage / "field_lineage.parquet",
            manifest["output_sha256"]["field_lineage.parquet"],
        )
        _validate_stage(facts, lineage, manifest)
        records.extend(project_record(name, row) for row in facts)
        all_lineage.extend(lineage)
    if len({row["record_id"] for row in records}) != len(records):
        message = "duplicate_cross_stage_identity"
        raise ValueError(message)
    records.sort(key=lambda row: (row["table"], row["record_id"]))
    counts: Counter[str] = Counter()
    for row in records:
        counts[row["table"]] += 1
        row["sqlite_row_number"] = counts[row["table"]]
    all_lineage.sort(key=_json)
    verify_rebuild(run, store, pin)
    return records, all_lineage


def _write_database(path: Path, records: list[dict[str, Any]]) -> None:
    # Reserve the file before SQLite opens it. The containing directory is new.
    with path.open("xb"):
        pass
    with closing(sqlite3.connect(path)) as db, db:
        for table, definition in _DEFINITIONS.items():
            db.execute(f'CREATE TABLE "{table}" ({definition})')
            placeholders = ",".join("?" for _ in definition.split(","))
            db.executemany(
                f'INSERT INTO "{table}" VALUES ({placeholders})',  # noqa: S608 - fixed schema identifiers; values bound separately
                [row["values"] for row in records if row["table"] == table],
            )
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            message = "sqlite_integrity_failed"
            raise ValueError(message)


def _write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(_json(value) + "\n")


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
        message = "existing_export_use_new_directory"
        raise ValueError(message)
    records, lineage = _prepare(run, store, pin)
    result = {
        "schema_version": SCHEMA,
        "status": "planned" if dry_run else "passed",
        "raw_manifest_sha256": pin,
        "policy": "retain_all_raw_facts_exact_decimal_sidecar/v1",
        "facts": len(records),
        "field_lineage": len(lineage),
        "table_counts": {
            name: sum(row["table"] == name for row in records) for name in _DEFINITIONS
        },
        "representation_changes": sum(row["representation_changed"] for row in records),
        "sqlite_version": sqlite3.sqlite_version,
        "publication_state": "local_validation_only",
    }
    if dry_run:
        return result
    output.mkdir(parents=True, exist_ok=False)
    try:
        _write_database(output / "compatibility.sqlite", records)
        _write_lines(output / "records.jsonl", records)
        _write_lines(output / "field_lineage.jsonl", lineage)
        hashes = {}
        for name in ("compatibility.sqlite", "records.jsonl", "field_lineage.jsonl"):
            with (output / name).open("rb") as handle:
                hashes[name] = hashlib.file_digest(handle, "sha256").hexdigest()
        result["output_sha256"] = hashes
        _write_json(output / "MANIFEST.json", result)
    except Exception as error:
        _write_json(
            output / "FAILURE.json",
            {
                "schema_version": SCHEMA,
                "status": "failed",
                "error_class": type(error).__name__,
            },
        )
        raise
    return result


def export_compatibility(
    run: Path, store: Path, pin: str, output: Path, *, dry_run: bool = True
) -> dict[str, Any]:
    """Verify raw inputs and preflight or create a new loss-accounted local export.

    Existing/partial outputs are retained and require a new directory. This is
    not a publication operation or a substitute for source rights clearance.
    """
    try:
        return _export(run, store, pin, output, dry_run=dry_run)
    except Exception as error:  # noqa: BLE001 - public protocol redaction boundary
        message = "compatibility_export_failed:" + type(error).__name__
        raise ValueError(message) from None
