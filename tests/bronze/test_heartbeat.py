"""Unit tests for Bronze Strata B0 Surveillance Heartbeat Ledger."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor
from archive_govt_nz.bronze.heartbeat import (
    SurveillanceHeartbeat,
    SurveillanceLedger,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_surveillance_ledger_append_and_load(tmp_path: Path) -> None:
    """SurveillanceLedger records observations and restores state accurately."""
    ledger_path = tmp_path / "surveillance.jsonl"
    ledger = SurveillanceLedger(ledger_path)

    obs1 = ledger.record_observation(
        source_url="https://legislation.govt.nz/act/2026/01.xml",
        domain="legislation",
        status_code=200,
        disposition="captured",
        etag='"etag-001"',
        content_sha256="abcd" * 16,
        response_time_ms=124.5,
    )
    assert obs1.disposition == "captured"
    assert ledger.get_latest("https://legislation.govt.nz/act/2026/01.xml") == obs1

    obs2 = ledger.record_observation(
        source_url="https://legislation.govt.nz/act/2026/01.xml",
        domain="legislation",
        status_code=304,
        disposition="unmodified",
        etag='"etag-001"',
    )
    assert ledger.get_latest("https://legislation.govt.nz/act/2026/01.xml") == obs2

    # New instance reloads from disk
    reloaded_ledger = SurveillanceLedger(ledger_path)
    assert (
        reloaded_ledger.get_latest("https://legislation.govt.nz/act/2026/01.xml")
        == obs2
    )
    all_obs = reloaded_ledger.load_all()
    assert len(all_obs) == 2


def test_conditional_ingest_304_prevents_cas_amplification(
    tmp_path: Path,
) -> None:
    """HTTP 304 / unmodified checks record heartbeat without writing CAS objects."""
    store = ContentAddressedStore(tmp_path / "cas")
    ingestor = BronzeDomainIngestor(
        store=store, domain="legislation", base_dir=tmp_path / "bronze"
    )

    rec, hb = ingestor.check_and_ingest_conditional(
        record_id="act-001",
        source_url="https://legislation.govt.nz/act/2026/01.xml",
        payload_bytes=None,
        status_code=304,
        etag='"etag-stable"',
    )

    assert rec is None
    assert hb.disposition == "unmodified"
    assert hb.status_code == 304
    # Ensure zero objects committed to CAS sha256 directory
    cas_sha_dir = tmp_path / "cas" / "sha256"
    assert not cas_sha_dir.exists() or len(list(cas_sha_dir.rglob("*"))) == 0


def test_conditional_ingest_200_writes_cas_and_records_heartbeat(
    tmp_path: Path,
) -> None:
    """HTTP 200 payload ingest commits to CAS and produces captured heartbeat."""
    store = ContentAddressedStore(tmp_path / "cas")
    ingestor = BronzeDomainIngestor(
        store=store, domain="legislation", base_dir=tmp_path / "bronze"
    )

    valid_xml = b'<?xml version="1.0"?><act id="act-1"><title>Act 1</title></act>'
    rec, hb = ingestor.check_and_ingest_conditional(
        record_id="act-001",
        source_url="https://legislation.govt.nz/act/2026/01.xml",
        payload_bytes=valid_xml,
        status_code=200,
        etag='"etag-v1"',
        media_type="application/xml",
        response_time_ms=45.2,
    )

    assert rec is not None
    assert hb.disposition == "captured"
    assert hb.content_sha256 == rec.fixity.sha256
    assert hb.response_time_ms == 45.2

    # CAS payload committed
    assert (tmp_path / "cas" / "sha256").exists()


def test_conditional_ingest_error_disposition(tmp_path: Path) -> None:
    """HTTP 500 error records error heartbeat without crashing or writing CAS."""
    store = ContentAddressedStore(tmp_path / "cas")
    ingestor = BronzeDomainIngestor(
        store=store, domain="gazette", base_dir=tmp_path / "bronze"
    )

    rec, hb = ingestor.check_and_ingest_conditional(
        record_id="not-001",
        source_url="https://gazette.govt.nz/notice/001",
        payload_bytes=None,
        status_code=500,
    )

    assert rec is None
    assert hb.disposition == "error"
    assert hb.status_code == 500
    assert "HTTP 500 error" in (hb.error_message or "")


def test_surveillance_heartbeat_model_roundtrip() -> None:
    """SurveillanceHeartbeat serializes and restores faithfully."""
    hb = SurveillanceHeartbeat(
        source_url="https://data.govt.nz/api/3/action/package_show",
        domain="ckan",
        checked_at="2026-08-24T12:00:00Z",
        status_code=200,
        disposition="captured",
        etag="W/123",
        last_modified="Sun, 23 Aug 2026 12:00:00 GMT",
        content_sha256="1234" * 16,
        response_time_ms=89.1,
    )

    d = hb.to_dict()
    restored = SurveillanceHeartbeat.from_dict(d)
    assert restored == hb
