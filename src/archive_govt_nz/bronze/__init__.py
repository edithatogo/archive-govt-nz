"""Bronze layer: Immutable raw ingestion models, manifests, and CAS storage."""

from archive_govt_nz.bronze.adapter import (
    BronzeDomainIngestor,
    IngestionResult,
)
from archive_govt_nz.bronze.manifest import (
    build_bronze_record,
    create_bronze_manifest,
    verify_bronze_manifest_fixity,
)
from archive_govt_nz.bronze.models import (
    BRONZE_MANIFEST_SCHEMA_V1,
    BronzeIngestionManifest,
    BronzePayloadFixity,
    BronzeRecord,
    BronzeSourceMetadata,
)

__all__ = [
    "BRONZE_MANIFEST_SCHEMA_V1",
    "BronzeDomainIngestor",
    "BronzeIngestionManifest",
    "BronzePayloadFixity",
    "BronzeRecord",
    "BronzeSourceMetadata",
    "IngestionResult",
    "build_bronze_record",
    "create_bronze_manifest",
    "verify_bronze_manifest_fixity",
]
