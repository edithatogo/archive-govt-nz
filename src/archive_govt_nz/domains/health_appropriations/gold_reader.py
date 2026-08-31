"""Bounded hash-pinned Gold snapshots for local plot consumers."""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.gold_export import (
    GOLD_TABLE_SCHEMAS,
    SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ROWS = 100_000
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
_SIDECARS = {"input_records.jsonl", "field_lineage.jsonl"}
_FILES = set(GOLD_TABLE_SCHEMAS) | _SIDECARS


def _snapshots(root: Path, pin: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    manifest = json.loads(
        verified_snapshot(root / "MANIFEST.json", pin, max_bytes=MAX_BYTES)
    )
    if (
        manifest["schema_version"] != SCHEMA
        or manifest["status"] != "passed"
        or manifest["policy"] != "source_derived_nominal_budget_period_basis_guarded/v1"
        or set(manifest["output_sha256"]) != _FILES
        or set(manifest["row_counts"]) != set(GOLD_TABLE_SCHEMAS)
    ):
        message = "invalid_gold_manifest"
        raise ValueError(message)
    if {path.name for path in root.iterdir()} != _FILES | {"MANIFEST.json"}:
        message = "gold_file_set"
        raise ValueError(message)
    payloads = {}
    total = 0
    for name in sorted(_FILES | {"MANIFEST.json"}):
        path = root / name
        if path.is_symlink() or not path.is_file():
            message = "gold_file_type"
            raise ValueError(message)
        digest = pin if name == "MANIFEST.json" else manifest["output_sha256"][name]
        payload = verified_snapshot(path, digest, max_bytes=MAX_BYTES)
        total += len(payload)
        if total > MAX_TOTAL_BYTES:
            message = "gold_resource_limit"
            raise ValueError(message)
        payloads[name] = payload
    return payloads, manifest


def _tables(
    payloads: dict[str, bytes], manifest: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    tables = {}
    for name, schema in GOLD_TABLE_SCHEMAS.items():
        with pq.ParquetFile(BytesIO(payloads[name])) as file:
            metadata = file.metadata
            expanded = sum(
                metadata.row_group(i).total_byte_size
                for i in range(metadata.num_row_groups)
            )
            if metadata.num_rows > MAX_ROWS or expanded > MAX_EXPANDED_BYTES:
                message = "gold_resource_limit"
                raise ValueError(message)
            if (
                file.schema_arrow != schema
                or metadata.num_rows != manifest["row_counts"][name]
            ):
                message = "gold_table_contract"
                raise ValueError(message)
            tables[name] = file.read().to_pylist()
    return tables


def _sidecars(payloads: dict[str, bytes], manifest: dict[str, Any]) -> set[str]:
    rows = {}
    for name in sorted(_SIDECARS):
        lines = payloads[name].splitlines()
        if len(lines) > MAX_ROWS:
            message = "gold_resource_limit"
            raise ValueError(message)
        rows[name] = [json.loads(line) for line in lines]
    facts, lineage = rows["input_records.jsonl"], rows["field_lineage.jsonl"]
    if (
        len(facts) != manifest["selected_facts"]
        or len(lineage) != manifest["field_lineage"]
    ):
        message = "gold_sidecar_contract"
        raise ValueError(message)
    ids = {row["record_id"] for row in facts}
    if len(ids) != len(facts) or {row["record_id"] for row in lineage} != ids:
        message = "gold_input_identity"
        raise ValueError(message)
    return ids


def read_verified_gold(
    root: Path, pin: str
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Verify all eight package files and consume only capped in-memory snapshots.

    Checks integrity, Arrow types, counts and input-ID closure, not a fresh raw
    extraction or rights decision. The caller pins a previously reviewed Gold
    manifest. Declared Parquet resource limits are not a process sandbox.
    """
    payloads, manifest = _snapshots(root, pin)
    tables = _tables(payloads, manifest)
    ids = _sidecars(payloads, manifest)
    used = set()
    for rows in tables.values():
        for row in rows:
            if "record_id" in row:
                used.add(row["record_id"])
            for key, value in row.items():
                if key.endswith("_input_ids") or key == "input_record_ids":
                    used.update(value)
    if used != ids:
        message = "gold_input_identity"
        raise ValueError(message)
    verified_snapshot(root / "MANIFEST.json", pin, max_bytes=MAX_BYTES)
    return tables, manifest
