"""Unit and contract tests for the legislation domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.domains.legislation.changes import (
    LegislationChangeEvent,
    LegislationChangeReport,
)

if TYPE_CHECKING:
    from pathlib import Path
from archive_govt_nz.domains.legislation.corpus import (
    export_corpus_jsonl,
    export_corpus_parquet,
)
from archive_govt_nz.domains.legislation.coverage import (
    LegislationCoverageReport,
)
from archive_govt_nz.domains.legislation.identity import (
    LegislationExpression,
    LegislationManifestation,
    LegislationWork,
)
from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    SectionRecord,
    VersionStatus,
)
from archive_govt_nz.domains.legislation.normalise import (
    normalise_legislation_payload,
)


def test_legislation_models_and_serialization() -> None:
    """Test creating and serializing a canonical legislation record."""
    sec = SectionRecord(
        section_id="sec-1",
        number="1",
        heading="Title",
        content="This is the Title section.",
    )
    rec = LegislationRecord(
        document_id="leg-act-1989-107",
        work_id="act-1989-107",
        title="Public Finance Act 1989",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://www.legislation.govt.nz/act/public/1989/0107/latest/whole.html",
        raw_cas_hash_sha256="a" * 64,
        raw_cas_hash_blake3="b" * 64,
        retrieval_timestamp="2026-08-18T18:00:00Z",
        sections=[sec],
    )

    data = rec.to_dict()
    assert data["schema_version"] == "archive-govt-nz.legislation/v1"
    assert data["document_id"] == "leg-act-1989-107"
    assert data["sections_count"] == 1


def test_normalise_legislation_payload() -> None:
    """Test deterministic normalisation from raw XML/HTML."""
    raw_xml = (
        b"<act><heading>Test Act 2026</heading>"
        b'<section id="s1"><heading>Section 1</heading>Content of section 1.</section>'
        b"</act>"
    )
    rec = normalise_legislation_payload(
        raw_content=raw_xml,
        work_id="act-2026-1",
        title="Test Act 2026",
        canonical_uri="https://www.legislation.govt.nz/act/public/2026/0001/latest/whole.html",
    )

    assert rec.work_id == "act-2026-1"
    assert len(rec.sections) == 1
    assert len(rec.raw_cas_hash_sha256) == 64
    assert len(rec.raw_cas_hash_blake3) == 64


def test_coverage_and_change_reports() -> None:
    """Test coverage tracking and change report generation."""
    cov = LegislationCoverageReport(
        total_seed_works=100,
        works_attempted=100,
        works_retrieved=98,
        failures_count=2,
        unresolved_gaps=["gap-1", "gap-2"],
    )
    assert cov.coverage_percent == 98.0
    d = cov.to_dict()
    assert d["coverage_percent"] == 98.0
    assert d["unresolved_gaps_count"] == 2

    evt = LegislationChangeEvent(
        work_id="act-1989-107",
        event_type="amendment",
        timestamp="2026-08-18T18:00:00Z",
    )
    rep = LegislationChangeReport(events=[evt])
    assert rep.has_changes is True
    assert rep.to_dict()["total_changes"] == 1


def test_export_corpus_jsonl_and_parquet(tmp_path: Path) -> None:
    """Test exporting legislation records to JSONL and Parquet formats."""
    rec = LegislationRecord(
        document_id="leg-1",
        work_id="work-1",
        title="Test Act",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://example.com/act",
        raw_cas_hash_sha256="0" * 64,
        raw_cas_hash_blake3="1" * 64,
        retrieval_timestamp="2026-08-18T18:00:00Z",
    )

    jsonl_file = tmp_path / "corpus.jsonl"
    parquet_file = tmp_path / "corpus.parquet"

    count1 = export_corpus_jsonl([rec], jsonl_file)
    assert count1 == 1
    assert jsonl_file.is_file()

    count2 = export_corpus_parquet([rec], parquet_file)
    assert count2 == 1
    assert parquet_file.is_file()


def test_identity_classes() -> None:
    """Test Work, Expression, and Manifestation identity models."""
    work = LegislationWork(
        work_id="w-1",
        title="Sample Work",
        legislation_type=LegislationType.ACT,
        canonical_uri="https://example.com/w1",
        year=2026,
    )
    assert work.year == 2026

    expr = LegislationExpression(
        expression_id="e-1",
        work_id="w-1",
        version_label="v1",
        status=VersionStatus.IN_FORCE,
    )
    assert expr.expression_id == "e-1"

    manif = LegislationManifestation(
        manifestation_id="m-1",
        expression_id="e-1",
        mime_type="text/xml",
        raw_cas_hash_sha256="c" * 64,
        raw_cas_hash_blake3="d" * 64,
        byte_size=1024,
        source_url="https://example.com/xml",
    )
    assert manif.byte_size == 1024
