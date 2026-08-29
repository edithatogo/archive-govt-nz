"""Dedicated health-appropriations Silver contracts."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations.silver import (
    normalize_donor_sqlite,
)


def _database(path: Path, *, omit: str | None = None) -> None:
    definitions = {
        "gdp_historical": 'CREATE TABLE gdp_historical ("Year" INTEGER, "NominalGDPMillions" INTEGER)',
        "health_spending_summary_befu25_data_expense_tables": 'CREATE TABLE health_spending_summary_befu25_data_expense_tables ("Year" INTEGER, "HealthSpendingMillions" INTEGER)',
        "health_spending_summary_hyefu24_data_expense_tables": 'CREATE TABLE health_spending_summary_hyefu24_data_expense_tables ("Year" INTEGER, "HealthSpendingMillions" INTEGER)',
        "historical_health_spending": 'CREATE TABLE historical_health_spending ("Year" INTEGER, "HealthSpendingMillions" REAL)',
        "recent_health_appropriations": 'CREATE TABLE recent_health_appropriations ("Year" INTEGER, "Department" TEXT, "AppropriationName" TEXT, "FunctionalClassification" TEXT, "AmountThousands" INTEGER, "AmountType" TEXT, "PortfolioName" TEXT)',
    }
    with sqlite3.connect(path) as connection:
        for table, statement in definitions.items():
            if table == omit:
                continue
            connection.execute(statement)
            if table == "gdp_historical":
                connection.execute(f"INSERT INTO {table} VALUES (2025, 400000)")
            elif table == "recent_health_appropriations":
                connection.execute(
                    f"INSERT INTO {table} VALUES (2025, 'Health', 'Care', 'Health', 123, 'Actuals', 'Health')"
                )
            else:
                connection.execute(f"INSERT INTO {table} VALUES (2025, 100.5)")


def _normalize(database: Path, output: Path) -> dict[str, object]:
    return normalize_donor_sqlite(
        database,
        output,
        source_sha256="a" * 64,
        observation_id="obs-1",
        observed_at="2026-08-29T00:00:00Z",
    )


def test_all_donor_rows_have_typed_facts_and_field_lineage(tmp_path: Path) -> None:
    database = tmp_path / "donor.sqlite"
    _database(database)
    receipt = _normalize(database, tmp_path / "silver")
    facts = pq.read_table(tmp_path / "silver" / "donor_facts.parquet")
    lineage = pq.read_table(tmp_path / "silver" / "field_lineage.parquet")
    assert receipt["record_count"] == 5
    assert facts.num_rows == 5
    assert lineage.num_rows == 15
    assert set(facts.column("recordset").to_pylist()) == {
        "appropriation_fact",
        "fiscal_context_fact",
        "health_spending_fact",
    }
    assert facts.schema.field("amount").type.precision == 20
    assert all(facts.column("source_object_sha256").to_pylist())


def test_silver_output_is_deterministic(tmp_path: Path) -> None:
    database = tmp_path / "donor.sqlite"
    _database(database)
    _normalize(database, tmp_path / "one")
    _normalize(database, tmp_path / "two")
    for name in ("donor_facts.parquet", "field_lineage.parquet"):
        left = hashlib.sha256((tmp_path / "one" / name).read_bytes()).digest()
        right = hashlib.sha256((tmp_path / "two" / name).read_bytes()).digest()
        assert left == right


def test_silver_fails_closed_on_table_drift(tmp_path: Path) -> None:
    database = tmp_path / "donor.sqlite"
    _database(database, omit="gdp_historical")
    with pytest.raises(ValueError, match="donor_sqlite_table_drift"):
        _normalize(database, tmp_path / "silver")
