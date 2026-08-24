"""Unit tests verifying Canonical URN injection into Silver layer records."""

from __future__ import annotations

from archive_govt_nz.bronze.manifest import build_bronze_record
from archive_govt_nz.core.urn import is_valid_urn
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA
from archive_govt_nz.silver.normalizers import (
    GazetteSilverNormalizer,
    HealthSilverNormalizer,
    LegislationSilverNormalizer,
    TreasurySilverNormalizer,
)


def test_silver_arrow_schema_contains_link_columns() -> None:
    """SILVER_ARROW_SCHEMA contains canonical URN and multihash CIDv1 fields."""
    field_names = SILVER_ARROW_SCHEMA.names
    assert "nz_canonical_urn" in field_names
    assert "nz_content_cidv1" in field_names
    assert "nz_source_record_id" in field_names
    assert "nz_acquisition_id" in field_names
    assert "nz_content_id" in field_names


def test_legislation_normalizer_injects_valid_urn() -> None:
    """LegislationSilverNormalizer generates a valid canonical URN and CIDv1."""
    norm = LegislationSilverNormalizer()
    payload = b'<?xml version="1.0"?><act id="act-1"><title>Act 1</title></act>'
    rec = build_bronze_record(
        record_id="act-public-2026-0001",
        domain="legislation",
        payload_bytes=payload,
        source_url="https://legislation.govt.nz/act/2026/0001.xml",
        cas_path="data/cas/sha256/123",
        custom_metadata={"work_id": "act-public-2026-0001", "instrument_type": "act"},
    )

    silver_records = norm.normalize_record(rec, payload)
    assert len(silver_records) == 1
    sr = silver_records[0]

    assert sr.nz_canonical_urn is not None
    assert is_valid_urn(sr.nz_canonical_urn)
    assert sr.nz_canonical_urn == "urn:nz-govt:legislation:act:act-public-2026-0001"
    assert sr.nz_content_cidv1 == rec.fixity.cidv1
    assert sr.to_dict()["nz_canonical_urn"] == sr.nz_canonical_urn


def test_gazette_and_health_and_treasury_normalizers_inject_urns() -> None:
    """Gazette, Health, and Treasury normalizers produce valid canonical URNs."""
    gaz_norm = GazetteSilverNormalizer()
    payload = b"<html>Notice content</html>"
    rec_gaz = build_bronze_record(
        record_id="2026-go1234",
        domain="gazette",
        payload_bytes=payload,
        source_url="https://gazette.govt.nz/notice/2026-go1234",
        cas_path="data/cas/sha256/456",
        custom_metadata={"notice_id": "2026-go1234", "notice_type": "official"},
    )
    srs_gaz = gaz_norm.normalize_record(rec_gaz, payload)
    assert is_valid_urn(srs_gaz[0].nz_canonical_urn or "")
    assert (
        srs_gaz[0].nz_canonical_urn == "urn:nz-govt:gazette:notice_official:2026-go1234"
    )

    health_norm = HealthSilverNormalizer()
    rec_health = build_bronze_record(
        record_id="moh-schedule-01",
        domain="health",
        payload_bytes=b'{"status":"ok"}',
        source_url="https://health.govt.nz/api/data",
        cas_path="data/cas/sha256/789",
        custom_metadata={"feed_type": "pae_ora"},
    )
    srs_health = health_norm.normalize_record(rec_health, b'{"status":"ok"}')
    assert is_valid_urn(srs_health[0].nz_canonical_urn or "")
    assert (
        srs_health[0].nz_canonical_urn == "urn:nz-govt:health:pae_ora:moh-schedule-01"
    )

    treasury_norm = TreasurySilverNormalizer()
    rec_treasury = build_bronze_record(
        record_id="befu-2026",
        domain="treasury",
        payload_bytes=payload,
        source_url="https://treasury.govt.nz/befu-2026",
        cas_path="data/cas/sha256/999",
        custom_metadata={"document_id": "befu-2026"},
    )
    srs_treasury = treasury_norm.normalize_record(rec_treasury, payload)
    assert is_valid_urn(srs_treasury[0].nz_canonical_urn or "")
    assert srs_treasury[0].nz_canonical_urn == "urn:nz-govt:treasury:release:befu-2026"
