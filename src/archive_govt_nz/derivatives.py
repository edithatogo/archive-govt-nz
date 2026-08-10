"""Core loss-aware JSONL and Parquet derivatives."""
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


@dataclass(frozen=True, slots=True)
class DerivativeReceipt:
    """Outputs and reconciliation evidence for one transformation."""

    jsonl_path: Path
    parquet_path: Path
    raw_ckan_path: Path
    row_count: int
    jsonl_sha256: str
    parquet_sha256: str
    raw_ckan_sha256: str
    transformation_version: str
    information_loss: tuple[str, ...]


def build_dataset_derivatives(
    records: list[dict[str, Any]],
    output_dir: Path,
    *,
    transformation_version: str = "derivatives/v1",
) -> DerivativeReceipt:
    """Write deterministic normalized JSONL and typed Parquet outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized = [_normalize(record) for record in records]
    raw_ckan = (
        json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    jsonl = b"".join(
        (
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        for row in normalized
    )
    jsonl_path = output_dir / "datasets.jsonl"
    parquet_path = output_dir / "datasets.parquet"
    raw_ckan_path = output_dir / "raw-ckan.json"
    jsonl_path.write_bytes(jsonl)
    raw_ckan_path.write_bytes(raw_ckan)
    table = pa.Table.from_pylist(normalized)
    pq.write_table(table, parquet_path, compression="zstd", use_dictionary=True)
    with duckdb.connect() as connection:
        observed = connection.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(parquet_path)]
        ).fetchone()
    row_count = int(observed[0]) if observed else 0
    return DerivativeReceipt(
        jsonl_path,
        parquet_path,
        raw_ckan_path,
        row_count,
        hashlib.sha256(jsonl).hexdigest(),
        hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        hashlib.sha256(raw_ckan).hexdigest(),
        transformation_version,
        ("unknown_ckan_fields_not_projected",),
    )


def _normalize(record: dict[str, Any]) -> dict[str, Any]:
    """Project stable fields while preserving an explicit source identifier."""
    return {
        "dataset_id": str(record.get("id", "")),
        "name": record.get("name"),
        "title": record.get("title"),
        "organization": (record.get("organization") or {}).get("name"),
        "metadata_modified": record.get("metadata_modified"),
        "resource_count": len(record.get("resources") or []),
    }
