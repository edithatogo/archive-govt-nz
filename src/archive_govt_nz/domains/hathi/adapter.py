"""Bronze acquisition adapter for historical NZ HathiTrust volumes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from archive_govt_nz.bronze.adapter import (
    BronzeDomainIngestor,
    IngestionResult,
)
from archive_govt_nz.domains.hathi.parser import parse_hathi_json, parse_hathi_mets_xml

if TYPE_CHECKING:
    from archive_govt_nz.bronze.attestation import Ed25519Signer
    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore

HATHI_DOMAIN: Final[str] = "hathi"


@dataclass(frozen=True, slots=True)
class HathiIngestOutcome:
    """Outcome of an individual HathiTrust volume ingestion into Bronze."""

    volume_id: str
    title: str
    page_count: int
    record: BronzeRecord


class HathiBronzeAdapter:
    """Ingests raw HathiTrust volume payloads into Bronze CAS and tracks fixity."""

    def __init__(
        self,
        store: ContentAddressedStore,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize adapter."""
        self.store = store
        self.base_dir = base_dir or Path(f"data/bronze/{HATHI_DOMAIN}")
        self.ingestor = BronzeDomainIngestor(
            store=store, domain=HATHI_DOMAIN, base_dir=self.base_dir
        )

    def ingest_document(
        self,
        *,
        payload_bytes: bytes,
        source_url: str,
        volume_id: str | None = None,
        observed_at: str | None = None,
        custom_metadata: dict[str, Any] | None = None,
    ) -> HathiIngestOutcome:
        """Parse, validate, and store a Hathi volume in Bronze."""
        if payload_bytes.strip().startswith(b"<"):
            if not volume_id:
                msg = "volume_id is required when ingesting raw METS XML"
                raise ValueError(msg)
            volume = parse_hathi_mets_xml(payload_bytes, volume_id=volume_id)
            media_type = "application/xml"
        else:
            volume = parse_hathi_json(payload_bytes)
            media_type = "application/json"

        meta = custom_metadata.copy() if custom_metadata else {}
        meta.update(
            {
                "volume_id": volume.volume_id,
                "title": volume.title,
                "author": volume.author,
                "publication_year": volume.publication_year,
                "rights_attributes": volume.rights_attributes,
                "page_count": volume.page_count,
            }
        )

        record = self.ingestor.ingest_payload(
            record_id=volume.volume_id,
            payload_bytes=payload_bytes,
            source_url=source_url,
            media_type=media_type,
            observed_at=observed_at,
            custom_metadata=meta,
            validate_signature=True,
        )

        return HathiIngestOutcome(
            volume_id=volume.volume_id,
            title=volume.title,
            page_count=volume.page_count,
            record=record,
        )

    def finalize_batch(
        self,
        batch_id: str,
        records: list[BronzeRecord],
        *,
        manifest_id: str = "latest",
        signer: Ed25519Signer | None = None,
    ) -> IngestionResult:
        """Commit batch manifest and optional cryptographic signature."""
        return self.ingestor.finalize_batch(
            batch_id=batch_id,
            records=records,
            manifest_id=manifest_id,
            signer=signer,
        )
