"""Silver layer normalizer for NZ Parliamentary Debates (Hansard).

Transforms raw Hansard Bronze XML bitstreams into bitemporal Silver Parquet
records, reconciles MP speaker entities, and links statutory citations.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.core.urn import CanonicalURN
from archive_govt_nz.domains.hansard.parser import parse_hansard_xml
from archive_govt_nz.silver.base import NormalizedSilverRecord, SilverNormalizer

if TYPE_CHECKING:
    from archive_govt_nz.bronze.models import BronzeRecord


class HansardSilverNormalizer(SilverNormalizer):
    """Normalizes Hansard sitting day debates into discrete Silver speech records."""

    @property
    def domain(self) -> str:
        """Domain identifier."""
        return "hansard"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        """Transform Bronze Hansard sitting XML into normalized speech records."""
        debate = parse_hansard_xml(payload_bytes)
        custom = record.custom_metadata or {}
        batch_id = custom.get("batch_id", "batch-hansard-001")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)

        silver_records: list[NormalizedSilverRecord] = []

        for speech in debate.speeches:
            work_id = f"{debate.document_id}_{speech.speech_id}"
            canonical_urn = CanonicalURN.format(self.domain, "speech", work_id)
            canonical_uri = f"nzhansard:speech/{work_id}"
            title = f"Hansard: {speech.speaker_name} on {debate.title}"

            speech_meta = {
                "document_id": debate.document_id,
                "sitting_date": debate.sitting_date,
                "parliament_number": debate.parliament_number,
                "session_number": debate.session_number,
                "volume_number": debate.volume_number,
                "debate_title": debate.title,
                "speech_id": speech.speech_id,
                "speaker_name": speech.speaker_name,
                "speaker_role": speech.speaker_role,
                "speech_type": speech.speech_type,
                "bill_references": list(speech.bill_references),
                "act_references": list(speech.act_references),
                "time_utc": speech.time_utc,
            }

            text_bytes = speech.speech_text.encode("utf-8")

            silver_records.append(
                NormalizedSilverRecord(
                    nz_canonical_urn=canonical_urn,
                    nz_source_record_id=work_id,
                    nz_acquisition_id=batch_id,
                    nz_content_id=record.fixity.sha256,
                    nz_content_cidv1=record.fixity.cidv1,
                    nz_observed_at=record.source_metadata.observed_at,
                    nz_schema_fingerprint=fingerprint,
                    domain=self.domain,
                    entity_type=f"parliamentary_speech:{speech.speech_type}",
                    canonical_uri=canonical_uri,
                    title=title,
                    body_text=speech.speech_text,
                    body_format="text",
                    valid_from=debate.sitting_date,
                    valid_to=None,
                    source_observed_at=record.source_metadata.observed_at,
                    is_current=True,
                    source_url=record.source_metadata.source_url,
                    cas_path=record.fixity.cas_path,
                    sha256_payload=record.fixity.sha256,
                    blake3_payload=record.fixity.blake3,
                    byte_size=len(text_bytes),
                    metadata_json=json.dumps(speech_meta, sort_keys=True),
                )
            )

        return silver_records
