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
HISTORICAL_NOMINAL_SCHEMA = pa.schema(
    [
        ("source_vintage", pa.string(), False),
        ("period_token", pa.string(), False),
        ("unit", pa.string(), False),
        ("currency", pa.string(), False),
        ("source_label", pa.string(), False),
        ("institutional_coverage", pa.string(), True),
        ("accounting_basis", pa.string(), True),
        ("amount", pa.decimal128(38, 18), False),
        ("input_record_id", pa.string(), False),
        ("formula_policy", pa.string(), False),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.health-canonical-consumer/v1",
        b"query": b"historical_nominal_source_observations",
    },
)
HISTORICAL_OBSERVATION_SCHEMA = pa.schema(
    [
        ("source_vintage", pa.string(), False),
        ("recordset", pa.string(), False),
        ("period_token", pa.string(), False),
        ("measure", pa.string(), False),
        ("unit", pa.string(), False),
        ("currency", pa.string(), True),
        ("price_basis", pa.string(), True),
        ("base_period", pa.string(), True),
        ("denominator_definition", pa.string(), True),
        ("institutional_coverage", pa.string(), True),
        ("accounting_basis", pa.string(), True),
        ("amount", pa.decimal128(38, 18), False),
        ("source_label", pa.string(), False),
        ("source_locator", pa.string(), False),
        ("input_record_id", pa.string(), False),
        ("formula_policy", pa.string(), False),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.health-canonical-consumer/v1",
        b"query": b"historical_observation_identity_mart",
    },
)
HISTORICAL_COVERAGE_SCHEMA = pa.schema(
    [
        ("source_vintage", pa.string(), False),
        ("recordset", pa.string(), False),
        ("measure", pa.string(), False),
        ("unit", pa.string(), False),
        ("currency", pa.string(), True),
        ("price_basis", pa.string(), True),
        ("base_period", pa.string(), True),
        ("denominator_definition", pa.string(), True),
        ("observation_count", pa.int64(), False),
        ("period_tokens", pa.list_(pa.field("element", pa.string())), False),
        ("input_record_ids", pa.list_(pa.field("element", pa.string())), False),
        ("formula_policy", pa.string(), False),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.health-canonical-consumer/v1",
        b"query": b"historical_source_coverage_by_exact_context",
    },
)
NOMINAL_REVENUE_SCHEMA = pa.schema(
    [
        ("source_vintage", pa.string(), False),
        ("period_token", pa.string(), False),
        ("amount_type", pa.string(), False),
        ("unit", pa.string(), False),
        ("vote", pa.string(), False),
        ("department", pa.string(), False),
        ("revenue_type", pa.string(), False),
        ("source_label", pa.string(), False),
        ("amount", pa.decimal128(38, 18), False),
        ("input_record_id", pa.string(), False),
        ("formula_policy", pa.string(), False),
    ],
    metadata={
        b"schema_version": b"archive-govt-nz.health-canonical-consumer/v1",
        b"query": b"nominal_revenue_source_observations",
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
_HISTORICAL_QUERY = """
SELECT
    source_vintage,
    period_token,
    unit,
    currency,
    source_label,
    institutional_coverage,
    accounting_basis,
    amount,
    record_id AS input_record_id,
    'identity_projection_no_cross_source_aggregation/v1' AS formula_policy
FROM canonical_historical
ORDER BY source_vintage, period_token, source_label, record_id
"""
_HISTORICAL_OBSERVATION_QUERY = """
SELECT source_vintage, 'health_spending_fact' AS recordset, period_token,
       measure, unit, currency, price_basis, base_period,
       denominator_definition, institutional_coverage, accounting_basis,
       amount, source_label, source_locator, record_id AS input_record_id,
       'identity_projection_no_cross_source_aggregation/v1' AS formula_policy
FROM canonical_health
UNION ALL
SELECT source_vintage, 'fiscal_context_fact' AS recordset, period_token,
       measure, unit, currency, price_basis, base_period,
       denominator_definition, institutional_coverage, accounting_basis,
       amount, source_label, source_locator, record_id AS input_record_id,
       'identity_projection_no_cross_source_aggregation/v1' AS formula_policy
FROM canonical_context
ORDER BY source_vintage, recordset, period_token, measure, source_label,
         input_record_id
"""
_HISTORICAL_COVERAGE_QUERY = """
SELECT source_vintage, recordset, measure, unit, currency, price_basis,
       base_period, denominator_definition,
       count(*)::BIGINT AS observation_count,
       list_sort(list_distinct(list(period_token))) AS period_tokens,
       list(input_record_id ORDER BY input_record_id) AS input_record_ids,
       'exact_context_coverage_no_cross_source_join/v1' AS formula_policy
FROM historical_observations
GROUP BY ALL
ORDER BY source_vintage, recordset, measure, unit, currency, price_basis,
         base_period, denominator_definition
"""
_REVENUE_QUERY = """
SELECT
    source_vintage, period_token, amount_type, unit, vote, department,
    revenue_type, source_label, amount, record_id AS input_record_id,
    'identity_projection_no_expenditure_netting/v1' AS formula_policy
FROM canonical_revenue
ORDER BY source_vintage, period_token, amount_type, unit, vote, department,
         revenue_type, source_label, record_id
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
        vintages = [receipt["vintage"] for receipt in receipts]
        _require(len(vintages) == len(set(vintages)))
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


def query_historical_nominal(
    packages: Sequence[CanonicalPackageInput],
) -> tuple[pa.Table, dict[str, Any]]:
    """Expose historical nominal observations without cross-source aggregation."""
    try:
        _require(isinstance(packages, tuple) and 0 < len(packages) <= MAX_PACKAGES)
        tables = []
        receipts = []
        for package in packages:
            _require(package.kind == "historical")
            canonical, receipt = read_verified_canonical_tables(package)
            table = canonical["health_spending_fact"]
            _require(
                table.schema.equals(
                    recordset_schema("health_spending_fact"), check_metadata=True
                )
            )
            tables.append(table)
            receipts.append(receipt)
        combined = pa.concat_tables(tables)
        vintages = [receipt["vintage"] for receipt in receipts]
        _require(len(vintages) == len(set(vintages)))
        rows = combined.to_pylist()
        ids = [row["record_id"] for row in rows]
        _require(len(ids) == len(set(ids)))
        _require(
            all(
                isinstance(row["amount"], Decimal)
                and row["period_token"]
                and row["unit"]
                and row["source_label"]
                and row["currency"]
                and row["price_basis"] is None
                for row in rows
            )
        )
        with closing(duckdb.connect(":memory:")) as database:
            database.register("canonical_historical", combined)
            result = database.execute(_HISTORICAL_QUERY).to_arrow_table()
        result = result.cast(HISTORICAL_NOMINAL_SCHEMA)
        _require(sorted(result["input_record_id"].to_pylist()) == sorted(ids))
        return result, {
            "schema_version": "archive-govt-nz.health-canonical-consumer/v1",
            "status": "verified_local_query",
            "query": "historical_nominal_source_observations",
            "package_marker_sha256": sorted(
                receipt["marker_sha256"] for receipt in receipts
            ),
            "input_records": len(ids),
            "output_rows": result.num_rows,
            "aggregation": "none",
            "currency_state": "source_assertion_preserved",
            "price_basis_state": "unknown",
            "period_alignment": "source_token_only",
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


def query_historical_observations(
    packages: Sequence[CanonicalPackageInput],
) -> tuple[pa.Table, dict[str, Any]]:
    """Expose health and fiscal-context facts without joining or pooling them."""
    try:
        _require(isinstance(packages, tuple) and 0 < len(packages) <= MAX_PACKAGES)
        health_tables = []
        context_tables = []
        receipts = []
        for package in packages:
            _require(package.kind == "historical")
            canonical, receipt = read_verified_canonical_tables(package)
            health = canonical["health_spending_fact"]
            context = canonical["fiscal_context_fact"]
            _require(
                health.schema.equals(
                    recordset_schema("health_spending_fact"), check_metadata=True
                )
                and context.schema.equals(
                    recordset_schema("fiscal_context_fact"), check_metadata=True
                )
            )
            health_tables.append(health)
            context_tables.append(context)
            receipts.append(receipt)
        vintages = [receipt["vintage"] for receipt in receipts]
        _require(len(vintages) == len(set(vintages)))
        health = pa.concat_tables(health_tables)
        context = pa.concat_tables(context_tables)
        source_ids = [
            row["record_id"] for table in (health, context) for row in table.to_pylist()
        ]
        _require(len(source_ids) == len(set(source_ids)))
        _require(
            all(
                isinstance(row["amount"], Decimal)
                and row["period_token"]
                and row["measure"]
                and row["unit"]
                and row["source_label"]
                and row["source_locator"]
                for table in (health, context)
                for row in table.to_pylist()
            )
        )
        with closing(duckdb.connect(":memory:")) as database:
            database.register("canonical_health", health)
            database.register("canonical_context", context)
            observations = (
                database.execute(_HISTORICAL_OBSERVATION_QUERY)
                .to_arrow_table()
                .cast(HISTORICAL_OBSERVATION_SCHEMA)
            )
        observed_ids = sorted(observations["input_record_id"].to_pylist())
        _require(observed_ids == sorted(source_ids))
        coverage = summarize_historical_coverage(observations)
        return observations, {
            "schema_version": "archive-govt-nz.health-canonical-consumer/v1",
            "status": "verified_local_query",
            "query": "historical_observation_identity_mart",
            "package_marker_sha256": sorted(
                receipt["marker_sha256"] for receipt in receipts
            ),
            "input_records": len(source_ids),
            "output_rows": observations.num_rows,
            "coverage_rows": coverage.num_rows,
            "cross_source_join": "not_performed",
            "vintage_pooling": "not_performed",
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


def summarize_historical_coverage(
    observations: pa.Table,
) -> pa.Table:
    """Report period coverage while keeping exact measures and bases separate."""
    try:
        _require(
            isinstance(observations, pa.Table)
            and observations.schema.equals(
                HISTORICAL_OBSERVATION_SCHEMA, check_metadata=True
            )
            and observations.num_rows > 0
        )
        rows = observations.to_pylist()
        ids = [row["input_record_id"] for row in rows]
        _require(
            len(ids) == len(set(ids))
            and all(
                row["period_token"]
                and row["source_vintage"]
                and row["measure"]
                and row["unit"]
                for row in rows
            )
        )
        with closing(duckdb.connect(":memory:")) as database:
            database.register("historical_observations", observations)
            result = database.execute(_HISTORICAL_COVERAGE_QUERY).to_arrow_table()
        result = result.cast(HISTORICAL_COVERAGE_SCHEMA)
        _require(
            sorted(
                item
                for group in result["input_record_ids"].to_pylist()
                for item in group
            )
            == sorted(ids)
        )
    except (
        duckdb.Error,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        pa.ArrowException,
    ):
        message = "canonical_consumer_invalid"
        raise ValueError(message) from None
    else:
        return result


def query_nominal_revenue(
    packages: Sequence[CanonicalPackageInput],
) -> tuple[pa.Table, dict[str, Any]]:
    """Expose verified revenue observations without appropriation netting."""
    try:
        _require(isinstance(packages, tuple) and 0 < len(packages) <= MAX_PACKAGES)
        tables = []
        receipts = []
        for package in packages:
            _require(package.kind == "revenue")
            canonical, receipt = read_verified_canonical_tables(package)
            table = canonical["revenue_fact"]
            _require(
                table.schema.equals(
                    recordset_schema("revenue_fact"), check_metadata=True
                )
            )
            tables.append(table)
            receipts.append(receipt)
        combined = pa.concat_tables(tables)
        vintages = [receipt["vintage"] for receipt in receipts]
        _require(len(vintages) == len(set(vintages)))
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
                and row["revenue_type"]
                and row["source_label"]
                and row["currency"] is None
                and row["price_basis"] is None
                for row in rows
            )
        )
        with closing(duckdb.connect(":memory:")) as database:
            database.register("canonical_revenue", combined)
            result = database.execute(_REVENUE_QUERY).to_arrow_table()
        result = result.cast(NOMINAL_REVENUE_SCHEMA)
        _require(sorted(result["input_record_id"].to_pylist()) == sorted(ids))
        return result, {
            "schema_version": "archive-govt-nz.health-canonical-consumer/v1",
            "status": "verified_local_query",
            "query": "nominal_revenue_source_observations",
            "package_marker_sha256": sorted(
                receipt["marker_sha256"] for receipt in receipts
            ),
            "input_records": len(ids),
            "output_rows": result.num_rows,
            "aggregation": "none",
            "netting": "prohibited",
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
