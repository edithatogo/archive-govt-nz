"""Bronze layer: Immutable raw ingestion models, manifests, and CAS storage.

Aligned with the Three-Strata Medallion Architecture from global-medicines-atlas.
"""

from archive_govt_nz.bronze.adapter import (
    BronzeDomainIngestor,
    IngestionResult,
)
from archive_govt_nz.bronze.attestation import (
    Ed25519Signer,
    Ed25519Verifier,
    ManifestSignature,
    seal_manifest,
    verify_manifest_seal,
)
from archive_govt_nz.bronze.fingerprint import (
    SchemaFingerprintResult,
    compute_arrow_schema_fingerprint,
    compute_json_schema_fingerprint,
    compute_xml_schema_fingerprint,
    detect_schema_drift,
)
from archive_govt_nz.bronze.heartbeat import (
    DEFAULT_HEARTBEAT_FILENAME,
    SurveillanceHeartbeat,
    SurveillanceLedger,
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
from archive_govt_nz.bronze.multihash import (
    MultiHashTriplet,
    StreamingMultiHasher,
    compute_cidv1_from_sha256,
    compute_multihash_triplet,
)
from archive_govt_nz.bronze.sniffer import (
    InvalidPayloadSignatureError,
    SniffResult,
    sniff_magic_mime,
    validate_payload_signature,
)

__all__ = [
    "BRONZE_MANIFEST_SCHEMA_V1",
    "DEFAULT_HEARTBEAT_FILENAME",
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
    "Ed25519Signer",
    "Ed25519Verifier",
    "ImmutabilityMode",
    "IngestionResult",
    "InvalidPayloadSignatureError",
    "ManifestSignature",
    "MultiHashTriplet",
    "SchemaFingerprintResult",
    "SniffResult",
    "StreamingMultiHasher",
    "SurveillanceHeartbeat",
    "SurveillanceLedger",
    "build_bronze_record",
    "compute_arrow_schema_fingerprint",
    "compute_cidv1_from_sha256",
    "compute_json_schema_fingerprint",
    "compute_multihash_triplet",
    "compute_xml_schema_fingerprint",
    "create_bronze_manifest",
    "detect_schema_drift",
    "seal_manifest",
    "sniff_magic_mime",
    "validate_payload_signature",
    "verify_bronze_manifest_fixity",
    "verify_manifest_seal",
]
