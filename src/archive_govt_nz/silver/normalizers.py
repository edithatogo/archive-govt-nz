"""Domain-specific Silver normalizers transforming Bronze records into clean Parquet."""

from __future__ import annotations

import json

from archive_govt_nz.bronze.models import BronzeRecord
from archive_govt_nz.core.urn import CanonicalURN
from archive_govt_nz.domains.hansard.parser import parse_hansard_xml
from archive_govt_nz.silver.base import NormalizedSilverRecord, SilverNormalizer


class LegislationSilverNormalizer(SilverNormalizer):
    """Normalizes statutory instruments, Acts, and Regulations."""

    @property
    def domain(self) -> str:
        return "legislation"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        custom = record.custom_metadata or {}
        text_content = payload_bytes.decode("utf-8", errors="replace")

        fingerprint = self.compute_schema_fingerprint(payload_bytes)
        work_id = custom.get("work_id", record.record_id)
        title = custom.get("title", f"Legislation {work_id}")
        doc_type = custom.get("instrument_type", "act")
        valid_from = custom.get("as_at") or custom.get("date_in_force")
        is_current = bool(custom.get("is_in_force", True))

        return [
            NormalizedSilverRecord(
                nz_canonical_urn=CanonicalURN.format(self.domain, doc_type, work_id),
                nz_source_record_id=record.record_id,
                nz_acquisition_id=custom.get("batch_id", "batch-legislation-001"),
                nz_content_id=record.fixity.sha256,
                nz_content_cidv1=record.fixity.cidv1,
                nz_observed_at=record.source_metadata.observed_at,
                nz_schema_fingerprint=fingerprint,
                domain=self.domain,
                entity_type=doc_type,
                canonical_uri=f"nzlc:{doc_type}/{work_id}",
                title=title,
                body_text=text_content[:50000],  # Bounded tabular sample
                body_format="xml" if "<" in text_content[:100] else "text",
                valid_from=valid_from,
                valid_to=None,
                source_observed_at=record.source_metadata.observed_at,
                is_current=is_current,
                source_url=record.source_metadata.source_url,
                cas_path=record.fixity.cas_path,
                sha256_payload=record.fixity.sha256,
                blake3_payload=record.fixity.blake3,
                byte_size=record.fixity.size_bytes,
                metadata_json=json.dumps(custom, sort_keys=True),
            )
        ]


class GazetteSilverNormalizer(SilverNormalizer):
    """Normalizes official New Zealand Gazette notices."""

    @property
    def domain(self) -> str:
        return "gazette"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        custom = record.custom_metadata or {}
        text_content = payload_bytes.decode("utf-8", errors="replace")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)

        notice_id = custom.get("notice_id", record.record_id)
        title = custom.get("title", f"Gazette Notice {notice_id}")
        notice_type = custom.get("notice_type", "general")
        published_date = (
            custom.get("published_date") or record.source_metadata.observed_at[:10]
        )

        return [
            NormalizedSilverRecord(
                nz_canonical_urn=CanonicalURN.format(
                    self.domain, f"notice_{notice_type}", notice_id
                ),
                nz_source_record_id=record.record_id,
                nz_acquisition_id=custom.get("batch_id", "batch-gazette-001"),
                nz_content_id=record.fixity.sha256,
                nz_content_cidv1=record.fixity.cidv1,
                nz_observed_at=record.source_metadata.observed_at,
                nz_schema_fingerprint=fingerprint,
                domain=self.domain,
                entity_type=f"gazette_notice:{notice_type}",
                canonical_uri=f"nzgazette:notice/{notice_id}",
                title=title,
                body_text=text_content[:50000],
                body_format="html" if "<html" in text_content[:200].lower() else "text",
                valid_from=published_date,
                valid_to=None,
                source_observed_at=record.source_metadata.observed_at,
                is_current=True,
                source_url=record.source_metadata.source_url,
                cas_path=record.fixity.cas_path,
                sha256_payload=record.fixity.sha256,
                blake3_payload=record.fixity.blake3,
                byte_size=record.fixity.size_bytes,
                metadata_json=json.dumps(custom, sort_keys=True),
            )
        ]


class CourtsNoticesSilverNormalizer(SilverNormalizer):
    """Normalizes Courts NZ public and legal notices."""

    @property
    def domain(self) -> str:
        return "courts"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        custom = record.custom_metadata or {}
        text_content = payload_bytes.decode("utf-8", errors="replace")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)

        notice_id = custom.get("notice_id", record.record_id)
        court_name = custom.get("court_name", "District Court")
        title = custom.get("title", f"{court_name} Notice {notice_id}")

        return [
            NormalizedSilverRecord(
                nz_canonical_urn=CanonicalURN.format(self.domain, "notice", notice_id),
                nz_source_record_id=record.record_id,
                nz_acquisition_id=custom.get("batch_id", "batch-courts-001"),
                nz_content_id=record.fixity.sha256,
                nz_content_cidv1=record.fixity.cidv1,
                nz_observed_at=record.source_metadata.observed_at,
                nz_schema_fingerprint=fingerprint,
                domain=self.domain,
                entity_type="court_notice",
                canonical_uri=f"nzcourt:notice/{notice_id}",
                title=title,
                body_text=text_content[:50000],
                body_format="text",
                valid_from=custom.get("hearing_date")
                or record.source_metadata.observed_at[:10],
                valid_to=None,
                source_observed_at=record.source_metadata.observed_at,
                is_current=True,
                source_url=record.source_metadata.source_url,
                cas_path=record.fixity.cas_path,
                sha256_payload=record.fixity.sha256,
                blake3_payload=record.fixity.blake3,
                byte_size=record.fixity.size_bytes,
                metadata_json=json.dumps(custom, sort_keys=True),
            )
        ]


class HealthSilverNormalizer(SilverNormalizer):
    """Normalizes Ministry of Health, COVID-19 dataset snapshots, and Pae Ora releases."""

    @property
    def domain(self) -> str:
        return "health"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        custom = record.custom_metadata or {}
        text_content = payload_bytes.decode("utf-8", errors="replace")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)

        feed_type = custom.get("feed_type", "moh_publication")
        title = custom.get("title", f"Health Data {record.record_id}")

        return [
            NormalizedSilverRecord(
                nz_canonical_urn=CanonicalURN.format(
                    self.domain, feed_type, record.record_id
                ),
                nz_source_record_id=record.record_id,
                nz_acquisition_id=custom.get("batch_id", "batch-health-001"),
                nz_content_id=record.fixity.sha256,
                nz_content_cidv1=record.fixity.cidv1,
                nz_observed_at=record.source_metadata.observed_at,
                nz_schema_fingerprint=fingerprint,
                domain=self.domain,
                entity_type=feed_type,
                canonical_uri=f"nzhealth:{feed_type}/{record.record_id}",
                title=title,
                body_text=text_content[:50000],
                body_format="json" if text_content.startswith("{") else "csv",
                valid_from=custom.get("as_of_date")
                or record.source_metadata.observed_at[:10],
                valid_to=None,
                source_observed_at=record.source_metadata.observed_at,
                is_current=True,
                source_url=record.source_metadata.source_url,
                cas_path=record.fixity.cas_path,
                sha256_payload=record.fixity.sha256,
                blake3_payload=record.fixity.blake3,
                byte_size=record.fixity.size_bytes,
                metadata_json=json.dumps(custom, sort_keys=True),
            )
        ]


class TreasurySilverNormalizer(SilverNormalizer):
    """Normalizes NZ Treasury publications, budget releases, and economic statements."""

    @property
    def domain(self) -> str:
        return "treasury"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        custom = record.custom_metadata or {}
        text_content = payload_bytes.decode("utf-8", errors="replace")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)

        doc_id = custom.get("document_id", record.record_id)
        title = custom.get("title", f"Treasury Document {doc_id}")

        return [
            NormalizedSilverRecord(
                nz_canonical_urn=CanonicalURN.format(self.domain, "release", doc_id),
                nz_source_record_id=record.record_id,
                nz_acquisition_id=custom.get("batch_id", "batch-treasury-001"),
                nz_content_id=record.fixity.sha256,
                nz_content_cidv1=record.fixity.cidv1,
                nz_observed_at=record.source_metadata.observed_at,
                nz_schema_fingerprint=fingerprint,
                domain=self.domain,
                entity_type="treasury_release",
                canonical_uri=f"nztreasury:release/{doc_id}",
                title=title,
                body_text=text_content[:50000],
                body_format="html" if "<html" in text_content[:200].lower() else "text",
                valid_from=custom.get("release_date")
                or record.source_metadata.observed_at[:10],
                valid_to=None,
                source_observed_at=record.source_metadata.observed_at,
                is_current=True,
                source_url=record.source_metadata.source_url,
                cas_path=record.fixity.cas_path,
                sha256_payload=record.fixity.sha256,
                blake3_payload=record.fixity.blake3,
                byte_size=record.fixity.size_bytes,
                metadata_json=json.dumps(custom, sort_keys=True),
            )
        ]


class HansardSilverNormalizer(SilverNormalizer):
    """Normalizes Hansard sitting day debates into discrete Silver speech records."""

    @property
    def domain(self) -> str:
        return "hansard"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
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


__all__ = [
    "CourtsNoticesSilverNormalizer",
    "GazetteSilverNormalizer",
    "HansardSilverNormalizer",
    "HealthSilverNormalizer",
    "LegislationSilverNormalizer",
    "TreasurySilverNormalizer",
]
