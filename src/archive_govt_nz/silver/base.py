"""Silver Layer: Canonical PyArrow schema specifications and normalizer base.

The Silver layer transforms raw, immutable Bronze bitstreams into standardized,
source-faithful columnar Parquet tables with rigorous bitemporal tracking
(source_observed_at vs. valid_from/valid_to) and cross-domain linking columns.
"""

from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass
from typing import Any

import pyarrow as pa

from archive_govt_nz.bronze.models import (
    BronzeRecord,
)

# Canonical PyArrow Schema for Silver Parquet Records
SILVER_ARROW_SCHEMA = pa.schema(
    [
        # Standard GMA/NZ Linkage Columns
        pa.field("nz_source_record_id", pa.string(), nullable=False),
        pa.field("nz_acquisition_id", pa.string(), nullable=False),
        pa.field("nz_content_id", pa.string(), nullable=False),
        pa.field("nz_observed_at", pa.string(), nullable=False),
        pa.field("nz_schema_fingerprint", pa.string(), nullable=False),
        # Domain & Entity Classifications
        pa.field("domain", pa.string(), nullable=False),
        pa.field("entity_type", pa.string(), nullable=False),
        pa.field("canonical_uri", pa.string(), nullable=False),
        pa.field("title", pa.string(), nullable=False),
        pa.field("body_text", pa.string(), nullable=True),
        pa.field("body_format", pa.string(), nullable=False),
        # Bitemporal Timeline Tracking
        pa.field("valid_from", pa.string(), nullable=True),
        pa.field("valid_to", pa.string(), nullable=True),
        pa.field("source_observed_at", pa.string(), nullable=False),
        pa.field("is_current", pa.bool_(), nullable=False),
        # Lineage & Storage Provenance
        pa.field("source_url", pa.string(), nullable=False),
        pa.field("cas_path", pa.string(), nullable=False),
        pa.field("sha256_payload", pa.string(), nullable=False),
        pa.field("blake3_payload", pa.string(), nullable=False),
        pa.field("byte_size", pa.int64(), nullable=False),
        # Structured Domain Metadata (JSON-encoded string for flexible nested querying)
        pa.field("metadata_json", pa.string(), nullable=False),
    ]
)


@dataclass(frozen=True, slots=True)
class NormalizedSilverRecord:
    """A single normalized record ready for vectorized Parquet insertion."""

    nz_source_record_id: str
    nz_acquisition_id: str
    nz_content_id: str
    nz_observed_at: str
    nz_schema_fingerprint: str
    domain: str
    entity_type: str
    canonical_uri: str
    title: str
    body_text: str | None
    body_format: str
    valid_from: str | None
    valid_to: str | None
    source_observed_at: str
    is_current: bool
    source_url: str
    cas_path: str
    sha256_payload: str
    blake3_payload: str
    byte_size: int
    metadata_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        """Convert normalized record to dictionary matching SILVER_ARROW_SCHEMA."""
        return {
            "nz_source_record_id": self.nz_source_record_id,
            "nz_acquisition_id": self.nz_acquisition_id,
            "nz_content_id": self.nz_content_id,
            "nz_observed_at": self.nz_observed_at,
            "nz_schema_fingerprint": self.nz_schema_fingerprint,
            "domain": self.domain,
            "entity_type": self.entity_type,
            "canonical_uri": self.canonical_uri,
            "title": self.title,
            "body_text": self.body_text,
            "body_format": self.body_format,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "source_observed_at": self.source_observed_at,
            "is_current": self.is_current,
            "source_url": self.source_url,
            "cas_path": self.cas_path,
            "sha256_payload": self.sha256_payload,
            "blake3_payload": self.blake3_payload,
            "byte_size": self.byte_size,
            "metadata_json": self.metadata_json,
        }


class SilverNormalizer(abc.ABC):
    """Abstract base class for domain-specific Bronze-to-Silver normalizers."""

    @property
    @abc.abstractmethod
    def domain(self) -> str:
        """The source domain handled by this normalizer."""

    @abc.abstractmethod
    def normalize_record(
        self,
        record: BronzeRecord,
        payload_bytes: bytes,
    ) -> list[NormalizedSilverRecord]:
        """Normalize a Bronze record and raw bitstream into Silver records."""

    def compute_schema_fingerprint(self, content: bytes) -> str:
        """Compute structural schema fingerprint for record change detection."""
        return hashlib.sha256(content[:1024]).hexdigest()
