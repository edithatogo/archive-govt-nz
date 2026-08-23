"""Manifest construction and fixity verification for Bronze layer objects."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

try:
    import blake3  # type: ignore[import-untyped,import-not-found]
except (ImportError, ModuleNotFoundError):
    blake3 = None

from archive_govt_nz.bronze.models import (
    BRONZE_MANIFEST_SCHEMA_V1,
    BronzeIngestionManifest,
    BronzePayloadFixity,
    BronzeRecord,
    BronzeSourceMetadata,
)
from archive_govt_nz.bronze.multihash import (
    compute_multihash_triplet,
)


def compute_hashes(data: bytes) -> tuple[str, str]:
    """Compute SHA-256 and BLAKE3 (or SHA-256 fallback if blake3 absent)."""
    triplet = compute_multihash_triplet(data)
    return triplet.sha256, triplet.blake3


def build_bronze_record(  # noqa: PLR0913
    *,
    record_id: str,
    domain: str,
    payload_bytes: bytes,
    source_url: str,
    cas_path: str,
    warc_record_id: str | None = None,
    media_type: str = "application/octet-stream",
    observed_at: str | None = None,
    status_code: int = 200,
    content_type: str | None = None,
    encoding: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
    headers: dict[str, str] | None = None,
    custom_metadata: dict[str, Any] | None = None,
) -> BronzeRecord:
    """Construct a BronzeRecord with cryptographic fixity calculated from bytes."""
    triplet = compute_multihash_triplet(payload_bytes)
    timestamp = observed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    fixity = BronzePayloadFixity(
        sha256=triplet.sha256,
        blake3=triplet.blake3,
        cidv1=triplet.cidv1,
        size_bytes=len(payload_bytes),
        cas_path=cas_path,
        warc_record_id=warc_record_id,
        media_type=media_type,
    )

    source_meta = BronzeSourceMetadata(
        source_url=source_url,
        observed_at=timestamp,
        status_code=status_code,
        content_type=content_type or media_type,
        encoding=encoding,
        etag=etag,
        last_modified=last_modified,
        headers=headers or {},
    )

    return BronzeRecord(
        record_id=record_id,
        domain=domain,
        source_metadata=source_meta,
        fixity=fixity,
        custom_metadata=custom_metadata or {},
    )


def create_bronze_manifest(
    *,
    manifest_id: str,
    batch_id: str,
    domain: str,
    records: list[BronzeRecord],
    created_at: str | None = None,
) -> BronzeIngestionManifest:
    """Create a Bronze ingestion manifest and compute self-verifying SHA-256 digest."""
    timestamp = created_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    records_count = len(records)
    total_bytes = sum(r.fixity.size_bytes for r in records)

    # Construct preliminary manifest to compute stable canonical digest
    manifest = BronzeIngestionManifest(
        manifest_id=manifest_id,
        batch_id=batch_id,
        domain=domain,
        created_at=timestamp,
        records=records,
        records_count=records_count,
        total_bytes=total_bytes,
        schema_version=BRONZE_MANIFEST_SCHEMA_V1,
        sha256_manifest="",
    )

    # Compute digest of record payload representations
    serialized = json.dumps(manifest.to_dict(), sort_keys=True).encode("utf-8")
    sha256_manifest = hashlib.sha256(serialized).hexdigest()

    return BronzeIngestionManifest(
        manifest_id=manifest_id,
        batch_id=batch_id,
        domain=domain,
        created_at=timestamp,
        records=records,
        records_count=records_count,
        total_bytes=total_bytes,
        schema_version=BRONZE_MANIFEST_SCHEMA_V1,
        sha256_manifest=sha256_manifest,
    )


def verify_bronze_manifest_fixity(manifest: BronzeIngestionManifest) -> bool:
    """Verify that a Bronze manifest's sha256_manifest matches its content."""
    if not manifest.sha256_manifest:
        return False

    # Re-derive unsigned dictionary
    unsigned_dict = manifest.to_dict()
    unsigned_dict["sha256_manifest"] = ""
    serialized = json.dumps(unsigned_dict, sort_keys=True).encode("utf-8")
    expected_digest = hashlib.sha256(serialized).hexdigest()

    return manifest.sha256_manifest == expected_digest
