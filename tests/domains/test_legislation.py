"""Unit and contract tests for the legislation domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.bootstrap import (
    load_work_ids_from_batch_file,
    reconcile_historical_batches,
)
from archive_govt_nz.domains.legislation.changes import (
    LegislationChangeEvent,
    LegislationChangeReport,
)
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.corpus import (
    export_corpus_jsonl,
    export_corpus_parquet,
)
from archive_govt_nz.domains.legislation.coverage import (
    LegislationCoverageReport,
)
from archive_govt_nz.domains.legislation.discovery import build_work_inventory
from archive_govt_nz.domains.legislation.identity import (
    LegislationExpression,
    LegislationManifestation,
    LegislationWork,
)
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
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
from archive_govt_nz.domains.legislation.publication import (
    prepare_legislation_publication_package,
)
from archive_govt_nz.domains.legislation.validate import (
    validate_legislation_record,
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
        retrieval_timestamp="2026-08-18T11:13:00Z",
        sections=[sec],
    )

    data = rec.to_dict()
    assert data["schema_version"] == "archive-govt-nz.legislation/v1"
    assert data["document_id"] == "leg-act-1989-107"
    assert data["sections_count"] == 1


def test_coverage_has_no_historical_fallback_denominator() -> None:
    """An empty bounded inventory must not imply a historical corpus total."""
    report = LegislationCoverageReport()
    assert report.total_seed_works == 0
    assert report.coverage_percent == 0.0


def test_normalise_legislation_payload() -> None:
    """Test deterministic normalisation from raw XML/HTML."""
    raw_xml = (
        b"<act><heading>Test Act 2026</heading>"
        b'<section id="s1"><heading>Section 1</heading>Content of section 1.</section>'
        b'<schedule id="sch1"><heading>Schedule 1</heading>Schedule text.</schedule>'
        b"<assent-date>2026-01-01</assent-date>"
        b"<commencement-date>2026-02-01</commencement-date>"
        b"</act>"
    )
    rec = normalise_legislation_payload(
        raw_content=raw_xml,
        work_id="act-2026-1",
        title="Test Act 2026",
        canonical_uri="https://www.legislation.govt.nz/act/public/2026/0001/latest/whole.html",
    )

    assert rec.work_id == "act-2026-1"
    assert rec.rights_statement is None
    assert rec.redistribution_policy == "rights_review_required"
    assert len(rec.sections) == 1
    assert len(rec.schedules) == 1
    assert rec.assent_date == "2026-01-01"
    assert rec.commencement_date == "2026-02-01"
    assert len(rec.raw_cas_hash_sha256) == 64
    assert len(rec.raw_cas_hash_blake3) == 64

    # HTML fallback with script/style stripping
    raw_html = (
        b"<html><head><script>alert(1);</script><style>body{color:red;}</style></head>"
        b"<body><h1>Test Bill</h1><p>Introduced bill content</p></body></html>"
    )
    rec_html = normalise_legislation_payload(
        raw_content=raw_html,
        work_id="bill-2026-1",
        title="Test Bill 2026",
        canonical_uri="https://www.legislation.govt.nz/bill/public/2026/0001/latest/whole.html",
    )
    assert rec_html.legislation_type == LegislationType.BILL
    assert rec_html.status == VersionStatus.BILL_INTRODUCED
    assert "alert" not in rec_html.plain_text

    # Order in council and deemed regulation checks
    rec_order = normalise_legislation_payload(
        raw_content=b"<order><heading>Order in Council</heading></order>",
        work_id="order-1",
        title="Order in Council 2026",
        canonical_uri="https://example.com/order",
    )
    assert rec_order.legislation_type == LegislationType.ORDER_IN_COUNCIL

    rec_deemed = normalise_legislation_payload(
        raw_content=b"<html><body>Deemed Reg</body></html>",
        work_id="deemed-1",
        title="Deemed Rule",
        canonical_uri="https://example.com/deemed",
    )
    assert rec_deemed.legislation_type == LegislationType.DEEMED_REGULATION


def test_validate_legislation_record() -> None:
    """Test validation rules on valid and invalid records."""
    valid_rec = LegislationRecord(
        document_id="leg-act-1",
        work_id="act-1",
        title="Valid Act",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://example.com/act",
        raw_cas_hash_sha256="0" * 64,
        raw_cas_hash_blake3="1" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
        byte_size=100,
        sections=[SectionRecord("s1", "1", "H1", "C1")],
    )
    assert len(validate_legislation_record(valid_rec)) == 0

    # Duplicate section ID error
    dup_rec = LegislationRecord(
        document_id="leg-act-1",
        work_id="act-1",
        title="Valid Act",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://example.com/act",
        raw_cas_hash_sha256="0" * 64,
        raw_cas_hash_blake3="1" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
        sections=[
            SectionRecord("s1", "1", "H1", "C1"),
            SectionRecord("s1", "2", "H2", "C2"),
        ],
    )
    dup_errors = validate_legislation_record(dup_rec)
    assert any("duplicate section_id" in err for err in dup_errors)

    invalid_rec = LegislationRecord(
        document_id="",
        work_id="",
        title="",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="invalid-uri",
        raw_cas_hash_sha256="badhash",
        raw_cas_hash_blake3="badhash",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    errors = validate_legislation_record(invalid_rec)
    assert len(errors) >= 4

    with pytest.raises(
        ValueError, match="normalised record missing canonical identity"
    ):
        build_legislation_manifest([invalid_rec])


def test_build_manifest_and_checkpoint_manager(tmp_path: Path) -> None:
    """Test manifest creation and checkpoint manager."""
    rec = LegislationRecord(
        document_id="leg-act-1",
        work_id="act-1",
        title="Valid Act",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://example.com/act",
        raw_cas_hash_sha256="0" * 64,
        raw_cas_hash_blake3="1" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    manifest = build_legislation_manifest([rec], run_id="run-test")
    assert manifest["total_records"] == 1
    assert manifest["run_id"] == "run-test"
    assert manifest["records"][0]["raw_sha256"] == "0" * 64

    with pytest.raises(ValueError, match="manifest record missing canonical identity"):
        build_legislation_manifest([], existing_records=[{}])

    chk_file = tmp_path / "checkpoint.json"
    mgr = LegislationCheckpointManager(chk_file)
    initial = mgr.load()
    assert initial["total_records_preserved"] == 0

    # Corrupted checkpoint file returns default
    chk_file.write_text("invalid json", encoding="utf-8")
    corrupt_loaded = mgr.load()
    assert corrupt_loaded["total_records_preserved"] == 0

    mgr.save(["batch-1"], ["act-1"], 1)
    loaded = mgr.load()
    assert loaded["completed_batches"] == ["batch-1"]
    assert loaded["total_records_preserved"] == 1


def test_api_client_and_discovery() -> None:
    """Test API client pacing and search discovery."""

    def handler(req: httpx.Request) -> httpx.Response:
        if "works" in req.url.path:
            return httpx.Response(
                200,
                json=[
                    {"work_id": "act-1", "title": "Act 1", "type": "act"},
                    {"work_id": "act-2", "title": "Act 2", "type": "act"},
                ],
            )
        if "error" in req.url.path:
            return httpx.Response(500, content=b"Server Error")
        return httpx.Response(200, content=b"<act/>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    api_client = NZLegislationApiClient(api_key="test-key", client=client)

    status, content, _ = api_client.get_document_raw(
        "https://example.com/doc", etag="etag-1"
    )
    assert status == 200
    assert content == b"<act/>"

    inv = build_work_inventory(api_client, search_terms=["Finance"], max_works=1)
    assert inv["candidate_works_count"] == 1
    assert inv["work_ids"] == ["act-1"]


def test_bootstrap_reconcile_and_publication(tmp_path: Path) -> None:
    """Test historical batch loading and publication package builder."""
    # Non-existent batch file returns empty list
    non_existent = tmp_path / "non_existent.txt"
    assert load_work_ids_from_batch_file(non_existent) == []

    batch_file = tmp_path / "historical-work-ids-0001.txt"
    batch_file.write_text("# Comment\nact-1\nact-2\n", encoding="utf-8")

    ids = load_work_ids_from_batch_file(batch_file)
    assert ids == ["act-1", "act-2"]

    rec_batches = reconcile_historical_batches(tmp_path)
    assert rec_batches["total_batches_found"] == 1
    assert rec_batches["total_unique_work_ids"] == 2

    rec = LegislationRecord(
        document_id="leg-1",
        work_id="act-1",
        title="Act 1",
        legislation_type=LegislationType.ACT,
        status=VersionStatus.IN_FORCE,
        canonical_uri="https://example.com/act1",
        raw_cas_hash_sha256="0" * 64,
        raw_cas_hash_blake3="1" * 64,
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    pkg = prepare_legislation_publication_package([rec], tmp_path / "pkg")
    assert pkg["total_records"] == 1
    assert pkg["status"] == "staged_ready_for_publication"


def test_coverage_and_change_reports() -> None:
    """Test coverage tracking and change report generation."""
    cov_empty = LegislationCoverageReport(total_seed_works=0, works_attempted=0)
    assert cov_empty.coverage_percent == 0.0

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
        timestamp="2026-08-18T11:13:00Z",
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
        retrieval_timestamp="2026-08-18T11:13:00Z",
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
