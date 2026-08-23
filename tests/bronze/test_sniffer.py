"""Unit tests for Bronze magic byte sniffer and signature validation engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor
from archive_govt_nz.bronze.sniffer import (
    InvalidPayloadSignatureError,
    sniff_magic_mime,
    validate_payload_signature,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_sniff_magic_mime_formats() -> None:
    """Accurately detects standard formats by initial magic bytes."""
    assert sniff_magic_mime(b"%PDF-1.7\nsome binary stream") == "application/pdf"
    assert sniff_magic_mime(b"WARC/1.0\r\nWARC-Type: response") == "application/warc"
    assert sniff_magic_mime(b"WARC/1.1\r\nWARC-Type: response") == "application/warc"
    assert sniff_magic_mime(b"\x1f\x8b\x08\x00\x00\x00") == "application/gzip"
    assert sniff_magic_mime(b"PK\x03\x04\x14\x00") == "application/zip"
    assert sniff_magic_mime(b'<?xml version="1.0"?><root/>') == "application/xml"
    assert sniff_magic_mime(b"\xef\xbb\xbf<?xml version='1.0'?>") == "application/xml"
    assert sniff_magic_mime(b"<act id='123'>") == "application/xml"
    assert (
        sniff_magic_mime(b"<!DOCTYPE html><html><body>Error</body></html>")
        == "text/html"
    )
    assert (
        sniff_magic_mime(b"<html><head><title>404</title></head></html>") == "text/html"
    )
    assert (
        sniff_magic_mime(b'{"dataset_id": "ds-01", "records": []}')
        == "application/json"
    )
    assert sniff_magic_mime(b"[1, 2, 3, 4]") == "application/json"
    assert sniff_magic_mime(b"id,name,value\n1,Alpha,100\n2,Beta,200\n") == "text/csv"
    assert sniff_magic_mime(b"Simple plain text file") == "text/plain"
    assert sniff_magic_mime(b"") == "application/x-empty"


def test_validate_payload_signature_rejects_empty() -> None:
    """Empty payloads are rejected."""
    result = validate_payload_signature(b"", expected_mime="application/pdf")
    assert not result.is_valid
    assert result.error == "Payload is empty (0 bytes)"


def test_validate_payload_signature_rejects_html_error_for_pdf() -> None:
    """HTML error page disguised as PDF is strictly rejected."""
    fake_pdf = (
        b"<!DOCTYPE html><html><head><title>404 Not Found</title></head>"
        b"<body>Resource not found</body></html>"
    )
    result = validate_payload_signature(fake_pdf, expected_mime="application/pdf")
    assert not result.is_valid
    assert result.error == "HTML error page disguised as PDF"
    assert result.detected_mime == "text/html"
    assert result.expected_mime == "application/pdf"


def test_validate_payload_signature_rejects_polyglots() -> None:
    """Polyglot binary with conflicting embedded HTML tags is rejected."""
    polyglot_pdf = b"%PDF-1.4\n<html><body><script>alert(1)</script></body></html>"
    result = validate_payload_signature(polyglot_pdf, expected_mime="application/pdf")
    assert not result.is_valid
    assert result.is_polyglot
    assert "Polyglot payload detected" in (result.error or "")


def test_validate_payload_signature_allows_compatible_types() -> None:
    """Allows compatible XML and JSON subtypes."""
    json_bytes = b'{"status": "ok"}'
    xml_bytes = b'<?xml version="1.0"?><response/>'

    res_json = validate_payload_signature(json_bytes, expected_mime="application/json")
    assert res_json.is_valid
    assert res_json.detected_mime == "application/json"

    res_xml = validate_payload_signature(xml_bytes, expected_mime="application/xml")
    assert res_xml.is_valid
    assert res_xml.detected_mime == "application/xml"


def test_bronze_ingestor_aborts_on_invalid_signature(tmp_path: Path) -> None:
    """BronzeDomainIngestor aborts and prevents CAS write when signature is invalid."""
    store = ContentAddressedStore(tmp_path / "cas")
    ingestor = BronzeDomainIngestor(store=store, domain="gazette")

    html_error = b"<html><head><title>500 Internal Server Error</title></head></html>"

    with pytest.raises(InvalidPayloadSignatureError) as exc_info:
        ingestor.ingest_payload(
            record_id="gazette-notice-001",
            payload_bytes=html_error,
            source_url="https://gazette.govt.nz/notice/pdf/001",
            media_type="application/pdf",
        )

    assert "HTML error page disguised as PDF" in str(exc_info.value)
    # Ensure no payload objects were committed to CAS store
    assert len(list((tmp_path / "cas" / "sha256").rglob("*"))) == 0


def test_bronze_ingestor_accepts_valid_payload(tmp_path: Path) -> None:
    """BronzeDomainIngestor successfully commits valid payloads to CAS."""
    store = ContentAddressedStore(tmp_path / "cas")
    ingestor = BronzeDomainIngestor(store=store, domain="legislation")

    valid_xml = (
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<act id="act-2026-01"><title>Test Act</title></act>'
    )
    rec = ingestor.ingest_payload(
        record_id="act-001",
        payload_bytes=valid_xml,
        source_url="https://legislation.govt.nz/act/2026/01.xml",
        media_type="application/xml",
    )

    assert rec.record_id == "act-001"
    assert rec.source_metadata.content_type == "application/xml"
    # Ensure CAS write succeeded
    assert (tmp_path / "cas").is_dir()
    assert rec.fixity.sha256 != ""
