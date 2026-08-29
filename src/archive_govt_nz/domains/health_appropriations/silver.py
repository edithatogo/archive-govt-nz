"""Source-faithful Silver normalization for the donor parity database."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

_SCHEMA_VERSION = "archive-govt-nz.health-appropriations-silver/v1"
_TABLES = {
    "gdp_historical": "fiscal_context_fact",
    "health_spending_summary_befu25_data_expense_tables": "health_spending_fact",
    "health_spending_summary_hyefu24_data_expense_tables": "health_spending_fact",
    "historical_health_spending": "health_spending_fact",
    "recent_health_appropriations": "appropriation_fact",
}

SILVER_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("schema_version", pa.string()),
        ("recordset", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_observation_id", pa.string()),
        ("source_locator", pa.string()),
        ("source_vintage", pa.string()),
        ("valid_time_start", pa.date32()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("donor_table", pa.string()),
        ("donor_row_number", pa.int64()),
        ("year", pa.int32()),
        ("department", pa.string()),
        ("appropriation_name", pa.string()),
        ("functional_classification", pa.string()),
        ("amount_type", pa.string()),
        ("portfolio_name", pa.string()),
        ("measure", pa.string()),
        ("amount", pa.decimal128(20, 3)),
        ("unit", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)

LINEAGE_SCHEMA = pa.schema(
    [
        ("lineage_id", pa.string()),
        ("record_id", pa.string()),
        ("field", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_coordinate", pa.string()),
        ("raw_value", pa.string()),
        ("normalized_value", pa.string()),
        ("rule", pa.string()),
    ]
)


def _identity(*parts: object) -> str:
    value = "\x1f".join(str(part) for part in parts).encode()
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.001"))


def _record(
    table: str, row_number: int, values: dict[str, Any], context: dict[str, str]
) -> dict[str, object]:
    year = values.get("Year")
    typed_year = int(year) if year is not None else None
    record_id = _identity(context["source_sha256"], table, row_number)
    lineage_id = _identity(record_id, "lineage")
    amount: Decimal | None = None
    measure: str | None = None
    unit: str | None = None
    if "AmountThousands" in values:
        amount = _decimal(values["AmountThousands"])
        measure, unit = "appropriation_amount", "NZD_thousands"
    elif "HealthSpendingMillions" in values:
        amount = _decimal(values["HealthSpendingMillions"])
        measure, unit = "health_spending", "NZD_millions"
    elif "NominalGDPMillions" in values:
        amount = _decimal(values["NominalGDPMillions"])
        measure, unit = "nominal_gdp", "NZD_millions"
    return {
        "record_id": record_id,
        "schema_version": _SCHEMA_VERSION,
        "recordset": _TABLES[table],
        "source_object_sha256": context["source_sha256"],
        "source_observation_id": context["observation_id"],
        "source_locator": context["source_locator"],
        "source_vintage": context["source_vintage"],
        "valid_time_start": date(typed_year, 7, 1) if typed_year else None,
        "observed_at": datetime.fromisoformat(context["observed_at"]),
        "rights_state": context["rights_state"],
        "quality_flags": ["donor_observed_derivative"],
        "transformation_id": "donor-sqlite-parity/v1",
        "lineage_id": lineage_id,
        "donor_table": table,
        "donor_row_number": row_number,
        "year": typed_year,
        "department": values.get("Department"),
        "appropriation_name": values.get("AppropriationName"),
        "functional_classification": values.get("FunctionalClassification"),
        "amount_type": values.get("AmountType"),
        "portfolio_name": values.get("PortfolioName"),
        "measure": measure,
        "amount": amount,
        "unit": unit,
        "raw_values_json": json.dumps(values, sort_keys=True, separators=(",", ":")),
    }


def normalize_donor_sqlite(
    database: Path,
    output_dir: Path,
    *,
    source_sha256: str,
    observation_id: str,
    observed_at: str,
    rights_state: str = "repository_code_only",
) -> dict[str, object]:
    """Normalize all five donor tables and emit cell-addressable lineage."""
    context = {
        "source_sha256": source_sha256,
        "observation_id": observation_id,
        "source_locator": "data/processed/health_funding_nz.sqlite",
        "source_vintage": "donor-4668e6c",
        "observed_at": observed_at,
        "rights_state": rights_state,
    }
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    records: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    counts: dict[str, int] = {}
    try:
        actual = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if actual != set(_TABLES):
            raise ValueError("donor_sqlite_table_drift")
        for table in sorted(_TABLES):
            rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
            counts[table] = len(rows)
            for row_number, row in enumerate(rows, start=1):
                values = dict(row)
                record = _record(table, row_number, values, context)
                records.append(record)
                for field, raw in values.items():
                    lineage.append(
                        {
                            "lineage_id": record["lineage_id"],
                            "record_id": record["record_id"],
                            "field": field,
                            "source_object_sha256": source_sha256,
                            "source_locator": context["source_locator"],
                            "source_coordinate": f"table:{table}/row:{row_number}/column:{field}",
                            "raw_value": None if raw is None else str(raw),
                            "normalized_value": None if raw is None else str(raw),
                            "rule": "donor_sqlite_identity_or_typed_decimal/v1",
                        }
                    )
    finally:
        connection.close()
    output_dir.mkdir(parents=True, exist_ok=True)
    record_table = pa.Table.from_pylist(records, schema=SILVER_SCHEMA)
    lineage_table = pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA)
    pq.write_table(record_table, output_dir / "donor_facts.parquet", compression="zstd")
    pq.write_table(
        lineage_table, output_dir / "field_lineage.parquet", compression="zstd"
    )
    return {
        "schema_version": _SCHEMA_VERSION,
        "record_count": len(records),
        "lineage_count": len(lineage),
        "table_counts": counts,
        "outputs": ["donor_facts.parquet", "field_lineage.parquet"],
    }
