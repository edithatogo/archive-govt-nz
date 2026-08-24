"""Bronze acquisition adapter for NZ Parliamentary Debates (Hansard)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from archive_govt_nz.bronze.adapter import (
    BronzeDomainIngestor,
    IngestionResult,
)
from archive_govt_nz.domains.hansard.parser import parse_hansard_xml

if TYPE_CHECKING:
    from archive_govt_nz.bronze.attestation import Ed25519Signer
    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore

HANSARD_DOMAIN: Final[str] = "hansard"


@dataclass(frozen=True, slots=True)
class HansardIngestOutcome:
    """Outcome of an individual Hansard sitting day XML ingestion."""

    document_id: str
    sitting_date: str
    speech_count: int
    record: BronzeRecord


class HansardBronzeAdapter:
    """Ingests raw Hansard XML documents into Bronze CAS and tracks fixity."""

    def __init__(
        self,
        store: ContentAddressedStore,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize adapter."""
        self.store = store
        self.base_dir = base_dir or Path(f"data/bronze/{HANSARD_DOMAIN}")
        self.ingestor = BronzeDomainIngestor(
            store=store, domain=HANSARD_DOMAIN, base_dir=self.base_dir
        )

    def ingest_document(
        self,
        *,
        xml_bytes: bytes,
        source_url: str,
        observed_at: str | None = None,
        custom_metadata: dict[str, Any] | None = None,
    ) -> HansardIngestOutcome:
        """Parse, validate, and store a Hansard sitting day record in Bronze."""
        debate = parse_hansard_xml(xml_bytes)
        meta = custom_metadata.copy() if custom_metadata else {}
        meta.update(
            {
                "document_id": debate.document_id,
                "sitting_date": debate.sitting_date,
                "parliament_number": debate.parliament_number,
                "session_number": debate.session_number,
                "volume_number": debate.volume_number,
                "title": debate.title,
                "speech_count": len(debate.speeches),
            }
        )

        record = self.ingestor.ingest_payload(
            record_id=debate.document_id,
            payload_bytes=xml_bytes,
            source_url=source_url,
            media_type="application/xml",
            observed_at=observed_at,
            custom_metadata=meta,
            validate_signature=True,
        )

        return HansardIngestOutcome(
            document_id=debate.document_id,
            sitting_date=debate.sitting_date,
            speech_count=len(debate.speeches),
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
