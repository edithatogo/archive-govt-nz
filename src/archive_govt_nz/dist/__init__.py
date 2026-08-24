"""Distribution & Multi-Platform Publication Hub for archive-govt-nz."""

from __future__ import annotations

from archive_govt_nz.dist.hf_adapter import (
    HFSyncOutcome,
    HuggingFaceDistributionAdapter,
)
from archive_govt_nz.dist.osf_adapter import (
    OSFDepositionOutcome,
    OSFDistributionAdapter,
)
from archive_govt_nz.dist.packaging import (
    SCHEMA_VERSION,
    PublicationItem,
    PublicationManifest,
    TargetPlatformConfig,
    build_publication_manifest,
    compute_bundle_root_digest,
    compute_file_fixity,
    generate_croissant_metadata,
    generate_ro_crate_metadata,
    save_publication_manifest,
)
from archive_govt_nz.dist.router import (
    RECEIPT_SCHEMA,
    PublicationReceipt,
    PublicationRouter,
)
from archive_govt_nz.dist.verifier import (
    FixityVerificationReport,
    PublicationVerifier,
)
from archive_govt_nz.dist.zenodo_adapter import (
    ZenodoDepositionOutcome,
    ZenodoDistributionAdapter,
)

__all__ = [
    "RECEIPT_SCHEMA",
    "SCHEMA_VERSION",
    "FixityVerificationReport",
    "HFSyncOutcome",
    "HuggingFaceDistributionAdapter",
    "OSFDepositionOutcome",
    "OSFDistributionAdapter",
    "PublicationItem",
    "PublicationManifest",
    "PublicationReceipt",
    "PublicationRouter",
    "PublicationVerifier",
    "TargetPlatformConfig",
    "ZenodoDepositionOutcome",
    "ZenodoDistributionAdapter",
    "build_publication_manifest",
    "compute_bundle_root_digest",
    "compute_file_fixity",
    "generate_croissant_metadata",
    "generate_ro_crate_metadata",
    "save_publication_manifest",
]
