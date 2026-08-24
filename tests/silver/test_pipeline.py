"""Tests for the Silver transformation pipeline, schema validation, and bitemporal Parquet."""

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.bronze.manifest import build_bronze_record, create_bronze_manifest
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA
from archive_govt_nz.silver.normalizers import (
    CourtsNoticesSilverNormalizer,
    GazetteSilverNormalizer,
    HealthSilverNormalizer,
    LegislationSilverNormalizer,
)
from archive_govt_nz.silver.pipeline import (
    DOMAIN_NORMALIZERS,
    SilverPipeline,
    get_domain_normalizer,
)


def test_legislation_silver_normalizer() -> None:
    normalizer = LegislationSilverNormalizer()
    payload = b'<act id="123"><title>Public Records Act 2005</title></act>'
    rec = build_bronze_record(
        record_id="act-123",
        domain="legislation",
        payload_bytes=payload,
        source_url="https://legislation.govt.nz/act/public/2005/0123/latest/DLM123.xml",
        cas_path="cas/sha256/11/111111",
        custom_metadata={
            "work_id": "DLM123",
            "title": "Public Records Act 2005",
            "instrument_type": "act",
        },
    )
    silver_records = normalizer.normalize_record(rec, payload)
    assert len(silver_records) == 1
    s_rec = silver_records[0]
    assert s_rec.domain == "legislation"
    assert s_rec.canonical_uri == "nzlc:act/DLM123"
    assert s_rec.title == "Public Records Act 2005"
    assert s_rec.body_format == "xml"
    assert s_rec.is_current is True


def test_gazette_silver_normalizer() -> None:
    normalizer = GazetteSilverNormalizer()
    payload = b"<html><body>Notice of Land Acquisition</body></html>"
    rec = build_bronze_record(
        record_id="notice-456",
        domain="gazette",
        payload_bytes=payload,
        source_url="https://gazette.govt.nz/notice/2026-0456",
        cas_path="cas/sha256/22/222222",
        custom_metadata={
            "notice_id": "2026-0456",
            "title": "Land Acquisition Notice",
            "notice_type": "land",
        },
    )
    silver_records = normalizer.normalize_record(rec, payload)
    assert len(silver_records) == 1
    assert silver_records[0].domain == "gazette"
    assert silver_records[0].canonical_uri == "nzgazette:notice/2026-0456"
    assert silver_records[0].body_format == "html"


def test_health_and_courts_normalizers() -> None:
    health_norm = HealthSilverNormalizer()
    h_payload = b'{"cases": 120, "region": "Auckland"}'
    h_rec = build_bronze_record(
        record_id="covid-20260823",
        domain="health",
        payload_bytes=h_payload,
        source_url="https://health.govt.nz/covid-data.json",
        cas_path="cas/sha256/33/333333",
        custom_metadata={"feed_type": "covid_stats", "title": "Daily COVID Summary"},
    )
    h_silver = health_norm.normalize_record(h_rec, h_payload)
    assert len(h_silver) == 1
    assert h_silver[0].domain == "health"
    assert h_silver[0].body_format == "json"

    courts_norm = CourtsNoticesSilverNormalizer()
    c_payload = b"Public Notice of Hearing: High Court Auckland"
    c_rec = build_bronze_record(
        record_id="court-789",
        domain="courts",
        payload_bytes=c_payload,
        source_url="https://courts.govt.nz/notice/789",
        cas_path="cas/sha256/44/444444",
        custom_metadata={"notice_id": "789", "court_name": "High Court Auckland"},
    )
    c_silver = courts_norm.normalize_record(c_rec, c_payload)
    assert len(c_silver) == 1
    assert c_silver[0].domain == "courts"
    assert c_silver[0].canonical_uri == "nzcourt:notice/789"


def test_silver_pipeline_end_to_end(tmp_path: Path) -> None:
    silver_dir = tmp_path / "silver"
    cas_dir = tmp_path / "cas_store"
    cas_dir.mkdir(parents=True)

    payload = b"Legislation Sample Act 2026 text"
    cas_rel = "sha256/55/555555"
    cas_file = cas_dir / cas_rel
    cas_file.parent.mkdir(parents=True, exist_ok=True)
    cas_file.write_bytes(payload)

    record = build_bronze_record(
        record_id="act-sample-2026",
        domain="legislation",
        payload_bytes=payload,
        source_url="https://legislation.govt.nz/act/2026",
        cas_path=cas_rel,
        custom_metadata={"work_id": "SAMPLE2026", "title": "Sample Act 2026"},
    )

    manifest = create_bronze_manifest(
        manifest_id="manifest-leg-001",
        batch_id="batch-leg-001",
        domain="legislation",
        records=[record],
    )

    pipeline = SilverPipeline(silver_base_dir=silver_dir)
    result = pipeline.transform_manifest(manifest, cas_base_dir=cas_dir)

    assert result.records_transformed == 1
    assert result.parquet_path.exists()
    assert result.parquet_bytes > 0

    # Read back parquet and verify schema
    table = pq.read_table(result.parquet_path)
    assert table.num_rows == 1
    assert table.schema == SILVER_ARROW_SCHEMA
    assert table.column("domain")[0].as_py() == "legislation"
    assert table.column("canonical_uri")[0].as_py() == "nzlc:act/SAMPLE2026"


def test_domain_normalizers_proxy() -> None:
    """DomainNormalizersProxy maps and lazily loads all domain normalizers."""
    assert "hansard" in DOMAIN_NORMALIZERS
    assert "hathi" in DOMAIN_NORMALIZERS
    assert "medilegal" in DOMAIN_NORMALIZERS
    assert "unknown_domain" not in DOMAIN_NORMALIZERS
    assert len(DOMAIN_NORMALIZERS) == 8
    assert list(DOMAIN_NORMALIZERS) == [
        "legislation",
        "gazette",
        "courts",
        "health",
        "treasury",
        "hansard",
        "hathi",
        "medilegal",
    ]
    assert DOMAIN_NORMALIZERS.get("hansard") is not None
    assert DOMAIN_NORMALIZERS.get("hathi") is not None
    assert DOMAIN_NORMALIZERS.get("medilegal") is not None
    assert DOMAIN_NORMALIZERS.get("nonexistent") is None
    assert get_domain_normalizer("nonexistent") is None

    with pytest.raises(KeyError):
        _ = DOMAIN_NORMALIZERS["nonexistent"]
