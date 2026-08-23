"""Bronze ingestion adapter for historical NZ COVID-19 pandemic official releases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor, IngestionResult

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore


class CovidDataIngestor:
    """Ingest Ministry of Health / Te Whatu Ora pandemic historical tables into Bronze CAS."""

    def __init__(
        self,
        store: ContentAddressedStore,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize COVID-19 data ingestor."""
        self.ingestor = BronzeDomainIngestor(
            store=store,
            domain="health_covid",
            base_dir=base_dir,
        )

    def ingest_dataset_release(
        self,
        *,
        dataset_id: str,
        title: str,
        release_date: str,
        payload_bytes: bytes,
        source_url: str,
        media_type: str = "text/csv",
        extra_metadata: dict[str, Any] | None = None,
    ) -> BronzeRecord:
        """Ingest one pandemic table release into CAS."""
        custom_metadata = {
            "dataset_id": dataset_id,
            "title": title,
            "release_date": release_date,
            "publisher": "Ministry of Health / Te Whatu Ora",
            **(extra_metadata or {}),
        }
        return self.ingestor.ingest_payload(
            record_id=f"rec-covid-{dataset_id}",
            payload_bytes=payload_bytes,
            source_url=source_url,
            media_type=media_type,
            observed_at=release_date,
            custom_metadata=custom_metadata,
        )

    def finalize(
        self,
        *,
        batch_id: str,
        records: list[BronzeRecord],
    ) -> IngestionResult:
        """Finalize COVID-19 ingestion batch and write manifest."""
        return self.ingestor.finalize_batch(
            batch_id=batch_id,
            manifest_id=f"covid-{batch_id}",
            records=records,
        )
