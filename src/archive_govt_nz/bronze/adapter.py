"""Standardized Bronze ingestion service for raw bitstreams and CAS indexing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from archive_govt_nz.bronze.manifest import (
    build_bronze_record,
    create_bronze_manifest,
    verify_bronze_manifest_fixity,
)

if TYPE_CHECKING:
    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore


from archive_govt_nz.bronze.sniffer import (
    InvalidPayloadSignatureError,
    validate_payload_signature,
)


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Telemetry and outcome of a domain Bronze ingestion batch."""

    status: str
    domain: str
    batch_id: str
    records_synced: int
    bytes_synced: int
    manifest_path: str | None = None
    manifest_sha256: str | None = None
    errors: list[str] | None = None


class BronzeDomainIngestor:
    """Standard service to ingest raw domain streams into Bronze CAS and write manifests."""

    def __init__(
        self,
        store: ContentAddressedStore,
        domain: str,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize ingestor for a specific archive domain."""
        self.store = store
        self.domain = domain
        self.base_dir = base_dir or Path(f"data/bronze/{domain}")

    def ingest_payload(
        self,
        *,
        record_id: str,
        payload_bytes: bytes,
        source_url: str,
        media_type: str = "application/octet-stream",
        observed_at: str | None = None,
        status_code: int = 200,
        content_type: str | None = None,
        encoding: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        headers: dict[str, str] | None = None,
        custom_metadata: dict[str, Any] | None = None,
        validate_signature: bool = True,
    ) -> BronzeRecord:
        """Store payload in CAS and return a typed BronzeRecord with fixity.

        Validates magic byte signatures before writing to CAS disk storage.
        """
        if validate_signature:
            sniff_res = validate_payload_signature(
                payload_bytes,
                expected_mime=media_type
                if media_type != "application/octet-stream"
                else content_type,
            )
            if not sniff_res.is_valid:
                err_msg = f"Bronze ingest rejected for record '{record_id}': {sniff_res.error}"
                raise InvalidPayloadSignatureError(
                    err_msg,
                    detected_mime=sniff_res.detected_mime,
                    expected_mime=sniff_res.expected_mime,
                )

        cas_receipt = self.store.put_bytes(payload_bytes)
        return build_bronze_record(
            record_id=record_id,
            domain=self.domain,
            payload_bytes=payload_bytes,
            source_url=source_url,
            cas_path=str(cas_receipt.path),
            warc_record_id=None,
            media_type=media_type,
            observed_at=observed_at,
            status_code=status_code,
            content_type=content_type or media_type,
            encoding=encoding,
            etag=etag,
            last_modified=last_modified,
            headers=headers,
            custom_metadata=custom_metadata,
        )

    def finalize_batch(
        self,
        *,
        batch_id: str,
        manifest_id: str,
        records: list[BronzeRecord],
        output_dir: Path | None = None,
    ) -> IngestionResult:
        """Create, verify, and persist a self-authenticating Bronze manifest."""
        target_dir = output_dir or self.base_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        manifest = create_bronze_manifest(
            manifest_id=manifest_id,
            batch_id=batch_id,
            domain=self.domain,
            records=records,
        )

        if not verify_bronze_manifest_fixity(manifest):
            err_msg = "Bronze manifest fixity validation failed during finalization"
            raise ValueError(err_msg)

        manifest_file = target_dir / f"manifest-{manifest_id}.json"
        manifest_dict = manifest.to_dict()
        manifest_file.write_text(
            json.dumps(manifest_dict, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        checkpoint_file = target_dir / "checkpoint.json"
        checkpoint_data = {
            "schema_version": "archive-govt-nz.bronze-checkpoint/v1",
            "domain": self.domain,
            "latest_batch_id": batch_id,
            "latest_manifest_id": manifest_id,
            "latest_manifest_sha256": manifest.sha256_manifest,
            "total_records": len(records),
            "total_bytes": manifest.total_bytes,
            "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        checkpoint_file.write_text(
            json.dumps(checkpoint_data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return IngestionResult(
            status="success",
            domain=self.domain,
            batch_id=batch_id,
            records_synced=len(records),
            bytes_synced=manifest.total_bytes,
            manifest_path=str(manifest_file),
            manifest_sha256=manifest.sha256_manifest,
            errors=[],
        )
