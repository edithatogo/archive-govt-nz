"""Automated analytical columnar derivative materialization (Parquet & DuckDB)."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.object_store import ContentAddressedStore


@dataclass(frozen=True, slots=True)
class TabularDerivativeResult:
    """Outcome of materializing one tabular analytical derivative."""

    resource_id: str
    dataset_id: str
    source_sha256: str
    source_bytes: int
    derivative_path: Path
    derivative_sha256: str
    derivative_bytes: int
    row_count: int
    column_count: int
    status: str
    error: str | None = None


def convert_tabular_bytes_to_parquet(
    source_bytes: bytes,
    output_path: Path,
) -> tuple[int, int, str]:
    """Parse CSV/TSV bytes into Parquet and return (rows, cols, sha256)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table = pcsv.read_csv(io.BytesIO(source_bytes))
    pq.write_table(table, output_path, compression="snappy")
    derivative_bytes = output_path.read_bytes()
    derivative_sha256 = hashlib.sha256(derivative_bytes).hexdigest()
    return table.num_rows, table.num_columns, derivative_sha256


def materialize_tabular_derivative(
    item: dict[str, Any],
    store: ContentAddressedStore,
    output_dir: Path,
) -> TabularDerivativeResult:
    """Materialize one Parquet derivative from a captured CAS object."""
    res_id = str(item.get("resource_id") or "")
    dataset_id = str(item.get("dataset_id") or "")
    source_sha = str(item.get("sha256") or "")

    output_path = output_dir / f"{dataset_id}_{res_id}.parquet"
    source_path = store.get_path(f"sha256:{source_sha}")

    if not source_path.is_file():
        return TabularDerivativeResult(
            resource_id=res_id,
            dataset_id=dataset_id,
            source_sha256=source_sha,
            source_bytes=0,
            derivative_path=output_path,
            derivative_sha256="",
            derivative_bytes=0,
            row_count=0,
            column_count=0,
            status="source_object_missing",
            error="Source CAS object not found",
        )

    source_bytes = source_path.read_bytes()
    try:
        rows, cols, deriv_sha = convert_tabular_bytes_to_parquet(
            source_bytes, output_path
        )
        return TabularDerivativeResult(
            resource_id=res_id,
            dataset_id=dataset_id,
            source_sha256=source_sha,
            source_bytes=len(source_bytes),
            derivative_path=output_path,
            derivative_sha256=deriv_sha,
            derivative_bytes=output_path.stat().st_size,
            row_count=rows,
            column_count=cols,
            status="materialized",
        )
    except (pa.ArrowInvalid, OSError, ValueError) as exc:
        return TabularDerivativeResult(
            resource_id=res_id,
            dataset_id=dataset_id,
            source_sha256=source_sha,
            source_bytes=len(source_bytes),
            derivative_path=output_path,
            derivative_sha256="",
            derivative_bytes=0,
            row_count=0,
            column_count=0,
            status="conversion_failed",
            error=str(exc),
        )


def build_analytical_derivatives_suite(
    captures: list[dict[str, Any]],
    store: ContentAddressedStore,
    output_dir: Path,
) -> dict[str, Any]:
    """Batch-convert eligible tabular captures into columnar Parquet derivatives."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for item in captures:
        fmt = str(item.get("format") or "").upper()
        if fmt not in {"CSV", "TSV", "TAB"}:
            continue

        res = materialize_tabular_derivative(item, store, output_dir)
        results.append(
            {
                "resource_id": res.resource_id,
                "dataset_id": res.dataset_id,
                "source_sha256": res.source_sha256,
                "source_bytes": res.source_bytes,
                "derivative_path": str(res.derivative_path),
                "derivative_sha256": res.derivative_sha256,
                "derivative_bytes": res.derivative_bytes,
                "row_count": res.row_count,
                "column_count": res.column_count,
                "status": res.status,
                "error": res.error,
            }
        )

    materialized_count = sum(1 for r in results if r["status"] == "materialized")
    return {
        "schema_version": "archive-govt-nz.analytical-derivatives/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_tabular_evaluated": len(results),
        "materialized_count": materialized_count,
        "derivatives": results,
    }
