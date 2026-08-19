"""Legislation domain models, API client, normalisers, and corpus exporters."""

from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.bootstrap import (
    load_work_ids_from_batch_file,
    reconcile_historical_batches,
)
from archive_govt_nz.domains.legislation.changes import (
    LegislationChangeEvent,
    LegislationChangeReport,
)
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointCorruptError,
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.corpus import (
    ExpressionTarget,
    LegislationArchiveService,
    LegislationSyncResult,
    ManifestationTarget,
    WorkTarget,
    export_corpus_jsonl,
    export_corpus_parquet,
)
from archive_govt_nz.domains.legislation.coverage import (
    LegislationCoverageReport,
)
from archive_govt_nz.domains.legislation.discovery import build_work_inventory
from archive_govt_nz.domains.legislation.identity import (
    LegislationExpression,
    LegislationManifestation,
    LegislationWork,
)
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
)
from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    ScheduleRecord,
    SectionRecord,
    VersionStatus,
)
from archive_govt_nz.domains.legislation.normalise import (
    normalise_legislation_payload,
)
from archive_govt_nz.domains.legislation.publication import (
    prepare_legislation_publication_package,
)
from archive_govt_nz.domains.legislation.validate import (
    validate_legislation_record,
)

__all__ = [
    "ExpressionTarget",
    "LegislationArchiveService",
    "LegislationChangeEvent",
    "LegislationChangeReport",
    "LegislationCheckpointCorruptError",
    "LegislationCheckpointManager",
    "LegislationCoverageReport",
    "LegislationExpression",
    "LegislationManifestation",
    "LegislationRecord",
    "LegislationSyncResult",
    "LegislationType",
    "LegislationWork",
    "ManifestationTarget",
    "NZLegislationApiClient",
    "ScheduleRecord",
    "SectionRecord",
    "VersionStatus",
    "WorkTarget",
    "build_legislation_manifest",
    "build_work_inventory",
    "export_corpus_jsonl",
    "export_corpus_parquet",
    "load_work_ids_from_batch_file",
    "normalise_legislation_payload",
    "prepare_legislation_publication_package",
    "reconcile_historical_batches",
    "validate_legislation_record",
]
