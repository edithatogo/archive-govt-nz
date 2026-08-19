"""Structured models for New Zealand legislation records (FRBR v1 and v2 models)."""

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
class ManifestationRecord:
    """FRBR Manifestation entity (specific physical/digital encoding)."""

    manifestation_id: str
    expression_id: str
    media_type: str
    cas_hash_sha256: str
    cas_hash_blake3: str
    byte_size: int
    source_uri: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ExpressionRecord:
    """FRBR Expression entity (specific text version over time)."""

    expression_id: str
    work_id: str
    version_status: VersionStatus
    version_date: str | None = None
    assent_date: str | None = None
    commencement_date: str | None = None
    manifestations: list[ManifestationRecord] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class WorkRecord:
    """FRBR Work entity (distinct legislative concept/statute)."""

    work_id: str
    title: str
    legislation_type: LegislationType
    year: int | None = None
    instrument_number: int | None = None
    canonical_uri: str = ""
    expressions: list[ExpressionRecord] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LegislationRecord:
    """Canonical normalised document-level legislation record supporting v1 and v2."""

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
    manifestation_id: str | None = None
    assent_date: str | None = None
    commencement_date: str | None = None
    source_modified_timestamp: str | None = None
    rights_statement: str | None = None
    redistribution_policy: str | None = None
    byte_size: int = 0
    sections: list[SectionRecord] = field(default_factory=list)
    schedules: list[ScheduleRecord] = field(default_factory=list)
    plain_text: str = ""

    def to_dict(self, schema_version: str = "v1") -> dict[str, Any]:
        """Serialize canonical record to schema-conforming dictionary (v1 or v2)."""
        if schema_version in ("v2", "archive-govt-nz.legislation/v2"):
            return self.to_dict_v2()

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

    def to_dict_v2(self) -> dict[str, Any]:
        """Serialize canonical record to v2 schema-conforming dictionary."""
        return {
            "schema_version": "archive-govt-nz.legislation/v2",
            "document_id": self.document_id,
            "work_id": self.work_id,
            "expression_id": self.expression_id,
            "manifestation_id": self.manifestation_id,
            "title": self.title,
            "legislation_type": self.legislation_type.value,
            "status": self.status.value,
            "canonical_uri": self.canonical_uri,
            "raw_cas_hash_sha256": self.raw_cas_hash_sha256,
            "raw_cas_hash_blake3": self.raw_cas_hash_blake3,
            "byte_size": self.byte_size,
            "retrieval_timestamp": self.retrieval_timestamp,
            "source_modified_timestamp": self.source_modified_timestamp,
            "assent_date": self.assent_date,
            "commencement_date": self.commencement_date,
            "sections_count": len(self.sections),
            "schedules_count": len(self.schedules),
            "rights_statement": self.rights_statement,
            "redistribution_policy": self.redistribution_policy,
            "plain_text": self.plain_text,
        }
