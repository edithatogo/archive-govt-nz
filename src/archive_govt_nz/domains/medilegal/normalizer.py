"""Silver layer normalizer for NZ Medico-Legal decisions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.core.urn import CanonicalURN
from archive_govt_nz.domains.medilegal.parser import (
    parse_medilegal_json,
    parse_medilegal_raw_text,
)
from archive_govt_nz.silver.base import NormalizedSilverRecord, SilverNormalizer

if TYPE_CHECKING:
    from archive_govt_nz.bronze.models import BronzeRecord


class MedicoLegalSilverNormalizer(SilverNormalizer):
    """Normalizes Medico-Legal and health tribunal decisions into Silver Parquet."""

    @property
    def domain(self) -> str:
        """Domain identifier."""
        return "medilegal"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        """Transform Bronze Medico-Legal payload into normalized Silver record."""
        custom = record.custom_metadata or {}
        if payload_bytes.strip().startswith(b"{"):
            case = parse_medilegal_json(payload_bytes)
        else:
            case_id = str(custom.get("case_id", record.record_id))
            tribunal = str(custom.get("tribunal", "Tribunal"))
            decision_date = str(custom.get("decision_date", "2020-01-01"))
            case = parse_medilegal_raw_text(
                payload_bytes.decode("utf-8", errors="replace"),
                case_id=case_id,
                tribunal=tribunal,
                decision_date=decision_date,
            )

        batch_id = custom.get("batch_id", "batch-medilegal-001")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)

        canonical_urn = CanonicalURN.format(self.domain, "decision", case.case_id)
        canonical_uri = f"nzml:decision/{case.case_id}"
        tribunal_slug = case.tribunal.lower()

        meta = {
            "case_id": case.case_id,
            "tribunal": case.tribunal,
            "decision_date": case.decision_date,
            "title": case.title,
            "findings_summary": case.findings_summary,
            "statutory_provisions": list(case.statutory_provisions),
            "is_anonymized": case.is_anonymized,
        }

        silver_record = NormalizedSilverRecord(
            nz_canonical_urn=canonical_urn,
            nz_source_record_id=case.case_id,
            nz_acquisition_id=batch_id,
            nz_content_id=record.fixity.sha256,
            nz_content_cidv1=record.fixity.cidv1 or ("bafybeia" + "a" * 51),
            nz_observed_at=record.source_metadata.observed_at,
            nz_schema_fingerprint=fingerprint,
            domain=self.domain,
            entity_type=f"medico_legal:decision:{tribunal_slug}",
            canonical_uri=canonical_uri,
            title=case.title,
            body_text=case.full_text,
            body_format="text",
            valid_from=case.decision_date,
            valid_to=None,
            source_observed_at=record.source_metadata.observed_at,
            is_current=True,
            source_url=record.source_metadata.source_url,
            cas_path=record.fixity.cas_path,
            sha256_payload=record.fixity.sha256,
            blake3_payload=record.fixity.blake3,
            byte_size=record.fixity.size_bytes,
            metadata_json=json.dumps(meta, sort_keys=True),
        )

        return [silver_record]
