"""Cross-Repository Federation and Cross-Jurisdiction Joins.

Provides pre-built zero-copy DuckDB views joining archive-govt-nz with
global-medicines-atlas (gma_*), reimbursement-atlas, and fyi-archive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.gold.analytics import GoldAnalyticsEngine, QueryResult

if TYPE_CHECKING:
    from pathlib import Path


class FederationManager:
    """Manages zero-copy federation attaches and cross-jurisdictional queries."""

    def __init__(self, engine: GoldAnalyticsEngine | None = None) -> None:
        """Initialize with an existing or new GoldAnalyticsEngine."""
        self.engine = engine or GoldAnalyticsEngine()

    def attach_global_medicines_atlas(self, parquet_path_or_url: str | Path) -> str:
        """Attach global-medicines-atlas Parquet data."""
        return self.engine.register_federation_partner(
            "global-medicines-atlas", parquet_path_or_url
        )

    def attach_fyi_archive(self, parquet_path_or_url: str | Path) -> str:
        """Attach fyi-archive Parquet data."""
        return self.engine.register_federation_partner(
            "fyi-archive", parquet_path_or_url
        )

    def attach_reimbursement_atlas(self, parquet_path_or_url: str | Path) -> str:
        """Attach reimbursement-atlas Parquet data."""
        return self.engine.register_federation_partner(
            "reimbursement-atlas", parquet_path_or_url
        )

    def query_statutes_and_medicines(self) -> QueryResult:
        """Query unified cross-jurisdiction health & medicines view."""
        sql = """
        SELECT * FROM v_fed_health_medicines
        ORDER BY source_observed_at DESC
        """
        return self.engine.query(sql)

    def query_legislation_and_foi(self) -> QueryResult:
        """Query unified legislation and OIA request disclosures view."""
        sql = """
        SELECT * FROM v_fed_legislation_foi
        ORDER BY requested_at DESC
        """
        return self.engine.query(sql)
