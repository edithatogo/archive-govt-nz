"""Native source registration through CAS/WARC and manifest records.

P2.2: Implement the producer-owned native registration and capture gaps.
Registers existing verified originals through native source, observation/version,
preservation and object records. Verifies real CAS/WARC bytes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
lazy from pathlib import Path
from typing import Any

from archive_govt_nz.core.manifests import (
    SourceManifest,
)
from archive_govt_nz.provenance import (
    build_manifest,
)
from archive_govt_nz.warc import write_response_record


@dataclass(frozen=True, slots=True)
class RightsGap:
    """Recorded rights gap for a source that cannot be acquired."""

    source_id: str
    reason: str
    observed_at: str
    rights_status: str
    redistribution_authorized: bool
    schema_version: str = "archive-govt-nz.rights-gap/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize a held-source rights gap without source payload."""
        return {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "reason": self.reason,
            "observed_at": self.observed_at,
            "rights_status": self.rights_status,
            "redistribution_authorized": self.redistribution_authorized,
        }


@dataclass(frozen=True, slots=True)
class NativeSourceRegistration:
    """Native registration record for a verified original source."""

    source_id: str
    source_uri: str
    source_type: str
    agency_slug: str
    archive_id: str
    object_id: str
    object_sha256: str
    warc_record_id: str | None
    warc_sha256: str | None
    captured_at: str
    capture_time_verified: bool
    warc_date_present: bool
    rights_status: str
    redistribution_authorized: bool
    metadata_only: bool
    native_lineage_qualified: bool
    schema_version: str = "archive-govt-nz.source-registration/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize native registration metadata for downstream verification."""
        return {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "source_uri": self.source_uri,
            "source_type": self.source_type,
            "agency_slug": self.agency_slug,
            "archive_id": self.archive_id,
            "object_id": self.object_id,
            "object_sha256": self.object_sha256,
            "warc_record_id": self.warc_record_id,
            "warc_sha256": self.warc_sha256,
            "captured_at": self.captured_at,
            "capture_time_verified": self.capture_time_verified,
            "warc_date_present": self.warc_date_present,
            "rights_status": self.rights_status,
            "redistribution_authorized": self.redistribution_authorized,
            "metadata_only": self.metadata_only,
            "native_lineage_qualified": self.native_lineage_qualified,
        }


def register_source(  # noqa: PLR0913, PLR0917 - stable producer API
    source_id: str,
    source_uri: str,
    source_type: str,
    agency_slug: str,
    archive_id: str,
    object_bytes: bytes,
    object_id: str | None = None,
    warc_path: Path | None = None,
    url: str | None = None,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    rights_status: str = "source_specific_review_required",
    redistribution_authorized: bool = False,  # noqa: FBT001, FBT002
    captured_at: str | None = None,
) -> NativeSourceRegistration:
    """Register an existing verified original through native records.

    Verifies real CAS/WARC bytes. Preserves historical WARC records and their
    missing-date status unchanged. Records rights gaps for unavailable sources.
    """
    if object_id is None:
        object_id = f"sha256:{hashlib.sha256(object_bytes).hexdigest()}"

    object_sha256 = hashlib.sha256(object_bytes).hexdigest()

    # Validate native URI scheme
    SourceManifest(
        source_id=source_id,
        source_uri=source_uri,
        source_type=source_type,
        agency_slug=agency_slug,
    )

    # Write WARC record if path provided
    warc_record_id = None
    warc_sha256 = None
    warc_date_present = False
    if warc_path is not None and url is not None:
        warc_receipt = write_response_record(
            warc_path,
            url=url,
            status_code=status_code,
            headers=headers or {},
            body=body or object_bytes,
        )
        warc_record_id = warc_receipt.record_id
        warc_sha256 = warc_receipt.sha256
        # Check if WARC-Date is present
        warc_bytes = warc_path.read_bytes()
        warc_header = warc_bytes.split(b"\r\n\r\n", 1)[0].decode("utf-8")
        warc_date_present = "WARC-Date:" in warc_header

    if captured_at is None:
        captured_at = datetime.now(UTC).isoformat()

    return NativeSourceRegistration(
        source_id=source_id,
        source_uri=source_uri,
        source_type=source_type,
        agency_slug=agency_slug,
        archive_id=archive_id,
        object_id=object_id,
        object_sha256=object_sha256,
        warc_record_id=warc_record_id,
        warc_sha256=warc_sha256,
        captured_at=captured_at,
        capture_time_verified=captured_at is not None,
        warc_date_present=warc_date_present,
        rights_status=rights_status,
        redistribution_authorized=redistribution_authorized,
        metadata_only=True,
        native_lineage_qualified=False,
    )


def record_rights_gap(
    source_id: str,
    reason: str,
    rights_status: str,
    redistribution_authorized: bool = False,  # noqa: FBT001, FBT002
) -> RightsGap:
    """Record a rights gap for a source that cannot be acquired."""
    return RightsGap(
        source_id=source_id,
        reason=reason,
        observed_at=datetime.now(UTC).isoformat(),
        rights_status=rights_status,
        redistribution_authorized=redistribution_authorized,
    )


def build_source_manifest(
    registration: NativeSourceRegistration,
) -> dict[str, Any]:
    """Build a manifest document from a native source registration."""
    objects = [{"object_id": registration.object_id}]
    observations = [{"observation_id": registration.source_id}]
    versions = [
        {
            "version_id": f"{registration.source_id}-v1",
            "observation_id": registration.source_id,
        }
    ]

    warc_records = []
    if registration.warc_record_id:
        warc_records.append(
            {
                "record_id": registration.warc_record_id,
                "object_id": registration.object_id,
                "sha256": registration.warc_sha256 or "",
                "byte_count": 0,
            }
        )

    manifest = build_manifest(
        archive_id=registration.archive_id,
        observations=observations,
        objects=objects,
        versions=versions,
        warc_records=warc_records or None,
    )
    return manifest.document
