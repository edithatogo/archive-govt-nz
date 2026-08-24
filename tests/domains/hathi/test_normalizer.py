"""Tests for HathiTrust Silver bitemporal normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pyarrow.parquet as pq

from archive_govt_nz.bronze.manifest import (
    build_bronze_record,
    create_bronze_manifest,
)
from archive_govt_nz.domains.hathi.normalizer import (
    HathiSilverNormalizer,
    classify_historical_rights,
)
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA
from archive_govt_nz.silver.pipeline import SilverPipeline

if TYPE_CHECKING:
    from pathlib import Path


SAMPLE_HATHI_PAYLOAD = {
    "schema_version": "archive-govt-nz.hathi-volume/v1",
    "volume_id": "nyp.33433012345678",
    "title": "Ordinances of the Province of Auckland",
    "author": "Auckland Provincial Council",
    "publication_year": 1865,
    "rights_attributes": "pd",
    "source_institution": "New York Public Library",
    "page_count": 2,
    "ocr_pages": [
        {
            "page_seq": 1,
            "page_number": "1",
            "page_text": "An Ordinance under the New Zealand Constitution Act 1852.",
        },
        {
            "page_seq": 2,
            "page_number": "2",
            "page_text": "Enacted under the Native Land Act 1865.",
        },
    ],
}


def test_classify_historical_rights() -> None:
    """classify_historical_rights resolves historical copyright terms."""
    assert classify_historical_rights(1850, "pd") == "public_domain"
    assert classify_historical_rights(1910, "open_access") == "public_domain"
    assert classify_historical_rights(1950, "restricted") == "crown_copyright_expired"
    assert classify_historical_rights(1990, "open_access") == "open_access"


def test_hathi_silver_normalizer() -> None:
    """HathiSilverNormalizer normalizes volume pages into Silver records."""
    normalizer = HathiSilverNormalizer()
    payload = json.dumps(SAMPLE_HATHI_PAYLOAD).encode("utf-8")

    bronze_record = build_bronze_record(
        record_id="nyp.33433012345678",
        domain="hathi",
        payload_bytes=payload,
        source_url="https://catalog.hathitrust.org/Record/001",
        cas_path="cas/aa/bb",
        custom_metadata={"batch_id": "batch-hathi-001"},
    )

    silver_records = normalizer.normalize_record(bronze_record, payload)
    assert len(silver_records) == 2

    r1 = silver_records[0]
    assert r1.nz_canonical_urn == "urn:nz-govt:hathi:page:nyp.33433012345678_p0001"
    assert r1.domain == "hathi"
    assert r1.entity_type == "historical_publication:page"
    assert r1.valid_from == "1865-01-01"
    assert r1.body_text is not None
    assert "Constitution Act 1852" in r1.body_text

    meta1 = json.loads(r1.metadata_json)
    assert meta1["rights_status"] == "public_domain"
    assert "New Zealand Constitution Act 1852" in meta1["act_references"]


def test_hathi_silver_normalizer_zero_pages() -> None:
    """HathiSilverNormalizer handles volume with 0 pages gracefully."""
    normalizer = HathiSilverNormalizer()
    payload = json.dumps(
        {
            "schema_version": "archive-govt-nz.hathi-volume/v1",
            "volume_id": "empty-vol-01",
            "title": "Empty Volume",
            "rights_attributes": "pd",
            "ocr_pages": [],
        }
    ).encode("utf-8")

    bronze_record = build_bronze_record(
        record_id="empty-vol-01",
        domain="hathi",
        payload_bytes=payload,
        source_url="https://catalog.hathitrust.org/Record/empty",
        cas_path="cas/empty",
    )

    records = normalizer.normalize_record(bronze_record, payload)
    assert len(records) == 1
    assert records[0].entity_type == "historical_publication:volume"
    assert records[0].nz_canonical_urn == "urn:nz-govt:hathi:volume:empty-vol-01"


def test_hathi_silver_pipeline_integration(tmp_path: Path) -> None:
    """SilverPipeline processes Bronze Hathi manifest into valid Parquet."""
    cas_dir = tmp_path / "cas"
    cas_dir.mkdir(parents=True)
    payload = json.dumps(SAMPLE_HATHI_PAYLOAD).encode("utf-8")
    payload_file = cas_dir / "hathi_sample.json"
    payload_file.write_bytes(payload)

    rec = build_bronze_record(
        record_id="nyp.33433012345678",
        domain="hathi",
        payload_bytes=payload,
        source_url="https://catalog.hathitrust.org/Record/001",
        cas_path=str(payload_file),
    )

    manifest = create_bronze_manifest(
        manifest_id="hathi-test",
        batch_id="batch-h-01",
        domain="hathi",
        records=[rec],
    )

    pipeline = SilverPipeline(silver_base_dir=tmp_path / "silver")
    res = pipeline.transform_manifest(manifest, cas_base_dir=cas_dir)

    assert res.domain == "hathi"
    assert res.records_transformed == 2
    assert res.parquet_path.is_file()

    table = pq.read_table(res.parquet_path)
    assert table.schema == SILVER_ARROW_SCHEMA
    assert table.num_rows == 2
