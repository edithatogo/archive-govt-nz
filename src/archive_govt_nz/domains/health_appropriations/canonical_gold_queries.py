"""Bounded named queries over source-separated canonical Gold fact products."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import (
    canonical_consumer as consumer,
)
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_verification as verifier,
)
from archive_govt_nz.domains.health_appropriations import moh_indicators
from archive_govt_nz.domains.health_appropriations.gold_reader import (
    MAX_BYTES,
    MAX_EXPANDED_BYTES,
    MAX_ROWS,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

VERSION = "archive-govt-nz.health-canonical-gold-query/v1"
TOOL_NAME = "health_appropriations_query_canonical_gold"
MAX_QUERY_ROWS = 200
PRODUCTS: dict[str, tuple[str, pa.Schema]] = {
    "historical": (
        "historical_observations.parquet",
        consumer.HISTORICAL_OBSERVATION_SCHEMA,
    ),
    "biff8_budget": (
        "biff8_budget.parquet",
        recordset_schema("appropriation_fact", version="v3"),
    ),
    "biff8_revenue": (
        "biff8_revenue.parquet",
        recordset_schema("revenue_fact", version="v3"),
    ),
    "budget": ("nominal_budget.parquet", consumer.NOMINAL_BUDGET_SCHEMA),
    "revenue": ("nominal_revenue.parquet", consumer.NOMINAL_REVENUE_SCHEMA),
    "pharmac": (
        "nominal_pharmaceutical_budget.parquet",
        recordset_schema("pharmaceutical_budget_fact"),
    ),
    "moh": ("published_health_indicators.parquet", moh_indicators.FACT_SCHEMA),
    "crown_befu": (
        "crown_expense_befu_2026.parquet",
        recordset_schema("fiscal_context_fact"),
    ),
    "crown_hyefu": (
        "crown_expense_hyefu_2025.parquet",
        recordset_schema("fiscal_context_fact"),
    ),
    "fiscal_crown": (
        "historical_fiscal_crown.parquet",
        recordset_schema("fiscal_context_fact"),
    ),
}
_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
_CAVEATS = {
    "classification_mapping": "not_inferred",
    "revision_interpretation": "not_assessed",
    "cross_source_comparison": "not_performed",
}


def _query_arrow_table(
    database: duckdb.DuckDBPyConnection, query: str, params: list[object]
) -> pa.Table:
    """Read a bounded SQL relation through DuckDB's Arrow relation API."""
    relation = database.sql(query, params=params)
    if relation is None:
        reason = "canonical_gold_query_relation_missing"
        raise ValueError(reason)
    return relation.to_arrow_table()


_ERRORS = frozenset(
    {
        "canonical_gold_query_package_invalid",
        "canonical_gold_query_product_unavailable",
        "canonical_gold_query_payload_invalid",
        "canonical_gold_query_resource_limit",
    }
)
INPUT_SCHEMA = {
    "$schema": _SCHEMA_URI,
    "type": "object",
    "additionalProperties": False,
    "required": ["package_dir", "manifest_sha256", "product"],
    "properties": {
        "package_dir": {"type": "string", "minLength": 1, "maxLength": 4096},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "product": {"enum": list(PRODUCTS)},
        "limit": {"type": "integer", "minimum": 1, "maximum": MAX_QUERY_ROWS},
    },
}
_PROPERTIES: dict[str, Any] = {
    "schema_version": {"const": VERSION},
    "status": {"enum": ["verified", "failed"]},
    "error": {"type": "string"},
    "product": {"enum": list(PRODUCTS)},
    "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "row_count": {"type": "integer", "minimum": 0, "maximum": MAX_QUERY_ROWS},
    "total_rows": {"type": "integer", "minimum": 0, "maximum": MAX_ROWS},
    "truncated": {"type": "boolean"},
    "rows": {"type": "array", "maxItems": MAX_QUERY_ROWS, "items": {"type": "object"}},
    "decimal_encoding": {"const": "exact_string"},
    "date_encoding": {"const": "iso8601"},
    "verification_scope": {
        "const": "pinned_package_fixity_and_selected_parquet_schema"
    },
    "source_reverification": {"const": "not_performed"},
    "publication": {"const": "not_performed"},
    "rights": {"const": "not_evaluated"},
    "package_report_caveats": {
        "type": "object",
        "required": list(_CAVEATS),
        "additionalProperties": False,
        "properties": {key: {"const": value} for key, value in _CAVEATS.items()},
    },
}
OUTPUT_SCHEMA = {
    "$schema": _SCHEMA_URI,
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "status"],
    "properties": _PROPERTIES,
    "allOf": [
        {
            "if": {"properties": {"status": {"const": "verified"}}},
            "then": {"required": [key for key in _PROPERTIES if key != "error"]},
            "else": {"required": ["error"]},
        }
    ],
}
MCP_TOOL = {
    "name": TOOL_NAME,
    "description": (
        "Query one named canonical Health Gold fact product with exact values, "
        "source identities and qualifiers. Verify package pins and the selected "
        "Parquet schema with bounded memory/rows. No arbitrary SQL, external reads, "
        "source re-verification, rights approval or publication."
    ),
    "inputSchema": INPUT_SCHEMA,
    "outputSchema": OUTPUT_SCHEMA,
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def _require(condition: object, code: str) -> None:
    if not condition:
        raise ValueError(code)


def _transport_schema(schema: pa.Schema) -> pa.Schema:
    """Use the producer's Parquet representation, including list child names."""
    buffer = BytesIO()
    pq.write_table(
        pa.Table.from_batches([], schema=schema),
        buffer,
        compression="zstd",
        use_dictionary=False,
        version="2.6",
    )
    with pq.ParquetFile(BytesIO(buffer.getvalue())) as file:
        return file.schema_arrow


def read_canonical_gold_product(root: Path, pin: str, product: str) -> pa.Table:
    """Read a full bounded typed product from an independently pinned package."""
    _require(
        type(product) is str and product in PRODUCTS,
        "canonical_gold_query_product_unavailable",
    )
    receipt = verifier.verify_canonical_gold_package(root, pin)
    _require(receipt["status"] == "verified", "canonical_gold_query_package_invalid")
    manifest = json.loads(
        verified_snapshot(
            root / "MANIFEST.json", pin, max_bytes=verifier.MAX_MANIFEST_BYTES
        )
    )
    name, schema = PRODUCTS[product]
    _require(
        product in manifest["products"] and name in manifest["outputs"],
        "canonical_gold_query_product_unavailable",
    )
    metadata = manifest["outputs"][name]
    payload = verified_snapshot(root / name, metadata["sha256"], max_bytes=MAX_BYTES)
    expected = _transport_schema(schema)
    with pq.ParquetFile(
        BytesIO(payload),
        thrift_string_size_limit=MAX_BYTES,
        thrift_container_size_limit=MAX_ROWS,
    ) as file:
        info = file.metadata
        _require(
            0 <= info.num_rows <= MAX_ROWS and 0 <= info.num_row_groups <= MAX_ROWS,
            "canonical_gold_query_resource_limit",
        )
        _require(
            file.schema_arrow.equals(expected, check_metadata=True)
            and type(metadata.get("rows")) is int
            and info.num_rows == metadata["rows"],
            "canonical_gold_query_payload_invalid",
        )
        expanded = 0
        for index in range(info.num_row_groups):
            group = info.row_group(index)
            for column_index in range(group.num_columns):
                column = group.column(column_index)
                size = column.total_uncompressed_size
                _require(
                    not column.file_path and size >= 0 and column.num_values >= 0,
                    "canonical_gold_query_payload_invalid",
                )
                if column.physical_type == "BYTE_ARRAY" and set(column.encodings) - {
                    "PLAIN",
                    "RLE",
                    "BIT_PACKED",
                }:
                    size *= max(1, column.num_values)
                expanded += size + 8 * (column.num_values + group.num_rows + 1)
        _require(expanded <= MAX_EXPANDED_BYTES, "canonical_gold_query_resource_limit")
        table = file.read(use_threads=False)
    table.validate(full=True)
    _require(table.nbytes <= MAX_EXPANDED_BYTES, "canonical_gold_query_resource_limit")
    _require(
        all(field.nullable or table[field.name].null_count == 0 for field in schema),
        "canonical_gold_query_payload_invalid",
    )
    return table


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_value(item) for item in cast("list[object]", value)]
    return value


def query_canonical_gold(
    package_dir: Path,
    manifest_sha256: str,
    *,
    product: str = "historical",
    limit: int = 50,
) -> dict[str, Any]:
    """Query stored facts without changing products or asserting source admission."""
    base: dict[str, Any] = {"schema_version": VERSION}
    if (
        type(product) is not str
        or product not in PRODUCTS
        or type(limit) is not int
        or not 1 <= limit <= MAX_QUERY_ROWS
    ):
        return {**base, "status": "failed", "error": "canonical_gold_query_invalid"}
    try:
        table = read_canonical_gold_product(package_dir, manifest_sha256, product)
        with duckdb.connect(
            ":memory:",
            config={
                "enable_external_access": False,
                "threads": 1,
                "memory_limit": f"{MAX_EXPANDED_BYTES}B",
                "max_temp_directory_size": "0B",
                "temp_directory": "",
            },
        ) as database:
            database.register("verified_facts", table)
            queried = _query_arrow_table(
                database,
                "SELECT * FROM verified_facts ORDER BY ALL ASC NULLS LAST LIMIT ?",
                [limit],
            )
        # Restore declared Arrow types, including UTC timestamps, after SQL.
        queried = queried.cast(table.schema)
        rows = [
            {key: _json_value(value) for key, value in row.items()}
            for row in queried.to_pylist()
        ]
        _require(
            len(json.dumps(rows, allow_nan=False, ensure_ascii=False).encode())
            <= verifier.MAX_MANIFEST_BYTES,
            "canonical_gold_query_resource_limit",
        )
    except (
        ValueError,
        OSError,
        TypeError,
        KeyError,
        AttributeError,
        pa.ArrowException,
        duckdb.Error,
    ) as error:
        code = str(error) if str(error) in _ERRORS else "canonical_gold_query_failed"
        return {**base, "status": "failed", "error": code}
    return {
        **base,
        "status": "verified",
        "product": product,
        "manifest_sha256": manifest_sha256,
        "row_count": len(rows),
        "total_rows": table.num_rows,
        "truncated": len(rows) < table.num_rows,
        "rows": rows,
        "decimal_encoding": "exact_string",
        "date_encoding": "iso8601",
        "verification_scope": "pinned_package_fixity_and_selected_parquet_schema",
        "source_reverification": "not_performed",
        "publication": "not_performed",
        "rights": "not_evaluated",
        "package_report_caveats": dict(_CAVEATS),
    }


def mcp_call(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate closed typed arguments before touching a package."""
    if any(Draft202012Validator(INPUT_SCHEMA).iter_errors(arguments)):
        message = "canonical_gold_query_arguments_invalid"
        raise ValueError(message)
    return query_canonical_gold(
        Path(arguments["package_dir"]),
        arguments["manifest_sha256"],
        product=arguments["product"],
        limit=arguments.get("limit", 50),
    )
