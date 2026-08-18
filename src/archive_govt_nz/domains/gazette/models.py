"""Structured models for New Zealand Gazette notices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GazetteRecord:
    """Canonical normalised Gazette notice."""

    notice_id: str
    issue_number: str
    year: int
    title: str
    publication_date: str
    category: str
    canonical_uri: str
    raw_cas_hash_sha256: str
    retrieval_timestamp: str
    raw_cas_hash_blake3: str | None = None
    department: str | None = None
    byte_size: int = 0
    content_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert GazetteRecord to schema-conforming dictionary."""
        return {
            "schema_version": "archive-govt-nz.gazette/v1",
            "notice_id": self.notice_id,
            "issue_number": self.issue_number,
            "year": self.year,
            "title": self.title,
            "publication_date": self.publication_date,
            "category": self.category,
            "department": self.department,
            "canonical_uri": self.canonical_uri,
            "raw_cas_hash_sha256": self.raw_cas_hash_sha256,
            "raw_cas_hash_blake3": self.raw_cas_hash_blake3,
            "byte_size": self.byte_size,
            "retrieval_timestamp": self.retrieval_timestamp,
            "content_text": self.content_text,
        }
