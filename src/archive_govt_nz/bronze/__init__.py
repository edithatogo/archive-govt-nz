"""Bronze layer: Immutable raw ingestion models, manifests, and CAS storage.

Aligned with the Three-Strata Medallion Architecture from global-medicines-atlas.
"""

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
    EVIDENTIARY_TRUTH_SENTENCE,
    STANDARD_RECORD_LINK_COLUMNS,
    STRATA_B0_SOURCE_INDEX,
    STRATA_B1_ACQUISITION_METADATA,
    STRATA_B2_RAW_EVIDENCE,
    BronzeIngestionManifest,
    BronzePayloadFixity,
    BronzeRecord,
    BronzeSourceMetadata,
    DurabilityPolicy,
    ImmutabilityMode,
)

__all__ = [
    "BRONZE_MANIFEST_SCHEMA_V1",
    "EVIDENTIARY_TRUTH_SENTENCE",
    "STANDARD_RECORD_LINK_COLUMNS",
    "STRATA_B0_SOURCE_INDEX",
    "STRATA_B1_ACQUISITION_METADATA",
    "STRATA_B2_RAW_EVIDENCE",
    "BronzeDomainIngestor",
    "BronzeIngestionManifest",
    "BronzePayloadFixity",
    "BronzeRecord",
    "BronzeSourceMetadata",
    "DurabilityPolicy",
    "ImmutabilityMode",
    "IngestionResult",
    "build_bronze_record",
    "create_bronze_manifest",
    "verify_bronze_manifest_fixity",
]
