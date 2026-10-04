"""Named read-only DuckDB queries over independently pinned fiscal Gold."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import fiscal_analytical_gold as gold

VERSION = "archive-govt-nz.fiscal-analytical-query/v1"
TOOL_NAME = "health_appropriations_query_fiscal_gold"
_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
_MAX_ROWS = 200
_ERRORS = frozenset(
    {
        "fiscal_gold_query_invalid",
        "fiscal_gold_inventory_invalid",
        "fiscal_gold_manifest_invalid",
        "fiscal_gold_manifest_pin_mismatch",
        "fiscal_gold_payload_invalid",
        "fiscal_gold_payload_pin_mismatch",
        "fiscal_gold_row_bounds_invalid",
        "fiscal_gold_schema_or_expansion_invalid",
    }
)
INPUT_SCHEMA = {
    "$schema": _SCHEMA_URI,
    "type": "object",
    "additionalProperties": False,
    "required": ["package_dir", "manifest_sha256", "table"],
    "properties": {
        "package_dir": {"type": "string", "minLength": 1, "maxLength": 4096},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "table": {"enum": list(gold.TABLE_SCHEMAS)},
        "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS},
    },
}
OUTPUT_SCHEMA = {
    "$schema": _SCHEMA_URI,
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "status"],
    "properties": {
        "schema_version": {"const": VERSION},
        "status": {"enum": ["verified", "failed"]},
        "error": {"type": "string"},
        "table": {"enum": list(gold.TABLE_SCHEMAS)},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "row_count": {"type": "integer", "minimum": 0, "maximum": _MAX_ROWS},
        "total_rows": {"type": "integer", "minimum": 0, "maximum": _MAX_ROWS},
        "truncated": {"type": "boolean"},
        "rows": {
            "type": "array",
            "maxItems": _MAX_ROWS,
            "items": {
                "type": "object",
                "additionalProperties": {
                    "type": ["string", "null", "array"],
                    "items": {"type": ["string", "null"]},
                },
            },
        },
        "decimal_encoding": {"const": "exact_string"},
        "date_encoding": {"const": "iso8601"},
        "verification_scope": {"const": "pinned_gold_payloads_and_schemas"},
        "source_reverification": {"const": "not_performed"},
        "publication": {"const": "not_performed"},
        "rights": {"const": "not_evaluated"},
    },
    "allOf": [
        {
            "if": {"properties": {"status": {"const": "verified"}}},
            "then": {
                "required": [
                    "table",
                    "manifest_sha256",
                    "row_count",
                    "total_rows",
                    "truncated",
                    "rows",
                    "decimal_encoding",
                    "date_encoding",
                    "verification_scope",
                    "source_reverification",
                    "publication",
                    "rights",
                ]
            },
            "else": {"required": ["error"]},
        }
    ],
}
MCP_TOOL = {
    "name": TOOL_NAME,
    "description": (
        "Verify a pinned local fiscal analytical Gold package and query one named "
        "table with bounded rows. Preserve exact Decimal strings, dates, source IDs, "
        "qualifications and exclusion statuses. No arbitrary SQL, external reads, "
        "source re-verification, rights evaluation or publication."
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


def query_fiscal_analytical_gold(
    package_dir: Path, manifest_sha256: str, *, table: str = "nominal", limit: int = 50
) -> dict[str, Any]:
    """Return a closed, bounded query with exact JSON encodings and scoped fixity."""
    envelope: dict[str, Any] = {"schema_version": VERSION}
    if (
        table not in gold.TABLE_SCHEMAS
        or type(limit) is not int
        or not 1 <= limit <= _MAX_ROWS
    ):
        return {**envelope, "status": "failed", "error": "fiscal_gold_query_invalid"}
    try:
        verified = gold.read_fiscal_analytical_gold(
            package_dir, manifest_sha256, table=table
        )
        with duckdb.connect(
            ":memory:", config={"enable_external_access": False}
        ) as database:
            database.register("verified_table", verified)
            sql = (
                "SELECT * FROM verified_table ORDER BY period_end LIMIT ?"
                if table == "nominal"
                else "SELECT * FROM verified_table ORDER BY period_end, measure LIMIT ?"
            )
            queried = database.execute(sql, [limit]).to_arrow_table()
        rows = [
            {
                key: str(value) if isinstance(value, (Decimal, date)) else value
                for key, value in row.items()
            }
            for row in queried.to_pylist()
        ]
    except (
        ValueError,
        OSError,
        TypeError,
        KeyError,
        AttributeError,
        pa.ArrowException,
        duckdb.Error,
    ) as error:
        code = str(error) if str(error) in _ERRORS else "fiscal_gold_query_failed"
        return {**envelope, "status": "failed", "error": code}
    return {
        **envelope,
        "status": "verified",
        "table": table,
        "manifest_sha256": manifest_sha256,
        "row_count": len(rows),
        "total_rows": verified.num_rows,
        "truncated": len(rows) < verified.num_rows,
        "rows": rows,
        "decimal_encoding": "exact_string",
        "date_encoding": "iso8601",
        "verification_scope": "pinned_gold_payloads_and_schemas",
        "source_reverification": "not_performed",
        "publication": "not_performed",
        "rights": "not_evaluated",
    }


def mcp_call(arguments: dict[str, Any]) -> dict[str, Any]:
    """Reject malformed tool arguments before local package I/O."""
    if any(Draft202012Validator(INPUT_SCHEMA).iter_errors(arguments)):
        msg = "fiscal_gold_query_arguments_invalid"
        raise ValueError(msg)
    return query_fiscal_analytical_gold(
        Path(arguments["package_dir"]),
        arguments["manifest_sha256"],
        table=arguments["table"],
        limit=arguments.get("limit", 50),
    )
