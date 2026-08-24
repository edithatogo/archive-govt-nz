"""Tests for Medico-Legal Silver bitemporal normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pyarrow.parquet as pq

from archive_govt_nz.bronze.manifest import (
    build_bronze_record,
    create_bronze_manifest,
)
from archive_govt_nz.domains.medilegal.normalizer import MedicoLegalSilverNormalizer
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA
from archive_govt_nz.silver.pipeline import SilverPipeline

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_CASE_JSON = {
    "schema_version": "archive-govt-nz.medilegal-case/v1",
    "case_id": "HDC-21HDC01234",
    "tribunal": "HDC",
    "decision_date": "2023-05-12",
    "title": "Breach of Right 4(1)",
    "findings_summary": "Finding of breach.",
    "full_text": "Decision under the Health and Disability Commissioner Act 1994.",
    "statutory_provisions": ["Health and Disability Commissioner Act 1994"],
    "is_anonymized": True,
}


def test_medilegal_silver_normalizer_json() -> None:
    """Normalizer transforms Bronze JSON record into normalized Silver record."""
    normalizer = MedicoLegalSilverNormalizer()
    payload = json.dumps(SAMPLE_CASE_JSON).encode("utf-8")

    bronze_record = build_bronze_record(
        domain="medilegal",
        record_id="HDC-21HDC01234",
        payload_bytes=payload,
        source_url="https://www.hdc.org.nz/decisions/21HDC01234",
        cas_path="cas/aa/bb",
        custom_metadata={"batch_id": "batch-medilegal-001"},
    )

    silver_records = normalizer.normalize_record(bronze_record, payload)
    assert len(silver_records) == 1

    r = silver_records[0]
    assert r.nz_canonical_urn == "urn:nz-govt:medilegal:decision:HDC-21HDC01234"
    assert r.domain == "medilegal"
    assert r.entity_type == "medico_legal:decision:hdc"
    assert r.valid_from == "2023-05-12"

    meta = json.loads(r.metadata_json)
    assert meta["case_id"] == "HDC-21HDC01234"
    assert meta["tribunal"] == "HDC"
    assert meta["statutory_provisions"] == [
        "Health and Disability Commissioner Act 1994"
    ]


def test_medilegal_silver_normalizer_raw_text() -> None:
    """Normalizer transforms Bronze raw text payload into Silver record."""
    normalizer = MedicoLegalSilverNormalizer()
    raw_payload = (
        b"Summary finding.\n\nDecision text under Medicines Act 1981 regarding Dr B."
    )

    bronze_record = build_bronze_record(
        domain="medilegal",
        record_id="HPDT-999",
        payload_bytes=raw_payload,
        source_url="https://www.hpdt.org.nz/decisions/999",
        cas_path="cas/cc/dd",
        custom_metadata={
            "case_id": "HPDT-999",
            "tribunal": "HPDT",
            "decision_date": "2021-08-10",
            "batch_id": "batch-medilegal-002",
        },
    )

    silver_records = normalizer.normalize_record(bronze_record, raw_payload)
    assert len(silver_records) == 1
    assert (
        silver_records[0].nz_canonical_urn == "urn:nz-govt:medilegal:decision:HPDT-999"
    )
    assert silver_records[0].entity_type == "medico_legal:decision:hpdt"
    assert silver_records[0].valid_from == "2021-08-10"


def test_medilegal_silver_pipeline_e2e(tmp_path: Path) -> None:
    """End-to-end SilverPipeline execution produces schema-compliant Parquet."""
    cas_dir = tmp_path / "cas"
    payload = json.dumps(SAMPLE_CASE_JSON).encode("utf-8")

    bronze_record = build_bronze_record(
        domain="medilegal",
        record_id="HDC-21HDC01234",
        payload_bytes=payload,
        source_url="https://www.hdc.org.nz/decisions/21HDC01234",
        cas_path="medilegal/test.json",
    )

    cas_file = cas_dir / "medilegal" / "test.json"
    cas_file.parent.mkdir(parents=True, exist_ok=True)
    cas_file.write_bytes(payload)

    manifest = create_bronze_manifest(
        manifest_id="manifest-medilegal-001",
        domain="medilegal",
        batch_id="batch-medilegal-001",
        records=[bronze_record],
    )

    pipeline = SilverPipeline(silver_base_dir=tmp_path / "silver")
    result = pipeline.transform_manifest(manifest, cas_base_dir=cas_dir)

    assert result.domain == "medilegal"
    assert result.records_transformed == 1
    assert result.parquet_path.exists()

    table = pq.read_table(result.parquet_path)
    assert table.schema.equals(SILVER_ARROW_SCHEMA)
    assert table.num_rows == 1
