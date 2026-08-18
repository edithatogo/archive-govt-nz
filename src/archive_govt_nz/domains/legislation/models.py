"""Structured models for New Zealand legislation records."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class LegislationType(StrEnum):
    """Enumeration of recognized statutory instrument types."""

    ACT = "act"
    BILL = "bill"
    REGULATION = "regulation"
    DEEMED_REGULATION = "deemed_regulation"
    ORDER_IN_COUNCIL = "order_in_council"
    OTHER = "other"


class VersionStatus(StrEnum):
    """In-force and enactment state of a legislative expression."""

    IN_FORCE = "in_force"
    AMENDED = "amended"
    REPEALED = "repealed"
    BILL_INTRODUCED = "bill_introduced"
    BILL_PASSED = "bill_passed"
    HISTORICAL = "historical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SectionRecord:
    """Individual statutory section or provision."""

    section_id: str
    number: str
    heading: str
    content: str


@dataclass(frozen=True, slots=True)
class ScheduleRecord:
    """Legislative schedule or appendix."""

    schedule_id: str
    number: str
    heading: str
    content: str


@dataclass(frozen=True, slots=True)
class LegislationRecord:
    """Canonical normalised document-level legislation record."""

    document_id: str
    work_id: str
    title: str
    legislation_type: LegislationType
    status: VersionStatus
    canonical_uri: str
    raw_cas_hash_sha256: str
    raw_cas_hash_blake3: str
    retrieval_timestamp: str = "2026-08-18T11:13:00Z"
    expression_id: str | None = None
    assent_date: str | None = None
    commencement_date: str | None = None
    byte_size: int = 0
    sections: list[SectionRecord] = field(default_factory=list)
    schedules: list[ScheduleRecord] = field(default_factory=list)
    plain_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize canonical record to schema-conforming dictionary."""
        return {
            "schema_version": "archive-govt-nz.legislation/v1",
            "document_id": self.document_id,
            "work_id": self.work_id,
            "expression_id": self.expression_id,
            "title": self.title,
            "legislation_type": self.legislation_type.value,
            "status": self.status.value,
            "canonical_uri": self.canonical_uri,
            "raw_cas_hash_sha256": self.raw_cas_hash_sha256,
            "raw_cas_hash_blake3": self.raw_cas_hash_blake3,
            "byte_size": self.byte_size,
            "retrieval_timestamp": self.retrieval_timestamp,
            "assent_date": self.assent_date,
            "commencement_date": self.commencement_date,
            "sections_count": len(self.sections),
            "schedules_count": len(self.schedules),
            "plain_text": self.plain_text,
        }
