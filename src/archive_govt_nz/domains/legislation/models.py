"""Structured models for New Zealand legislation records (FRBR v1 and v2 models)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


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


class RelationshipType(StrEnum):
    """Statutory relationship types between legislative works."""

    AMENDS = "amends"
    AMENDED_BY = "amended_by"
    REPEALS = "repeals"
    REPEALED_BY = "repealed_by"
    REPLACES = "replaces"
    REPLACED_BY = "replaced_by"


@dataclass(frozen=True, slots=True)
class RelationshipRecord:
    """Statutory relationship reference."""

    relationship_type: RelationshipType
    target_work_id: str
    effective_date: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize relationship record."""
        return {
            "relationship_type": self.relationship_type.value,
            "target_work_id": self.target_work_id,
            "effective_date": self.effective_date,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class ProvenanceReference:
    """Archival provenance and acquisition citation."""

    source_system: str
    record_id: str
    ingested_at: str
    agent: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize provenance reference."""
        return {
            "source_system": self.source_system,
            "record_id": self.record_id,
            "ingested_at": self.ingested_at,
            "agent": self.agent,
        }


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
    source_modified_timestamp: str | None = None
    status_uncertain: bool = False
    manifestations: list[ManifestationRecord] = field(default_factory=list)
    relationships: list[RelationshipRecord] = field(default_factory=list)
    sections: list[SectionRecord] = field(default_factory=list)
    schedules: list[ScheduleRecord] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class WorkRecord:
    """FRBR Work entity (distinct legislative concept/statute)."""

    work_id: str
    title: str
    legislation_type: LegislationType
    year: int | None = None
    instrument_number: int | None = None
    canonical_uri: str = ""
    relationships: list[RelationshipRecord] = field(default_factory=list)
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
    retrieval_timestamp: str
    expression_id: str | None = None
    manifestation_id: str | None = None
    assent_date: str | None = None
    commencement_date: str | None = None
    source_modified_timestamp: str | None = None
    status_uncertain: bool = False
    relationships: list[RelationshipRecord] = field(default_factory=list)
    provenance: list[ProvenanceReference] = field(default_factory=list)
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
            "status_uncertain": self.status_uncertain,
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
            "relationships": [r.to_dict() for r in self.relationships],
            "provenance": [p.to_dict() for p in self.provenance],
            "rights_statement": self.rights_statement,
            "redistribution_policy": self.redistribution_policy,
            "plain_text": self.plain_text,
        }


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Result of cross-version schema conversion with lossy reporting."""

    record: LegislationRecord
    v1_dict: dict[str, Any]
    lossy: bool
    dropped_fields: list[str]


def convert_v1_to_v2(v1_dict: dict[str, Any]) -> LegislationRecord:
    """Losslessly promote a v1 dictionary into a canonical v2 LegislationRecord."""
    leg_type_raw = v1_dict.get("legislation_type", "other")
    try:
        leg_type = LegislationType(leg_type_raw)
    except ValueError:
        leg_type = LegislationType.OTHER

    status_raw = v1_dict.get("status", "unknown")
    try:
        status = VersionStatus(status_raw)
    except ValueError:
        status = VersionStatus.UNKNOWN

    return LegislationRecord(
        document_id=v1_dict["document_id"],
        work_id=v1_dict["work_id"],
        expression_id=v1_dict.get("expression_id"),
        manifestation_id=None,
        title=v1_dict["title"],
        legislation_type=leg_type,
        status=status,
        status_uncertain=False,
        canonical_uri=v1_dict["canonical_uri"],
        raw_cas_hash_sha256=v1_dict["raw_cas_hash_sha256"],
        raw_cas_hash_blake3=v1_dict["raw_cas_hash_blake3"],
        retrieval_timestamp=v1_dict["retrieval_timestamp"],
        assent_date=v1_dict.get("assent_date"),
        commencement_date=v1_dict.get("commencement_date"),
        source_modified_timestamp=None,
        rights_statement=None,
        redistribution_policy=None,
        byte_size=v1_dict.get("byte_size", 0),
        plain_text=v1_dict.get("plain_text", ""),
    )


def convert_v2_to_v1(
    record_or_dict: LegislationRecord | dict[str, Any],
) -> ConversionResult:
    """Convert a v2 record or dictionary to v1 format with explicit lossy reporting."""
    if isinstance(record_or_dict, LegislationRecord):
        rec = record_or_dict
        v2_dict = rec.to_dict_v2()
    else:
        v2_dict = record_or_dict
        rec = convert_v1_to_v2(v2_dict)

    dropped: list[str] = []
    if v2_dict.get("manifestation_id"):
        dropped.append("manifestation_id")
    if v2_dict.get("source_modified_timestamp"):
        dropped.append("source_modified_timestamp")
    if v2_dict.get("status_uncertain"):
        dropped.append("status_uncertain")
    if v2_dict.get("relationships"):
        dropped.append("relationships")
    if v2_dict.get("provenance"):
        dropped.append("provenance")
    if v2_dict.get("rights_statement"):
        dropped.append("rights_statement")
    if v2_dict.get("redistribution_policy"):
        dropped.append("redistribution_policy")

    v1_dict = rec.to_dict("v1")
    return ConversionResult(
        record=rec,
        v1_dict=v1_dict,
        lossy=len(dropped) > 0,
        dropped_fields=dropped,
    )


def validate_legislation_record(
    data: dict[str, Any], schema_version: str = "v2"
) -> list[str]:
    """Validate serialized dictionary against JSON Schema Draft 2020-12."""
    if schema_version in ("v2", "archive-govt-nz.legislation/v2"):
        schema_subpath = "v2/legislation-record.schema.json"
    elif schema_version in ("v1", "archive-govt-nz.legislation/v1"):
        schema_subpath = "v1/legislation-record.schema.json"
    else:
        return [f"Unsupported or missing schema version: {schema_version}"]

    repo_root = Path(__file__).parents[4]
    schema_file = repo_root / "schemas" / "legislation" / schema_subpath
    if not schema_file.exists():
        return [f"Schema file not found: {schema_file}"]

    with schema_file.open(encoding="utf-8") as f:
        schema_json = json.load(f)

    validator = Draft202012Validator(schema_json)
    return [f"{err.json_path}: {err.message}" for err in validator.iter_errors(data)]
