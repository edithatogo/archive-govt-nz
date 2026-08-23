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
from archive_govt_nz.gold.search import (
    EMBEDDING_DIM,
    GoldHybridSearchEngine,
    SearchResult,
    compute_deterministic_embedding,
    cosine_similarity,
)

__all__ = [
    "CROISSANT_CONTEXT",
    "DCAT_AP_CONTEXT",
    "EMBEDDING_DIM",
    "RO_CRATE_CONTEXT",
    "DCATAPMetadataExporter",
    "GoldAnalyticsEngine",
    "GoldHybridSearchEngine",
    "QueryResult",
    "SearchResult",
    "compute_deterministic_embedding",
    "cosine_similarity",
]
