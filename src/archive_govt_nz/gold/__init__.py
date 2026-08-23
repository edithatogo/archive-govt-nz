"""Gold Layer: Analytical DuckDB engine, DCAT-AP graphs, and vector indexes."""

from archive_govt_nz.gold.analytics import (
    GoldAnalyticsEngine,
    QueryResult,
)
from archive_govt_nz.gold.dcat import (
    CROISSANT_CONTEXT,
    DCAT_AP_CONTEXT,
    RO_CRATE_CONTEXT,
    DCATAPMetadataExporter,
)

__all__ = [
    "CROISSANT_CONTEXT",
    "DCAT_AP_CONTEXT",
    "RO_CRATE_CONTEXT",
    "DCATAPMetadataExporter",
    "GoldAnalyticsEngine",
    "QueryResult",
]
