"""Core universal data model, source identity, and registry contracts."""

from __future__ import annotations

from archive_govt_nz.core.identity import (
    SourceIdentity,
    SourceType,
    canonical_source_uri,
    parse_source_uri,
)
from archive_govt_nz.core.manifests import (
    CaptureEvent,
    PreservationManifest,
    PreservationRecord,
    PublicationReceipt,
    SourceManifest,
    SourceStatus,
)
from archive_govt_nz.core.registry import AgencyRegistry, AgencySeed

__all__ = (
    "AgencyRegistry",
    "AgencySeed",
    "CaptureEvent",
    "PreservationManifest",
    "PreservationRecord",
    "PublicationReceipt",
    "SourceIdentity",
    "SourceManifest",
    "SourceStatus",
    "SourceType",
    "canonical_source_uri",
    "parse_source_uri",
)
