"""Universal manifest and receipt contracts."""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class SourceStatus(enum.StrEnum):
    """Lifecycle status of a registered archival source."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"
    TOMBSTONED = "tombstoned"


@dataclass(frozen=True, slots=True)
class SourceManifest:
    """Declared scope and metadata for an archival source."""

    source_id: str
    source_uri: str
    source_type: str
    agency_slug: str
    title: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: SourceStatus = SourceStatus.ACTIVE
    withdrawal_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "archive-govt-nz.source-manifest/v1"

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to JSON-serializable dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True, slots=True)
class PreservationRecord:
    """Metadata fixity descriptor for an individual preserved object."""

    record_id: str
    sha256: str
    size_bytes: int
    media_type: str
    uri: str = ""
    warc_record_id: str | None = None


@dataclass(frozen=True, slots=True)
class PreservationManifest:
    """Fixity bundle for an archival capture execution."""

    manifest_id: str
    source_id: str
    sha256_root: str
    records: tuple[PreservationRecord, ...]
    captured_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    schema_version: str = "archive-govt-nz.preservation-manifest/v1"

    @property
    def records_count(self) -> int:
        """Return total number of preserved records."""
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "source_id": self.source_id,
            "captured_at": self.captured_at,
            "sha256_root": self.sha256_root,
            "records_count": self.records_count,
            "records": [asdict(r) for r in self.records],
        }


@dataclass(frozen=True, slots=True)
class CaptureEvent:
    """Audit log entry for a source capture attempt."""

    event_id: str
    source_id: str
    status: str
    agent: str
    bytes_captured: int
    objects_created: int
    prov_activity_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    error_message: str | None = None
    schema_version: str = "archive-govt-nz.capture-event/v1"

    def to_dict(self) -> dict[str, Any]:
        """Convert capture event to dictionary."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    """Verifiable proof of remote publication to external index/repository."""

    receipt_id: str
    target_platform: str
    remote_identifier: str
    sha256_bundle_root: str
    file_count: int
    total_bytes: int
    status: str = "published"
    doi: str | None = None
    commit_pinned_url: str | None = None
    published_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    schema_version: str = "archive-govt-nz.publication-receipt/v1"

    def to_dict(self) -> dict[str, Any]:
        """Convert publication receipt to dictionary."""
        return asdict(self)
