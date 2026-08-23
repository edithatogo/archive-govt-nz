"""Bronze ingestion adapter for Pae Ora (Healthy Futures) reform records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor, IngestionResult

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore


class PaeOraReformIngestor:
    """Ingest Pae Ora health system reform policy publications & transition records."""

    def __init__(
        self,
        store: ContentAddressedStore,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize Pae Ora reform ingestor."""
        self.ingestor = BronzeDomainIngestor(
            store=store,
            domain="health_pae_ora",
            base_dir=base_dir,
        )

    def ingest_publication(
        self,
        *,
        document_id: str,
        title: str,
        entity: str,
        published_at: str,
        payload_bytes: bytes,
        source_url: str,
        media_type: str = "application/pdf",
        extra_metadata: dict[str, Any] | None = None,
    ) -> BronzeRecord:
        """Ingest one Pae Ora reform publication bitstream into Bronze CAS."""
        custom_metadata = {
            "document_id": document_id,
            "title": title,
            "entity": entity,
            "published_at": published_at,
            "statutory_context": "Pae Ora (Healthy Futures) Act 2022",
            **(extra_metadata or {}),
        }
        return self.ingestor.ingest_payload(
            record_id=f"rec-pae-ora-{document_id}",
            payload_bytes=payload_bytes,
            source_url=source_url,
            media_type=media_type,
            observed_at=published_at,
            custom_metadata=custom_metadata,
        )

    def finalize(
        self,
        *,
        batch_id: str,
        records: list[BronzeRecord],
    ) -> IngestionResult:
        """Finalize Pae Ora reform ingestion batch and write manifest."""
        return self.ingestor.finalize_batch(
            batch_id=batch_id,
            manifest_id=f"pae-ora-{batch_id}",
            records=records,
        )
