"""Local analytical Gold tables from independently verified fiscal inputs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    fiscal_cpi_benchmark as cpi,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_per_capita as population,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_share_analysis as fiscal,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
        CanonicalPackageInput,
    )

VERSION = "archive-govt-nz.fiscal-analytical-gold/v1"
_MAX_BYTES = 16 * 1024 * 1024
_MAX_ROWS = 200
_TABLES = ("nominal", "shares", "per_capita", "cpi_benchmark")
_NOMINAL_FIELDS = (
    "source_object_sha256",
    "source_vintage",
    "period_start",
    "period_end",
    "period_definition_evidence_sha256",
    "numerator_source_time_status",
    "numerator_id",
    "numerator_amount",
    "input_scale",
    "numerator_coverage",
    "accounting_basis",
    "source_quality_flags",
)

TABLE_SCHEMAS = {
    "nominal": pa.schema(
        [fiscal.SHARE_SCHEMA.field(name) for name in _NOMINAL_FIELDS],
        metadata={
            b"schema_version": b"archive-govt-nz.fiscal-health-nominal/v1",
            b"period_rule": b"treasury-fiscal-1972-2025-March-June-years/v1",
        },
    ),
    "shares": fiscal.SHARE_SCHEMA,
    "per_capita": population.SCHEMA,
    "cpi_benchmark": cpi.SCHEMA,
}


@dataclass(frozen=True)
class FiscalAnalyticalInputs:
    """Explicit source packages and retained metadata observations."""

    package: CanonicalPackageInput
    fiscal_period_evidence: Path
    population_input: population.PopulationInput
    population_period_evidence: Path
    cpi_input: cpi.CpiInput
    cpi_definition_evidence: Path


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def build_tables(
    inputs: FiscalAnalyticalInputs,
) -> tuple[dict[str, pa.Table], dict[str, Any]]:
    """Reverify Bronze/Silver inputs before deriving each analytical product."""
    shares, share_receipt = fiscal.query_fiscal_health_shares(
        inputs.package, period_evidence=inputs.fiscal_period_evidence
    )
    rates, rate_receipt = population.query_fiscal_per_capita(
        inputs.package,
        fiscal_period_evidence=inputs.fiscal_period_evidence,
        population_period_evidence=inputs.population_period_evidence,
        population_input=inputs.population_input,
    )
    benchmarks, benchmark_receipt = cpi.query_fiscal_cpi_benchmark(
        inputs.package,
        fiscal_period_evidence=inputs.fiscal_period_evidence,
        cpi_definition_evidence=inputs.cpi_definition_evidence,
        cpi_input=inputs.cpi_input,
    )
    nominal = pa.Table.from_pylist(
        [row for row in shares.to_pylist() if row["measure"] == "health_share_gdp"],
        schema=fiscal.SHARE_SCHEMA,
    )
    return {
        "nominal": nominal.select(_NOMINAL_FIELDS).replace_schema_metadata(
            TABLE_SCHEMAS["nominal"].metadata
        ),
        "shares": shares,
        "per_capita": rates,
        "cpi_benchmark": benchmarks,
    }, {
        "shares": share_receipt,
        "per_capita": rate_receipt,
        "cpi_benchmark": benchmark_receipt,
    }


def export_fiscal_analytical_gold(
    inputs: FiscalAnalyticalInputs, output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build a new local package; dry runs verify inputs without filesystem writes."""
    if write:
        _protect_inputs(inputs, output)
    tables, receipts = build_tables(inputs)
    payloads: dict[str, bytes] = {}
    inventory = {}
    for name, table in tables.items():
        if not table.schema.equals(TABLE_SCHEMAS[name], check_metadata=True):
            msg = "fiscal_gold_schema_invalid"
            raise ValueError(msg)
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink, compression="zstd", version="2.6")
        content = sink.getvalue().to_pybytes()
        if len(content) > _MAX_BYTES or table.num_rows > _MAX_ROWS:
            msg = "fiscal_gold_bounds_exceeded"
            raise ValueError(msg)
        filename = f"{name}.parquet"
        payloads[filename] = content
        inventory[name] = {
            "filename": filename,
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
            "rows": table.num_rows,
            "statuses": dict(sorted(Counter(table["status"].to_pylist()).items()))
            if "status" in table.column_names
            else {"source_observation": table.num_rows},
        }
    manifest = {
        "schema_version": VERSION,
        "tables": inventory,
        "input_receipts": receipts,
        "scope": "local_fiscal_2025_qualified_analytical_products",
        "rights": "not_evaluated",
        "publication": "not_performed",
        "health_input_cost_deflator": "not_asserted",
        "currency_iso": "not_asserted",
        "source_qualifications": "retained",
    }
    payloads["manifest.json"] = _json(manifest)
    if write:
        output.mkdir(parents=True, exist_ok=False)
        # Exclusive directory creation protects existing products. On failure retain
        # bounded partial evidence instead of deleting potentially concurrent files.
        for filename, content in payloads.items():
            with (output / filename).open("xb") as stream:
                stream.write(content)
    return {
        "schema_version": VERSION,
        "status": "written" if write else "dry_run",
        "manifest_sha256": hashlib.sha256(payloads["manifest.json"]).hexdigest(),
        "tables": inventory,
    }


def _protect_inputs(inputs: FiscalAnalyticalInputs, output: Path) -> None:
    target = output.resolve()
    protected = (
        inputs.package.root,
        inputs.package.original,
        inputs.package.raw_root,
        inputs.fiscal_period_evidence,
        inputs.population_period_evidence,
        inputs.cpi_definition_evidence,
        inputs.population_input.silver_root,
        inputs.population_input.cas_root,
        inputs.cpi_input.silver_root,
        inputs.cpi_input.cas_root,
    )
    for path in protected:
        if path is not None:
            source = path.resolve()
            if target.is_relative_to(source) or source.is_relative_to(target):
                msg = "fiscal_gold_output_overlaps_input"
                raise ValueError(msg)


def read_fiscal_analytical_gold(
    root: Path, manifest_sha256: str, *, table: str, limit: int = 200
) -> pa.Table:
    """Check package fixity and read a bounded table; do not reverify sources."""
    if table not in _TABLES or type(limit) is not int or not 1 <= limit <= _MAX_ROWS:
        msg = "fiscal_gold_query_invalid"
        raise ValueError(msg)
    expected = {"manifest.json", *(f"{name}.parquet" for name in _TABLES)}
    if (
        root.is_symlink()
        or not root.is_dir()
        or {p.name for p in root.iterdir()} != expected
    ):
        msg = "fiscal_gold_inventory_invalid"
        raise ValueError(msg)
    marker = root / "manifest.json"
    if (
        marker.is_symlink()
        or not marker.is_file()
        or marker.stat().st_size > _MAX_BYTES
    ):
        msg = "fiscal_gold_manifest_invalid"
        raise ValueError(msg)
    content = marker.read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest_sha256:
        msg = "fiscal_gold_manifest_pin_mismatch"
        raise ValueError(msg)
    manifest = json.loads(content)
    if manifest.get("schema_version") != VERSION or set(
        manifest.get("tables", {})
    ) != set(_TABLES):
        msg = "fiscal_gold_manifest_invalid"
        raise ValueError(msg)
    loaded = {
        name: _read_payload(root, name, manifest["tables"][name]) for name in _TABLES
    }
    return loaded[table].slice(0, limit)


def _read_payload(root: Path, name: str, record: dict[str, Any]) -> pa.Table:
    path = root / f"{name}.parquet"
    if (
        record.get("filename") != path.name
        or path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > _MAX_BYTES
    ):
        msg = "fiscal_gold_payload_invalid"
        raise ValueError(msg)
    payload = path.read_bytes()
    if len(payload) != record.get("bytes") or hashlib.sha256(
        payload
    ).hexdigest() != record.get("sha256"):
        msg = "fiscal_gold_payload_pin_mismatch"
        raise ValueError(msg)
    reader = pq.ParquetFile(pa.BufferReader(payload))
    if (
        reader.metadata.num_rows != record.get("rows")
        or reader.metadata.num_rows > _MAX_ROWS
    ):
        msg = "fiscal_gold_row_bounds_invalid"
        raise ValueError(msg)
    if (
        not reader.schema_arrow.equals(TABLE_SCHEMAS[name], check_metadata=True)
        or sum(
            reader.metadata.row_group(i).total_byte_size
            for i in range(reader.metadata.num_row_groups)
        )
        > _MAX_BYTES
    ):
        msg = "fiscal_gold_schema_or_expansion_invalid"
        raise ValueError(msg)
    return reader.read()
