"""Tests for Bronze layer models, manifest generation, and fixity verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz.bronze.manifest import (
    build_bronze_record,
    compute_hashes,
    create_bronze_manifest,
    verify_bronze_manifest_fixity,
)
from archive_govt_nz.bronze.models import (
    BRONZE_MANIFEST_SCHEMA_V1,
    BronzeIngestionManifest,
    BronzePayloadFixity,
    BronzeSourceMetadata,
)


@pytest.fixture
def manifest_schema() -> dict[str, object]:
    """Load the official Bronze Ingestion Manifest JSON Schema."""
    schema_path = (
        Path(__file__).parents[2]
        / "schemas"
        / "bronze-ingestion-manifest-v1.schema.json"
    )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_compute_hashes() -> None:
    """Test cryptographic digest calculation."""
    payload = b"<test>payload</test>"
    sha256_hash, blake3_hash = compute_hashes(payload)

    assert len(sha256_hash) == 64
    assert len(blake3_hash) == 64
    assert sha256_hash != blake3_hash


def test_compute_hashes_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test hash calculation when blake3 module is absent."""
    monkeypatch.setattr("archive_govt_nz.bronze.manifest.blake3", None)
    payload = b"<test>payload</test>"
    sha256_hash, blake3_hash = compute_hashes(payload)

    assert len(sha256_hash) == 64
    assert len(blake3_hash) == 64


def test_bronze_payload_fixity_roundtrip() -> None:
    """Test BronzePayloadFixity serialization and deserialization."""
    fixity = BronzePayloadFixity(
        sha256="a" * 64,
        blake3="b" * 64,
        size_bytes=1024,
        cas_path="cas/sha256/aa/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        warc_record_id="urn:uuid:12345",
        media_type="application/xml",
    )
    as_dict = fixity.to_dict()
    restored = BronzePayloadFixity.from_dict(as_dict)

    assert restored.sha256 == fixity.sha256
    assert restored.blake3 == fixity.blake3
    assert restored.size_bytes == 1024
    assert restored.cas_path == fixity.cas_path
    assert restored.warc_record_id == "urn:uuid:12345"
    assert restored.media_type == "application/xml"


def test_bronze_source_metadata_roundtrip() -> None:
    """Test BronzeSourceMetadata serialization and deserialization."""
    meta = BronzeSourceMetadata(
        source_url="https://example.test/source.xml",
        observed_at="2026-08-23T17:00:00Z",
        status_code=200,
        content_type="application/xml",
        encoding="utf-8",
        etag='"etag123"',
        last_modified="Sun, 23 Aug 2026 12:00:00 GMT",
        headers={"content-type": "application/xml", "server": "nginx"},
        rate_limit_remaining=50,
        rate_limit_reset=1700000000,
    )
    as_dict = meta.to_dict()
    restored = BronzeSourceMetadata.from_dict(as_dict)

    assert restored.source_url == meta.source_url
    assert restored.observed_at == meta.observed_at
    assert restored.status_code == 200
    assert restored.content_type == "application/xml"
    assert restored.encoding == "utf-8"
    assert restored.etag == '"etag123"'
    assert restored.headers["server"] == "nginx"
    assert restored.rate_limit_remaining == 50
    assert restored.rate_limit_reset == 1700000000


def test_build_bronze_record_and_manifest(manifest_schema: dict[str, object]) -> None:
    """Test end-to-end record construction, manifest creation, and schema validity."""
    payload_1 = b'<act year="2024" number="1"><title>Test Act 1</title></act>'
    payload_2 = b'<act year="2024" number="2"><title>Test Act 2</title></act>'

    rec1 = build_bronze_record(
        record_id="rec-001",
        domain="legislation",
        payload_bytes=payload_1,
        source_url="https://www.legislation.govt.nz/act/public/2024/0001/latest/whole.xml",
        cas_path="cas/sha256/11/1111111111111111111111111111111111111111111111111111111111111111",
        media_type="application/xml",
        custom_metadata={"title": "Test Act 1"},
    )
    rec2 = build_bronze_record(
        record_id="rec-002",
        domain="legislation",
        payload_bytes=payload_2,
        source_url="https://www.legislation.govt.nz/act/public/2024/0002/latest/whole.xml",
        cas_path="cas/sha256/22/2222222222222222222222222222222222222222222222222222222222222222",
        media_type="application/xml",
        custom_metadata={"title": "Test Act 2"},
    )

    manifest = create_bronze_manifest(
        manifest_id="manifest-leg-20260823-001",
        batch_id="batch-leg-001",
        domain="legislation",
        records=[rec1, rec2],
        created_at="2026-08-23T17:00:00Z",
    )

    assert manifest.schema_version == BRONZE_MANIFEST_SCHEMA_V1
    assert manifest.records_count == 2
    assert manifest.total_bytes == len(payload_1) + len(payload_2)
    assert manifest.sha256_manifest is not None

    # Verify JSON Schema validity
    manifest_dict = manifest.to_dict()
    Draft202012Validator.check_schema(manifest_schema)
    validator = Draft202012Validator(manifest_schema)
    validator.validate(manifest_dict)

    # Verify fixity
    assert verify_bronze_manifest_fixity(manifest) is True

    # Test roundtrip from_dict
    restored_manifest = BronzeIngestionManifest.from_dict(manifest_dict)
    assert restored_manifest.manifest_id == manifest.manifest_id
    assert restored_manifest.records_count == 2
    assert restored_manifest.total_bytes == manifest.total_bytes
    assert restored_manifest.sha256_manifest == manifest.sha256_manifest


def test_verify_manifest_fixity_fails_on_tampering() -> None:
    """Test that tampering with manifest records invalidates fixity verification."""
    payload = b"<notice>Gazette Notice</notice>"
    rec = build_bronze_record(
        record_id="rec-gaz-001",
        domain="gazette",
        payload_bytes=payload,
        source_url="https://gazette.govt.nz/notice/2026-001",
        cas_path="cas/sha256/33/3333333333333333333333333333333333333333333333333333333333333333",
    )
    manifest = create_bronze_manifest(
        manifest_id="manifest-gaz-001",
        batch_id="batch-gaz-001",
        domain="gazette",
        records=[rec],
    )

    assert verify_bronze_manifest_fixity(manifest) is True

    # Manifest with empty sha256
    unsigned = BronzeIngestionManifest(
        manifest_id=manifest.manifest_id,
        batch_id=manifest.batch_id,
        domain=manifest.domain,
        created_at=manifest.created_at,
        records=manifest.records,
        records_count=1,
        total_bytes=len(payload),
        sha256_manifest="",
    )
    assert verify_bronze_manifest_fixity(unsigned) is False

    # Tampered manifest
    tampered_rec = build_bronze_record(
        record_id="rec-gaz-001-tampered",
        domain="gazette",
        payload_bytes=payload,
        source_url="https://gazette.govt.nz/notice/2026-001",
        cas_path="cas/sha256/33/3333333333333333333333333333333333333333333333333333333333333333",
    )
    tampered = BronzeIngestionManifest(
        manifest_id=manifest.manifest_id,
        batch_id=manifest.batch_id,
        domain=manifest.domain,
        created_at=manifest.created_at,
        records=[tampered_rec],
        records_count=1,
        total_bytes=len(payload),
        sha256_manifest=manifest.sha256_manifest,
    )
    assert verify_bronze_manifest_fixity(tampered) is False
