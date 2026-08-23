"""Gold Layer: Embedded DuckDB analytical engine and cross-domain SQL views.

Provides zero-copy analytical SQL over canonical Silver Parquet datasets,
unified cross-domain entity views, and zero-copy federation hooks for
global-medicines-atlas and fyi-archive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Analytical query execution outcome containing Arrow table and metadata."""

    row_count: int
    column_names: list[str]
    arrow_table: pa.Table

    def to_pylist(self) -> list[dict[str, Any]]:
        """Convert result to list of row dictionaries."""
        return self.arrow_table.to_pylist()


class GoldAnalyticsEngine:
    """Embedded DuckDB analytical query engine for Silver and Gold datasets."""

    def __init__(self, silver_base_dir: Path | None = None) -> None:
        """Initialize in-memory DuckDB connection and attach Silver Parquet tables."""
        self.silver_base_dir = silver_base_dir or Path("data/silver")
        self.con = duckdb.connect(database=":memory:")
        self._register_silver_views()

    def _register_silver_views(self) -> None:
        """Scan silver directory and register each domain corpus as a DuckDB view."""
        if not self.silver_base_dir.exists():
            return

        registered_views: list[str] = []

        for domain_dir in self.silver_base_dir.iterdir():
            if domain_dir.is_dir():
                parquet_file = domain_dir / "corpus.parquet"
                if parquet_file.exists():
                    view_name = f"silver_{domain_dir.name}"
                    self.con.execute(
                        f"CREATE OR REPLACE VIEW {view_name} AS "
                        f"SELECT * FROM read_parquet('{parquet_file.as_posix()}')"
                    )
                    registered_views.append(view_name)

        if registered_views:
            union_sql = " UNION ALL ".join(
                f"SELECT * FROM {v}" for v in registered_views
            )
            self.con.execute(
                f"CREATE OR REPLACE VIEW v_gold_all_entities AS {union_sql}"
            )

    def register_domain_table(self, domain: str, parquet_path: Path) -> None:
        """Explicitly register or update a domain Parquet dataset as a DuckDB view."""
        view_name = f"silver_{domain}"
        self.con.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{parquet_path.as_posix()}')"
        )

    def register_federation_partner(
        self,
        partner_name: str,
        parquet_path_or_url: str | Path,
    ) -> None:
        """Attach an external federated Parquet source (e.g. global-medicines-atlas)."""
        view_name = f"fed_{partner_name.replace('-', '_')}"
        target_str = str(parquet_path_or_url)
        self.con.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{target_str}')"
        )

    def query(self, sql: str) -> QueryResult:
        """Execute a read-only SQL query and return a columnar Arrow Table."""
        rel = self.con.sql(sql)
        if rel is None:
            empty_table = pa.Table.from_pylist([])
            return QueryResult(row_count=0, column_names=[], arrow_table=empty_table)

        arrow_res = rel.arrow()
        arrow_table: pa.Table = (
            arrow_res.read_all() if hasattr(arrow_res, "read_all") else arrow_res  # type: ignore[assignment]
        )
        return QueryResult(
            row_count=arrow_table.num_rows,
            column_names=arrow_table.column_names,
            arrow_table=arrow_table,
        )

    def close(self) -> None:
        """Close database connection."""
        self.con.close()
