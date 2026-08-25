"""Tests for SilverPipeline stateful checkpointing and memory-bounded streaming."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

from archive_govt_nz.bronze.models import (
    BronzeIngestionManifest,
    BronzePayloadFixity,
    BronzeRecord,
    BronzeSourceMetadata,
)
from archive_govt_nz.silver.pipeline import SilverPipeline


def test_silver_pipeline_with_checkpoint_resume(tmp_path: Path) -> None:
    """Validate SilverPipeline stateful checkpointing and recovery."""
    cas_dir = tmp_path / "cas"
    cas_dir.mkdir()
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    # Create dummy CAS files and records
    records: list[BronzeRecord] = []
    now_str = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for i in range(10):
        cas_file = cas_dir / f"payload_{i}.json"
        data = {
            "notice_id": f"2026-gn{i}",
            "title": f"Notice {i}",
            "notice_type": "General",
            "text": f"Text content for notice {i}",
            "publication_date": "2026-08-26",
            "nz_canonical_urn": f"urn:nz:gazette:2026:gn{i}",
        }
        cas_file.write_text(json.dumps(data), encoding="utf-8")
        records.append(
            BronzeRecord(
                record_id=f"rec_{i}",
                domain="gazette",
                source_metadata=BronzeSourceMetadata(
                    source_url=f"https://gazette.govt.nz/notice/{i}",
                    observed_at=now_str,
                ),
                fixity=BronzePayloadFixity(
                    sha256=f"hash_{i:064d}",
                    blake3=f"b3_{i:064d}",
                    size_bytes=cas_file.stat().st_size,
                    cas_path=str(cas_file),
                    cidv1=f"cid_{i}",
                ),
            )
        )

    manifest = BronzeIngestionManifest(
        manifest_id="man-checkpoint-test",
        batch_id="batch-001",
        domain="gazette",
        created_at=now_str,
        records=records,
        records_count=10,
        total_bytes=1000,
        sha256_manifest="manifest_sha256",
    )

    # Simulate an interrupted run by pre-creating a checkpoint at index 4 (5 records already processed)
    domain_silver = silver_dir / "gazette"
    domain_silver.mkdir(parents=True, exist_ok=True)
    checkpoint_file = domain_silver / ".checkpoint.json"
    checkpoint_file.write_text(
        json.dumps(
            {
                "domain": "gazette",
                "last_processed_index": 4,
                "records_transformed": 5,
            }
        ),
        encoding="utf-8",
    )

    pipeline = SilverPipeline(silver_base_dir=silver_dir)
    res = pipeline.transform_manifest(manifest, chunk_size=3, resume=True)

    assert res.domain == "gazette"
    assert res.checkpoint_resumed is True
    assert res.records_transformed == 10
    assert not checkpoint_file.exists()

    # Read output Parquet table
    table = pq.read_table(res.parquet_path)
    assert table.num_rows == 5  # processed remaining 5 records
