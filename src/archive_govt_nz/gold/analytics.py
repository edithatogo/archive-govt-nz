"""Gold Layer: Embedded DuckDB analytical engine and cross-domain SQL views.

Provides zero-copy analytical SQL over canonical Silver Parquet datasets,
unified cross-domain entity views, and zero-copy federation hooks for
global-medicines-atlas and fyi-archive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

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
    ) -> str:
        """Attach an external federated Parquet source (e.g. global-medicines-atlas)."""
        view_name = f"fed_{partner_name.replace('-', '_')}"
        target_str = str(parquet_path_or_url)
        self.con.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{target_str}')"
        )
        self._refresh_federated_views(view_name)
        return view_name

    def _refresh_federated_views(self, new_partner_view: str) -> None:
        """Create or update zero-copy join views against newly attached partners."""
        tables = [
            r[0]
            for r in self.con.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
        ]

        if (
            new_partner_view == "fed_global_medicines_atlas"
            and "silver_health" in tables
        ):
            self.con.execute(
                """
                CREATE OR REPLACE VIEW v_fed_health_medicines AS
                SELECT
                    h.nz_canonical_urn,
                    h.title AS nz_health_title,
                    h.domain,
                    h.source_observed_at,
                    gma.inn_name,
                    gma.atc_code,
                    gma.global_status
                FROM silver_health h
                JOIN fed_global_medicines_atlas gma
                  ON h.nz_canonical_urn = gma.nz_canonical_urn
                  OR lower(h.title) LIKE concat('%', lower(gma.inn_name), '%')
                """
            )

        if new_partner_view == "fed_fyi_archive" and "silver_legislation" in tables:
            self.con.execute(
                """
                CREATE OR REPLACE VIEW v_fed_legislation_foi AS
                SELECT
                    l.nz_canonical_urn,
                    l.title AS legislation_title,
                    l.canonical_uri,
                    fyi.request_id,
                    fyi.public_body,
                    fyi.request_status,
                    fyi.requested_at
                FROM silver_legislation l
                JOIN fed_fyi_archive fyi
                  ON fyi.referenced_urn = l.nz_canonical_urn
                  OR lower(fyi.summary) LIKE concat('%', lower(l.title), '%')
                """
            )

        if new_partner_view == "fed_reimbursement_atlas" and "silver_health" in tables:
            self.con.execute(
                """
                CREATE OR REPLACE VIEW v_fed_reimbursement_schedule AS
                SELECT
                    h.nz_canonical_urn,
                    h.title,
                    r.scheme_id,
                    r.item_code,
                    r.reimbursement_amount,
                    r.currency
                FROM silver_health h
                JOIN fed_reimbursement_atlas r
                  ON r.nz_canonical_urn = h.nz_canonical_urn
                """
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

    def __enter__(self) -> Self:
        """Enter runtime context."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit runtime context and close connection."""
        self.close()

    def close(self) -> None:
        """Close database connection."""
        self.con.close()


class GoldKnowledgeGraphIngestor:
    """Ingests downstream NLP extraction outputs into Gold analytical knowledge views."""

    @staticmethod
    def attach_nlp_extractions(
        engine: GoldAnalyticsEngine, extractions_path: Path
    ) -> None:
        """Mount extracted entity and citation Parquet feeds into DuckDB knowledge views."""
        if not extractions_path.exists():
            return

        p_str = extractions_path.as_posix()
        engine.con.execute(
            f"""
            CREATE OR REPLACE VIEW v_gold_extracted_entities AS
            SELECT
                record_id,
                title,
                category,
                publication_date,
                entities_json,
                source_urn,
                content_sha256
            FROM read_parquet('{p_str}')
            """
        )
        engine.con.execute(
            f"""
            CREATE OR REPLACE VIEW v_gold_statutory_graph AS
            SELECT
                record_id,
                title,
                category,
                publication_date,
                citations_json,
                source_urn
            FROM read_parquet('{p_str}')
            """
        )
