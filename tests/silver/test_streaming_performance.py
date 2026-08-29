"""Test suite for chunked streaming transformation in SilverPipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from archive_govt_nz.bronze.manifest import create_bronze_manifest
from archive_govt_nz.bronze.models import (
    BronzePayloadFixity,
    BronzeRecord,
    BronzeSourceMetadata,
)
from archive_govt_nz.silver.pipeline import SilverPipeline


def test_silver_pipeline_streaming_chunks(tmp_path: Path) -> None:
    """Verify SilverPipeline streams in small batches without error and produces valid Parquet."""
    cas_dir = tmp_path / "cas"
    cas_dir.mkdir(parents=True)

    # Create 15 synthetic bronze records
    records: list[BronzeRecord] = []
    for i in range(15):
        payload_file = cas_dir / f"payload_{i}.json"
        content = json.dumps(
            {"title": f"Treasury Release {i}", "fiscal_year": "2025/26"}
        ).encode()
        payload_file.write_bytes(content)

        fixity = BronzePayloadFixity(
            sha256="fake_sha",
            blake3="fake_blake",
            cidv1="fake_cid",
            size_bytes=len(content),
            cas_path=str(payload_file),
            media_type="application/json",
        )
        src = BronzeSourceMetadata(
            source_url=f"https://treasury.govt.nz/rel/{i}",
            observed_at="2026-08-25T19:00:00Z",
            status_code=200,
        )
        records.append(
            BronzeRecord(
                record_id=f"rec-{i}",
                domain="treasury",
                source_metadata=src,
                fixity=fixity,
            )
        )

    manifest = create_bronze_manifest(
        manifest_id="mani-stream-001",
        batch_id="batch-stream-001",
        domain="treasury",
        records=records,
    )

    silver_out = tmp_path / "silver"
    pipeline = SilverPipeline(silver_base_dir=silver_out)

    # Set small chunk_size to force multiple streaming batch writes
    res = pipeline.transform_manifest(manifest, chunk_size=5)

    assert res.domain == "treasury"
    assert res.records_transformed == 15
    assert res.parquet_path.exists()

    # Verify resulting Parquet file contains all 15 records
    table = pq.read_table(res.parquet_path)
    assert table.num_rows == 15
    assert "nz_canonical_urn" in table.column_names
