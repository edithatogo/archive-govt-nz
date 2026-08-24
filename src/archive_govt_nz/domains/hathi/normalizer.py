"""Silver layer normalizer for HathiTrust historical NZ volumes.

Transforms Bronze METS/OCR volume bitstreams into bitemporal Silver Parquet
records, enforces deterministic rights classification, and indexes historical citations.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from archive_govt_nz.core.urn import CanonicalURN
from archive_govt_nz.domains.hathi.parser import parse_hathi_json, parse_hathi_mets_xml
from archive_govt_nz.silver.base import NormalizedSilverRecord, SilverNormalizer

if TYPE_CHECKING:
    from archive_govt_nz.bronze.models import BronzeRecord

_PD_CUTOFF_YEAR: Final[int] = 1928
_CROWN_COPYRIGHT_CUTOFF_YEAR: Final[int] = 1975


def classify_historical_rights(pub_year: int | None, rights_attr: str) -> str:
    """Classify copyright status under NZ Copyright Act historical terms."""
    if rights_attr in ("pd", "crown_copyright_expired"):
        return "public_domain"
    if pub_year is not None:
        if pub_year < _PD_CUTOFF_YEAR:
            return "public_domain"
        if pub_year <= _CROWN_COPYRIGHT_CUTOFF_YEAR:
            return "crown_copyright_expired"
    return "open_access"


class HathiSilverNormalizer(SilverNormalizer):
    """Normalizes HathiTrust volume records into discrete Silver page records."""

    @property
    def domain(self) -> str:
        """Domain identifier."""
        return "hathi"

    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        """Transform Bronze Hathi payload into normalized Silver records."""
        if payload_bytes.strip().startswith(b"<"):
            volume = parse_hathi_mets_xml(payload_bytes, volume_id=record.record_id)
        else:
            volume = parse_hathi_json(payload_bytes)

        custom = record.custom_metadata or {}
        batch_id = custom.get("batch_id", "batch-hathi-001")
        fingerprint = self.compute_schema_fingerprint(payload_bytes)
        rights_status = classify_historical_rights(
            volume.publication_year, volume.rights_attributes
        )

        silver_records: list[NormalizedSilverRecord] = []
        pub_year_str = f"{volume.publication_year or 1900:04d}-01-01"

        if not volume.pages:
            work_id = volume.volume_id
            canonical_urn = CanonicalURN.format(self.domain, "volume", work_id)
            canonical_uri = f"nzhathi:volume/{work_id}"
            title = f"HathiTrust NZ: {volume.title}"

            meta = {
                "volume_id": volume.volume_id,
                "author": volume.author,
                "publication_year": volume.publication_year,
                "rights_status": rights_status,
                "source_institution": volume.source_institution,
                "page_count": volume.page_count,
            }

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
                    entity_type="historical_publication:volume",
                    canonical_uri=canonical_uri,
                    title=title,
                    body_text="",
                    body_format="text",
                    valid_from=pub_year_str,
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
            )
            return silver_records

        for page in volume.pages:
            work_id = f"{volume.volume_id}_p{page.page_seq:04d}"
            canonical_urn = CanonicalURN.format(self.domain, "page", work_id)
            canonical_uri = f"nzhathi:volume/{volume.volume_id}#p={page.page_seq}"
            title = f"HathiTrust NZ: {volume.title} (Page {page.page_seq})"

            page_meta = {
                "volume_id": volume.volume_id,
                "author": volume.author,
                "publication_year": volume.publication_year,
                "rights_status": rights_status,
                "source_institution": volume.source_institution,
                "page_seq": page.page_seq,
                "page_number": page.page_number,
                "act_references": list(page.act_references),
            }

            text_bytes = page.page_text.encode("utf-8")

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
                    entity_type="historical_publication:page",
                    canonical_uri=canonical_uri,
                    title=title,
                    body_text=page.page_text,
                    body_format="text",
                    valid_from=pub_year_str,
                    valid_to=None,
                    source_observed_at=record.source_metadata.observed_at,
                    is_current=True,
                    source_url=record.source_metadata.source_url,
                    cas_path=record.fixity.cas_path,
                    sha256_payload=record.fixity.sha256,
                    blake3_payload=record.fixity.blake3,
                    byte_size=len(text_bytes),
                    metadata_json=json.dumps(page_meta, sort_keys=True),
                )
            )

        return silver_records


__all__ = [
    "HathiSilverNormalizer",
    "classify_historical_rights",
]
