"""Unit tests for Silver Hansard bitemporal normalization and entity reconciliation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pyarrow.parquet as pq

from archive_govt_nz.bronze.manifest import (
    build_bronze_record,
    create_bronze_manifest,
)
from archive_govt_nz.core.urn import is_valid_urn
from archive_govt_nz.domains.hansard.normalizer import HansardSilverNormalizer
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA
from archive_govt_nz.silver.pipeline import SilverPipeline

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_DEBATE_XML = (
    b'<?xml version="1.0" encoding="utf-8"?>\n'
    b'<debate id="HANSARD-20260820-01" date="2026-08-20" '
    b'parliament="54" session="1" volume="776">\n'
    b"    <heading>Oral Questions \xe2\x80\x94 Health and Justice</heading>\n"
    b'    <speech id="SPCH-001" speaker="Hon Dr Ayesha Verrall" '
    b'role="Spokesperson for Health" type="question" '
    b'time="2026-08-20T14:10:00Z">\n'
    b"        <p>Will the Minister support the Pae Ora (Healthy Futures) "
    b"Act 2022 and repeal of the Medicines Amendment Bill 2026?</p>\n"
    b"    </speech>\n"
    b'    <speech id="SPCH-002" speaker="Hon Dr Shane Reti" '
    b'role="Minister of Health" type="answer" '
    b'time="2026-08-20T14:10:30Z">\n'
    b"        <p>The Government remains committed to clinical safety and "
    b"timely access under the Public Finance Act 1989.</p>\n"
    b"    </speech>\n"
    b"</debate>\n"
)


def test_hansard_silver_normalizer_direct() -> None:
    """HansardSilverNormalizer transforms XML into normalized Silver records."""
    normalizer = HansardSilverNormalizer()
    bronze_rec = build_bronze_record(
        record_id="HANSARD-20260820-01",
        domain="hansard",
        payload_bytes=SAMPLE_DEBATE_XML,
        source_url="https://www.parliament.nz/en/pb/hansard-debates/HANSARD-20260820-01",
        cas_path="data/cas/sha256/hansard1",
        custom_metadata={"batch_id": "batch-hansard-001"},
    )

    silver_recs = normalizer.normalize_record(bronze_rec, SAMPLE_DEBATE_XML)
    assert len(silver_recs) == 2

    # Speech 1 verification
    sr1 = silver_recs[0]
    assert sr1.domain == "hansard"
    assert sr1.entity_type == "parliamentary_speech:question"
    assert is_valid_urn(sr1.nz_canonical_urn or "")
    assert (
        sr1.nz_canonical_urn
        == "urn:nz-govt:hansard:speech:HANSARD-20260820-01_SPCH-001"
    )
    assert sr1.valid_from == "2026-08-20"
    assert sr1.body_format == "text"
    assert "Pae Ora (Healthy Futures) Act" in sr1.body_text

    meta1 = json.loads(sr1.metadata_json)
    assert meta1["speaker_name"] == "Hon Dr Ayesha Verrall"
    assert meta1["speaker_role"] == "Spokesperson for Health"
    assert "Medicines Amendment Bill" in meta1["bill_references"]
    assert "Pae Ora (Healthy Futures) Act" in meta1["act_references"]

    # Speech 2 verification
    sr2 = silver_recs[1]
    assert sr2.entity_type == "parliamentary_speech:answer"
    assert (
        sr2.nz_canonical_urn
        == "urn:nz-govt:hansard:speech:HANSARD-20260820-01_SPCH-002"
    )
    meta2 = json.loads(sr2.metadata_json)
    assert meta2["speaker_name"] == "Hon Dr Shane Reti"
    assert "Public Finance Act" in meta2["act_references"]


def test_hansard_silver_pipeline_end_to_end(tmp_path: Path) -> None:
    """SilverPipeline processes Bronze Hansard manifest into valid Parquet."""
    cas_dir = tmp_path / "cas"
    cas_dir.mkdir(parents=True)
    payload_file = cas_dir / "hansard_sample.xml"
    payload_file.write_bytes(SAMPLE_DEBATE_XML)

    rec = build_bronze_record(
        record_id="HANSARD-20260820-01",
        domain="hansard",
        payload_bytes=SAMPLE_DEBATE_XML,
        source_url="https://www.parliament.nz/hansard",
        cas_path=str(payload_file),
    )

    manifest = create_bronze_manifest(
        manifest_id="hansard-test",
        batch_id="batch-h-01",
        domain="hansard",
        records=[rec],
    )

    pipeline = SilverPipeline(silver_base_dir=tmp_path / "silver")
    res = pipeline.transform_manifest(manifest, cas_base_dir=cas_dir)

    assert res.domain == "hansard"
    assert res.records_transformed == 2
    assert res.parquet_path.is_file()

    # Read back and check Arrow schema
    table = pq.read_table(res.parquet_path)
    assert table.schema == SILVER_ARROW_SCHEMA
    assert table.num_rows == 2
    pydict = table.to_pydict()
    assert len(pydict["nz_canonical_urn"]) == 2
