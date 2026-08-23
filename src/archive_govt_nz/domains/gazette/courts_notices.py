"""Bronze ingestion adapter for Courts of New Zealand public notices archive."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor, IngestionResult

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore


class CourtsPublicNoticesIngestor:
    """Ingest judicial notices, liquidation, insolvency, and probate releases into Bronze."""

    def __init__(
        self,
        store: ContentAddressedStore,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize courts notice ingestor."""
        self.ingestor = BronzeDomainIngestor(
            store=store,
            domain="courts_notices",
            base_dir=base_dir,
        )

    def ingest_notice(
        self,
        *,
        notice_id: str,
        notice_type: str,
        court_name: str,
        title: str,
        payload_bytes: bytes,
        source_url: str,
        published_at: str,
        media_type: str = "application/json",
        extra_metadata: dict[str, Any] | None = None,
    ) -> BronzeRecord:
        """Ingest a single Courts NZ notice bitstream into Bronze CAS."""
        custom_metadata = {
            "notice_type": notice_type,
            "court_name": court_name,
            "title": title,
            "published_at": published_at,
            **(extra_metadata or {}),
        }
        return self.ingestor.ingest_payload(
            record_id=f"rec-court-{notice_id}",
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
        """Finalize Courts NZ notice ingestion batch and write manifest."""
        return self.ingestor.finalize_batch(
            batch_id=batch_id,
            manifest_id=f"courts-{batch_id}",
            records=records,
        )
