"""Read-only DuckDB queries over verified canonical health packages."""

from __future__ import annotations

from contextlib import closing
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import duckdb
import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_verified_canonical_tables,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from collections.abc import Sequence

NOMINAL_BUDGET_SCHEMA = pa.schema(
    [
        ("source_vintage", pa.string(), False),
        ("period_token", pa.string(), False),
        ("amount_type", pa.string(), False),
        ("unit", pa.string(), False),
        ("vote", pa.string(), False),
        ("department", pa.string(), False),
        ("portfolio", pa.string(), False),
        ("source_label", pa.string(), False),
        ("total_amount", pa.decimal128(38, 18), False),
        ("input_record_ids", pa.list_(pa.string()), False),
        ("input_count", pa.int64(), False),
        ("formula_policy", pa.string(), False),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.health-canonical-consumer/v1",
        b"query": b"nominal_budget_by_source_labels",
    },
)
MAX_PACKAGES = 32

_QUERY = """
SELECT
    source_vintage,
    period_token,
    amount_type,
    unit,
    vote,
    department,
    portfolio,
    source_label,
    CAST(sum(amount) AS DECIMAL(38,18)) AS total_amount,
    list(record_id ORDER BY record_id) AS input_record_ids,
    count(*)::BIGINT AS input_count,
    'exact_sum_same_source_labels_and_unit/v1' AS formula_policy
FROM canonical_appropriations
GROUP BY ALL
ORDER BY source_vintage, period_token, amount_type, unit, vote,
         department, portfolio, source_label
"""


def _require(value: object) -> None:
    if not value:
        message = "canonical_consumer_invalid"
        raise ValueError(message)


def query_nominal_budget(
    packages: Sequence[CanonicalPackageInput],
) -> tuple[pa.Table, dict[str, Any]]:
    """Aggregate exact nominal amounts without mapping or period inference."""
    try:
        _require(isinstance(packages, tuple) and 0 < len(packages) <= MAX_PACKAGES)
        tables = []
        receipts = []
        for package in packages:
            _require(package.kind == "budget")
            canonical, receipt = read_verified_canonical_tables(package)
            table = canonical["appropriation_fact"]
            _require(
                table.schema.equals(
                    recordset_schema("appropriation_fact"), check_metadata=True
                )
            )
            tables.append(table)
            receipts.append(receipt)
        combined = pa.concat_tables(tables)
        rows = combined.to_pylist()
        ids = [row["record_id"] for row in rows]
        _require(len(ids) == len(set(ids)))
        _require(
            all(
                isinstance(row["amount"], Decimal)
                and row["period_token"]
                and row["amount_type"]
                and row["unit"]
                and row["vote"]
                and row["department"]
                and row["portfolio"]
                and row["source_label"]
                and row["currency"] is None
                and row["price_basis"] is None
                for row in rows
            )
        )
        with closing(duckdb.connect(":memory:")) as database:
            database.register("canonical_appropriations", combined)
            result = database.execute(_QUERY).to_arrow_table()
        result = result.cast(NOMINAL_BUDGET_SCHEMA)
        used = [item for row in result["input_record_ids"].to_pylist() for item in row]
        _require(sorted(used) == sorted(ids))
        return result, {
            "schema_version": "archive-govt-nz.health-canonical-consumer/v1",
            "status": "verified_local_query",
            "query": "nominal_budget_by_source_labels",
            "package_marker_sha256": sorted(
                receipt["marker_sha256"] for receipt in receipts
            ),
            "input_records": len(ids),
            "output_rows": result.num_rows,
            "currency_state": "unknown",
            "price_basis_state": "unknown",
            "period_alignment": "source_token_only",
            "classification_mapping": "not_performed",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        }
    except (
        duckdb.Error,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        pa.ArrowException,
    ):
        message = "canonical_consumer_invalid"
        raise ValueError(message) from None
