"""Tests for the generalized Bronze domain ingestion adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor, IngestionResult
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_bronze_domain_ingestor_flow(tmp_path: Path) -> None:
    """Test full ingestion flow into CAS and manifest creation."""
    store = ContentAddressedStore(tmp_path / "cas")
    out_dir = tmp_path / "bronze_out"
    ingestor = BronzeDomainIngestor(store=store, domain="test_domain", base_dir=out_dir)

    payload1 = b"Sample raw bitstream 1"
    payload2 = b"Sample raw bitstream 2"

    rec1 = ingestor.ingest_payload(
        record_id="rec-001",
        payload_bytes=payload1,
        source_url="https://example.test/item/1",
        media_type="text/plain",
    )
    rec2 = ingestor.ingest_payload(
        record_id="rec-002",
        payload_bytes=payload2,
        source_url="https://example.test/item/2",
        media_type="application/json",
    )

    assert rec1.record_id == "rec-001"
    assert rec1.fixity.size_bytes == len(payload1)
    assert rec2.record_id == "rec-002"
    assert rec2.fixity.size_bytes == len(payload2)

    res = ingestor.finalize_batch(
        batch_id="batch-001",
        manifest_id="manifest-001",
        records=[rec1, rec2],
    )

    assert isinstance(res, IngestionResult)
    assert res.status == "success"
    assert res.records_synced == 2
    assert res.bytes_synced == len(payload1) + len(payload2)
    assert res.manifest_path is not None
    assert (out_dir / "manifest-manifest-001.json").is_file()
    assert (out_dir / "checkpoint.json").is_file()

    chk = json.loads((out_dir / "checkpoint.json").read_text(encoding="utf-8"))
    assert chk["latest_batch_id"] == "batch-001"
    assert chk["total_records"] == 2
