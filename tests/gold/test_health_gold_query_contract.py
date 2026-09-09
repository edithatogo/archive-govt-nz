"""Golden query contracts for the read-only Gold DuckDB engine."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.gold.analytics import GoldAnalyticsEngine


def _write_fact(path: Path) -> None:
    pq.write_table(
        pa.table(
            {
                "period": [2024, 2025],
                "measure": ["health_spending", "health_spending"],
                "amount": [100, 120],
                "source_record_id": ["r1", "r2"],
            }
        ),
        path,
    )


def test_gold_query_is_deterministic_and_preserves_lineage() -> None:
    """A bounded analytical query returns stable totals and source IDs."""
    with TemporaryDirectory() as directory:
        base = Path(directory) / "silver" / "health"
        base.mkdir(parents=True)
        _write_fact(base / "corpus.parquet")
        sql = """
            SELECT measure, SUM(amount) AS total,
                   array_agg(source_record_id ORDER BY period) AS source_ids
            FROM silver_health
            GROUP BY measure
            ORDER BY measure
        """
        with GoldAnalyticsEngine(Path(directory) / "silver") as engine:
            first = engine.query(sql).to_pylist()
            second = engine.query(sql).to_pylist()
        assert (
            first
            == second
            == [
                {"measure": "health_spending", "total": 220, "source_ids": ["r1", "r2"]}
            ]
        )


def test_gold_engine_does_not_allow_write_statements() -> None:
    """Analytical query entry points reject writes to the in-memory engine."""
    with GoldAnalyticsEngine() as engine:
        with pytest.raises(ValueError, match="gold_query_read_only"):
            engine.query("CREATE TABLE injected (value INTEGER)")
