"""Bronze acquisition adapter for NZ Medico-Legal tribunal decisions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from archive_govt_nz.bronze.adapter import (
    BronzeDomainIngestor,
    IngestionResult,
)
from archive_govt_nz.domains.medilegal.parser import (
    parse_medilegal_json,
    parse_medilegal_raw_text,
)

if TYPE_CHECKING:
    from archive_govt_nz.bronze.attestation import Ed25519Signer
    from archive_govt_nz.bronze.models import BronzeRecord
    from archive_govt_nz.object_store import ContentAddressedStore

MEDILEGAL_DOMAIN: Final[str] = "medilegal"


@dataclass(frozen=True, slots=True)
class MedicoLegalIngestOutcome:
    """Outcome of an individual Medico-Legal decision ingestion into Bronze."""

    case_id: str
    tribunal: str
    decision_date: str
    title: str
    record: BronzeRecord


class MedicoLegalBronzeAdapter:
    """Ingests Medico-Legal decision bitstreams into Bronze CAS and tracks fixity."""

    def __init__(
        self,
        store: ContentAddressedStore,
        base_dir: Path | None = None,
    ) -> None:
        """Initialize adapter."""
        self.store = store
        self.base_dir = base_dir or Path(f"data/bronze/{MEDILEGAL_DOMAIN}")
        self.ingestor = BronzeDomainIngestor(
            store=store, domain=MEDILEGAL_DOMAIN, base_dir=self.base_dir
        )

    def ingest_document(  # noqa: PLR0913
        self,
        *,
        payload_bytes: bytes,
        source_url: str,
        case_id: str | None = None,
        tribunal: str | None = None,
        decision_date: str | None = None,
        observed_at: str | None = None,
        custom_metadata: dict[str, Any] | None = None,
    ) -> MedicoLegalIngestOutcome:
        """Parse, sanitize, validate, and store a Medico-Legal case in Bronze."""
        if payload_bytes.strip().startswith(b"{"):
            case = parse_medilegal_json(payload_bytes)
            media_type = "application/json"
        else:
            if not case_id or not tribunal or not decision_date:
                msg = (
                    "case_id, tribunal, and decision_date are required "
                    "for raw text ingest"
                )
                raise ValueError(msg)
            case = parse_medilegal_raw_text(
                payload_bytes.decode("utf-8", errors="replace"),
                case_id=case_id,
                tribunal=tribunal,
                decision_date=decision_date,
            )
            media_type = "text/plain"

        meta = custom_metadata.copy() if custom_metadata else {}
        meta.update(
            {
                "case_id": case.case_id,
                "tribunal": case.tribunal,
                "decision_date": case.decision_date,
                "title": case.title,
                "findings_summary": case.findings_summary,
                "statutory_provisions": list(case.statutory_provisions),
                "is_anonymized": case.is_anonymized,
            }
        )

        record = self.ingestor.ingest_payload(
            record_id=case.case_id,
            payload_bytes=payload_bytes,
            source_url=source_url,
            media_type=media_type,
            observed_at=observed_at,
            custom_metadata=meta,
            validate_signature=True,
        )

        return MedicoLegalIngestOutcome(
            case_id=case.case_id,
            tribunal=case.tribunal,
            decision_date=case.decision_date,
            title=case.title,
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
