"""Data models for Bronze ingestion tier records and manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BRONZE_MANIFEST_SCHEMA_V1 = "archive-govt-nz.bronze-ingestion-manifest/v1"


@dataclass(frozen=True, slots=True)
class BronzePayloadFixity:
    """Cryptographic fixity and storage references for an immutable Bronze payload."""

    sha256: str
    blake3: str
    size_bytes: int
    cas_path: str
    warc_record_id: str | None = None
    media_type: str = "application/octet-stream"

    def to_dict(self) -> dict[str, Any]:
        """Convert to primitive dictionary."""
        return {
            "sha256": self.sha256,
            "blake3": self.blake3,
            "size_bytes": self.size_bytes,
            "cas_path": self.cas_path,
            "warc_record_id": self.warc_record_id,
            "media_type": self.media_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BronzePayloadFixity:
        """Construct instance from dictionary."""
        return cls(
            sha256=str(data["sha256"]),
            blake3=str(data["blake3"]),
            size_bytes=int(data["size_bytes"]),
            cas_path=str(data["cas_path"]),
            warc_record_id=str(data["warc_record_id"])
            if data.get("warc_record_id")
            else None,
            media_type=str(data.get("media_type") or "application/octet-stream"),
        )


@dataclass(frozen=True, slots=True)
class BronzeSourceMetadata:
    """Protocol metadata and HTTP evidence for the ingested source resource."""

    source_url: str
    observed_at: str
    status_code: int = 200
    content_type: str = "application/octet-stream"
    encoding: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    rate_limit_remaining: int | None = None
    rate_limit_reset: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to primitive dictionary."""
        return {
            "source_url": self.source_url,
            "observed_at": self.observed_at,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "encoding": self.encoding,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "headers": dict(self.headers),
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset": self.rate_limit_reset,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BronzeSourceMetadata:
        """Construct instance from dictionary."""
        return cls(
            source_url=str(data["source_url"]),
            observed_at=str(data["observed_at"]),
            status_code=int(data.get("status_code", 200)),
            content_type=str(data.get("content_type", "application/octet-stream")),
            encoding=str(data["encoding"]) if data.get("encoding") else None,
            etag=str(data["etag"]) if data.get("etag") else None,
            last_modified=str(data["last_modified"])
            if data.get("last_modified")
            else None,
            headers=dict(data.get("headers") or {}),
            rate_limit_remaining=int(data["rate_limit_remaining"])
            if data.get("rate_limit_remaining") is not None
            else None,
            rate_limit_reset=int(data["rate_limit_reset"])
            if data.get("rate_limit_reset") is not None
            else None,
        )


@dataclass(frozen=True, slots=True)
class BronzeRecord:
    """An individual observed Bronze record representing an ingested raw payload."""

    record_id: str
    domain: str
    source_metadata: BronzeSourceMetadata
    fixity: BronzePayloadFixity
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to primitive dictionary."""
        return {
            "record_id": self.record_id,
            "domain": self.domain,
            "source_metadata": self.source_metadata.to_dict(),
            "fixity": self.fixity.to_dict(),
            "custom_metadata": dict(self.custom_metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BronzeRecord:
        """Construct instance from dictionary."""
        return cls(
            record_id=str(data["record_id"]),
            domain=str(data["domain"]),
            source_metadata=BronzeSourceMetadata.from_dict(data["source_metadata"]),
            fixity=BronzePayloadFixity.from_dict(data["fixity"]),
            custom_metadata=dict(data.get("custom_metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class BronzeIngestionManifest:
    """A versioned, verifiable ingestion manifest for a batch of Bronze captures."""

    manifest_id: str
    batch_id: str
    domain: str
    created_at: str
    records: list[BronzeRecord]
    schema_version: str = BRONZE_MANIFEST_SCHEMA_V1
    sha256_manifest: str | None = None

    @property
    def records_count(self) -> int:
        """Return the number of records in this manifest."""
        return len(self.records)

    @property
    def total_bytes(self) -> int:
        """Return the sum of raw payload bytes in this manifest."""
        return sum(rec.fixity.size_bytes for rec in self.records)

    def to_dict(self) -> dict[str, Any]:
        """Convert to primitive dictionary."""
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "batch_id": self.batch_id,
            "domain": self.domain,
            "created_at": self.created_at,
            "records_count": self.records_count,
            "total_bytes": self.total_bytes,
            "sha256_manifest": self.sha256_manifest,
            "records": [rec.to_dict() for rec in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BronzeIngestionManifest:
        """Construct instance from dictionary."""
        records = [BronzeRecord.from_dict(item) for item in data.get("records", [])]
        return cls(
            manifest_id=str(data["manifest_id"]),
            batch_id=str(data["batch_id"]),
            domain=str(data["domain"]),
            created_at=str(data["created_at"]),
            records=records,
            schema_version=str(data.get("schema_version", BRONZE_MANIFEST_SCHEMA_V1)),
            sha256_manifest=str(data["sha256_manifest"])
            if data.get("sha256_manifest")
            else None,
        )
