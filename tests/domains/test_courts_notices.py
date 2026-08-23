"""Tests for Courts NZ Public Notices Bronze ingestion adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.domains.gazette.courts_notices import CourtsPublicNoticesIngestor
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_courts_public_notices_ingestor(tmp_path: Path) -> None:
    """Test public notices ingestion and batch finalization."""
    store = ContentAddressedStore(tmp_path / "cas")
    out_dir = tmp_path / "courts_bronze"
    ingestor = CourtsPublicNoticesIngestor(store=store, base_dir=out_dir)

    payload = b'{"court": "High Court", "notice": "Liquidation order granted"}'
    rec = ingestor.ingest_notice(
        notice_id="2026-HC-001",
        notice_type="liquidation",
        court_name="High Court of New Zealand",
        title="In the Matter of ABC Ltd (In Liquidation)",
        payload_bytes=payload,
        source_url="https://example.court.nz/notices/2026-HC-001",
        published_at="2026-08-23T10:00:00Z",
    )

    assert rec.record_id == "rec-court-2026-HC-001"
    assert rec.custom_metadata["court_name"] == "High Court of New Zealand"

    res = ingestor.finalize(batch_id="courts-batch-001", records=[rec])
    assert res.status == "success"
    assert res.records_synced == 1
