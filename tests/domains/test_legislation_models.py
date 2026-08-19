"""Unit tests for v2 FRBR legislation models, identity, and crosswalk."""

from __future__ import annotations

from archive_govt_nz.domains.legislation.identity import (
    LegislationExpression,
    LegislationManifestation,
    LegislationWork,
    generate_expression_id,
    generate_manifestation_id,
    generate_work_id,
)
from archive_govt_nz.domains.legislation.models import (
    ExpressionRecord,
    LegislationRecord,
    LegislationType,
    ManifestationRecord,
    ProvenanceReference,
    RelationshipRecord,
    RelationshipType,
    ScheduleRecord,
    SectionRecord,
    VersionStatus,
    WorkRecord,
    convert_v1_to_v2,
    convert_v2_to_v1,
    validate_legislation_record,
)


def test_deterministic_identity_generators() -> None:
    """Test deterministic ID generation without fabrication."""
    # Work ID
    assert generate_work_id(LegislationType.ACT, 1989, 107) == "act-1989-107"
    assert generate_work_id("bill", 2026, 12) == "bill-2026-12"
    assert (
        generate_work_id("regulation", None, None, slug="Heavy-Traffic-Rule")
        == "regulation-heavy-traffic-rule"
    )
    assert generate_work_id("other", None, None) == "other-unknown"

    # Expression ID
    assert (
        generate_expression_id("act-1989-107", version_date="2026-01-01")
        == "exp:act-1989-107:2026-01-01"
    )
    assert (
        generate_expression_id("act-1989-107", version_label="v1.0")
        == "exp:act-1989-107:v1.0"
    )
    dummy_hash = "0" * 64
    assert (
        generate_expression_id("act-1989-107", sha256_digest=dummy_hash)
        == f"exp:act-1989-107:{'0' * 16}"
    )
    assert generate_expression_id("act-1989-107") == "exp:act-1989-107:latest"

    # Manifestation ID
    assert (
        generate_manifestation_id("exp:act-1:latest", "application/xml", dummy_hash)
        == f"man:exp:act-1:latest:xml:{'0' * 12}"
    )
    assert (
        generate_manifestation_id("exp:act-1:latest", "text/html", dummy_hash)
        == f"man:exp:act-1:latest:html:{'0' * 12}"
    )
    assert (
        generate_manifestation_id(
            "exp:act-1:latest", "application/octet-stream", dummy_hash
        )
        == f"man:exp:act-1:latest:bin:{'0' * 12}"
    )


def test_frbr_identity_dataclasses() -> None:
    """Test identity domain model dataclasses."""
    work = LegislationWork(
        work_id="act-1989-107",
        title="Public Finance Act 1989",
        legislation_type=LegislationType.ACT,
        canonical_uri="https://www.legislation.govt.nz/act/public/1989/0107/latest/whole.xml",
        year=1989,
        instrument_number=107,
    )
    assert work.work_id == "act-1989-107"

    expr = LegislationExpression(
        expression_id="exp:act-1989-107:2026-01-01",
        work_id="act-1989-107",
        version_label="2026-01-01",
        status=VersionStatus.IN_FORCE,
        version_date="2026-01-01",
        status_uncertain=False,
    )
    assert expr.expression_id == "exp:act-1989-107:2026-01-01"

    man = LegislationManifestation(
        manifestation_id="man:exp:act-1:latest:xml:1234",
        expression_id="exp:act-1:latest",
        mime_type="application/xml",
        raw_cas_hash_sha256="a" * 64,
        raw_cas_hash_blake3="b" * 64,
        byte_size=1024,
        source_url="https://example.com/act.xml",
    )
    assert man.byte_size == 1024


def test_frbr_runtime_records_and_relationships() -> None:
    """Test WorkRecord, ExpressionRecord, ManifestationRecord, and relationships."""
    rel = RelationshipRecord(
        relationship_type=RelationshipType.AMENDS,
        target_work_id="act-1988-1",
        effective_date="2026-01-01",
        note="Amends section 4",
    )
    assert rel.to_dict()["relationship_type"] == "amends"

    prov = ProvenanceReference(
        source_system="pco-legislation",
        record_id="rec-001",
        ingested_at="2026-08-19T00:00:00Z",
        agent="archive-govt-nz",
    )
    assert prov.to_dict()["source_system"] == "pco-legislation"

    man_rec = ManifestationRecord(
        manifestation_id="man-1",
        expression_id="exp-1",
        media_type="application/xml",
        cas_hash_sha256="a" * 64,
        cas_hash_blake3="b" * 64,
        byte_size=500,
        source_uri="https://example.com/source.xml",
        created_at="2026-08-19T00:00:00Z",
    )

    exp_rec = ExpressionRecord(
        expression_id="exp-1",
        work_id="act-1",
        version_status=VersionStatus.IN_FORCE,
        version_date="2026-01-01",
        manifestations=[man_rec],
        relationships=[rel],
        sections=[
            SectionRecord("s1", "1", "Title", "Content"),
        ],
        schedules=[
            ScheduleRecord("sch1", "1", "Schedule", "Content"),
        ],
    )

    work_rec = WorkRecord(
        work_id="act-1",
        title="Test Act",
        legislation_type=LegislationType.ACT,
        year=2026,
        instrument_number=1,
        canonical_uri="https://example.com/act",
        relationships=[rel],
        expressions=[exp_rec],
    )

    assert len(work_rec.expressions) == 1
    assert len(work_rec.expressions[0].manifestations) == 1


def test_legislation_record_v1_and_v2_serialization() -> None:
    """Test LegislationRecord dual serialization and schema conformance."""
    rec = LegislationRecord(
        document_id="doc-1",
        work_id="act-2026-1",
        title="Test Act 2026",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://www.legislation.govt.nz/act/public/2026/0001/latest/whole.xml",
        raw_cas_hash_sha256="a" * 64,
        raw_cas_hash_blake3="b" * 64,
        retrieval_timestamp="2026-08-19T10:00:00Z",
        expression_id="exp-2026-1-v1",
        manifestation_id="man-2026-1-xml",
        assent_date="2026-02-01",
        commencement_date="2026-03-01",
        source_modified_timestamp="2026-02-15T00:00:00Z",
        status_uncertain=False,
        relationships=[
            RelationshipRecord(
                relationship_type=RelationshipType.AMENDS,
                target_work_id="act-2020-5",
            )
        ],
        provenance=[
            ProvenanceReference(
                source_system="pco",
                record_id="pco-1",
                ingested_at="2026-08-19T10:00:00Z",
                agent="archive-govt-nz",
            )
        ],
        rights_statement="Crown Copyright",
        redistribution_policy="open_access",
        byte_size=1234,
        sections=[SectionRecord("s1", "1", "Short Title", "This Act...")],
        schedules=[ScheduleRecord("sch1", "1", "Enactments Repealed", "None")],
        plain_text="This Act...",
    )

    # v1 serialization
    v1 = rec.to_dict("v1")
    assert v1["schema_version"] == "archive-govt-nz.legislation/v1"
    assert v1["document_id"] == "doc-1"
    assert "manifestation_id" not in v1
    assert "rights_statement" not in v1
    v1_errors = validate_legislation_record(v1, "v1")
    assert v1_errors == []

    # v2 serialization
    v2 = rec.to_dict_v2()
    assert v2["schema_version"] == "archive-govt-nz.legislation/v2"
    assert v2["manifestation_id"] == "man-2026-1-xml"
    assert v2["rights_statement"] == "Crown Copyright"
    assert len(v2["relationships"]) == 1
    assert len(v2["provenance"]) == 1
    v2_errors = validate_legislation_record(v2, "v2")
    assert v2_errors == []


def test_crosswalk_conversions_and_lossy_reporting() -> None:
    """Test convert_v1_to_v2 and convert_v2_to_v1 with lossy reporting."""
    v1_data = {
        "schema_version": "archive-govt-nz.legislation/v1",
        "document_id": "doc-100",
        "work_id": "act-1990-1",
        "expression_id": "exp-1",
        "title": "Act 1990",
        "legislation_type": "act",
        "status": "in_force",
        "canonical_uri": "https://www.legislation.govt.nz/act/1990/1",
        "raw_cas_hash_sha256": "c" * 64,
        "raw_cas_hash_blake3": "d" * 64,
        "byte_size": 2048,
        "retrieval_timestamp": "2026-08-19T00:00:00Z",
        "assent_date": "1990-01-01",
        "commencement_date": "1990-02-01",
        "sections_count": 0,
        "schedules_count": 0,
        "plain_text": "Content",
    }

    # v1 to v2 promotion
    promoted = convert_v1_to_v2(v1_data)
    assert promoted.document_id == "doc-100"
    assert promoted.legislation_type == LegislationType.ACT
    assert promoted.status == VersionStatus.IN_FORCE

    # Lossless conversion back to v1
    lossless_res = convert_v2_to_v1(promoted)
    assert lossless_res.lossy is False
    assert lossless_res.dropped_fields == []
    assert lossless_res.v1_dict["document_id"] == "doc-100"

    # Lossy conversion when rich v2 fields are present
    v2_rich = LegislationRecord(
        document_id="doc-200",
        work_id="act-2026-2",
        title="Rich Act",
        legislation_type=LegislationType.BILL,
        status=VersionStatus.BILL_INTRODUCED,
        canonical_uri="https://example.com/bill",
        raw_cas_hash_sha256="e" * 64,
        raw_cas_hash_blake3="f" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
        manifestation_id="man-1",
        source_modified_timestamp="2026-08-18T00:00:00Z",
        status_uncertain=True,
        rights_statement="NZGOAL",
        redistribution_policy="open",
        relationships=[
            RelationshipRecord(
                relationship_type=RelationshipType.REPEALS,
                target_work_id="act-1900-1",
            )
        ],
    )
    lossy_res = convert_v2_to_v1(v2_rich)
    assert lossy_res.lossy is True
    assert "manifestation_id" in lossy_res.dropped_fields
    assert "source_modified_timestamp" in lossy_res.dropped_fields
    assert "status_uncertain" in lossy_res.dropped_fields
    assert "rights_statement" in lossy_res.dropped_fields
    assert "redistribution_policy" in lossy_res.dropped_fields
    assert "relationships" in lossy_res.dropped_fields

    # Dict input to convert_v2_to_v1
    dict_v2 = v2_rich.to_dict_v2()
    lossy_dict_res = convert_v2_to_v1(dict_v2)
    assert lossy_dict_res.lossy is True

    # Invalid enums fallback in convert_v1_to_v2
    fallback_v1 = {
        "document_id": "doc-fallback",
        "work_id": "work-fallback",
        "title": "Fallback",
        "legislation_type": "invalid_type",
        "status": "invalid_status",
        "canonical_uri": "https://example.com/fb",
        "raw_cas_hash_sha256": "0" * 64,
        "raw_cas_hash_blake3": "1" * 64,
        "retrieval_timestamp": "2026-08-19T00:00:00Z",
    }
    fb_rec = convert_v1_to_v2(fallback_v1)
    assert fb_rec.legislation_type == LegislationType.OTHER
    assert fb_rec.status == VersionStatus.UNKNOWN


def test_schema_validation_failure() -> None:
    """Test validate_legislation_record catches invalid documents."""
    invalid_doc = {
        "schema_version": "archive-govt-nz.legislation/v2",
        "document_id": "doc-invalid",
        # missing mandatory fields
    }
    errors = validate_legislation_record(invalid_doc, "v2")
    assert len(errors) > 0

    # Non-existent schema
    missing_errors = validate_legislation_record({}, "v999")
    assert any("Unsupported or missing schema version" in e for e in missing_errors)
