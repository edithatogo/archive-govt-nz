"""Gold Layer analytics, search, and CLI integration tests for Hansard corpus."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.cli import query_command
from archive_govt_nz.core.urn import CanonicalURN
from archive_govt_nz.gold.analytics import GoldAnalyticsEngine
from archive_govt_nz.gold.search import GoldHybridSearchEngine
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA

if TYPE_CHECKING:
    from pathlib import Path


def _create_sample_hansard_parquet(parquet_path: Path) -> None:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    cid_a = "bafybeia" + "a" * 51
    cid_b = "bafybeib" + "b" * 51
    speeches = [
        {
            "nz_canonical_urn": CanonicalURN.format(
                "hansard", "speech", "HANSARD-01_SPCH-001"
            ),
            "nz_source_record_id": "HANSARD-01_SPCH-001",
            "nz_acquisition_id": "batch-h-001",
            "nz_content_id": "a" * 64,
            "nz_content_cidv1": cid_a,
            "nz_observed_at": "2026-08-20T14:00:00Z",
            "nz_schema_fingerprint": "f" * 64,
            "domain": "hansard",
            "entity_type": "parliamentary_speech:question",
            "canonical_uri": "nzhansard:speech/HANSARD-01_SPCH-001",
            "title": "Hansard: Hon Dr Ayesha Verrall on Health Funding",
            "body_text": "Will the Minister support the Pae Ora Act and fund it?",
            "body_format": "text",
            "valid_from": "2026-08-20",
            "valid_to": None,
            "source_observed_at": "2026-08-20T14:00:00Z",
            "is_current": True,
            "source_url": "https://www.parliament.nz/hansard/01",
            "cas_path": "data/cas/h1",
            "sha256_payload": "a" * 64,
            "blake3_payload": "b" * 64,
            "byte_size": 85,
            "metadata_json": json.dumps(
                {
                    "speaker_name": "Hon Dr Ayesha Verrall",
                    "act_references": ["Pae Ora Act"],
                }
            ),
        },
        {
            "nz_canonical_urn": CanonicalURN.format(
                "hansard", "speech", "HANSARD-01_SPCH-002"
            ),
            "nz_source_record_id": "HANSARD-01_SPCH-002",
            "nz_acquisition_id": "batch-h-001",
            "nz_content_id": "c" * 64,
            "nz_content_cidv1": cid_b,
            "nz_observed_at": "2026-08-20T14:02:00Z",
            "nz_schema_fingerprint": "f" * 64,
            "domain": "hansard",
            "entity_type": "parliamentary_speech:answer",
            "canonical_uri": "nzhansard:speech/HANSARD-01_SPCH-002",
            "title": "Hansard: Hon Dr Shane Reti on Health Delivery",
            "body_text": "Delivering services under the Public Finance Act.",
            "body_format": "text",
            "valid_from": "2026-08-20",
            "valid_to": None,
            "source_observed_at": "2026-08-20T14:02:00Z",
            "is_current": True,
            "source_url": "https://www.parliament.nz/hansard/02",
            "cas_path": "data/cas/h2",
            "sha256_payload": "c" * 64,
            "blake3_payload": "d" * 64,
            "byte_size": 81,
            "metadata_json": json.dumps(
                {
                    "speaker_name": "Hon Dr Shane Reti",
                    "act_references": ["Public Finance Act"],
                }
            ),
        },
    ]

    pydict: dict[str, list[object]] = {
        name: [s[name] for s in speeches] for name in SILVER_ARROW_SCHEMA.names
    }
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, parquet_path)


def test_gold_duckdb_hansard_analytics(tmp_path: Path) -> None:
    """Gold analytics engine registers and runs queries on Hansard corpus."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "hansard" / "corpus.parquet"
    _create_sample_hansard_parquet(parquet_path)

    engine = GoldAnalyticsEngine(silver_base_dir=silver_dir)
    try:
        sql = (
            "SELECT entity_type, count(*) as count "
            "FROM silver_hansard "
            "GROUP BY entity_type "
            "ORDER BY entity_type"
        )
        res = engine.query(sql)
        assert res.row_count == 2
        rows = res.to_pylist()
        assert rows[0]["entity_type"] == "parliamentary_speech:answer"
        assert rows[0]["count"] == 1
        assert rows[1]["entity_type"] == "parliamentary_speech:question"
        assert rows[1]["count"] == 1
    finally:
        engine.close()


def test_gold_search_hansard_indexing(tmp_path: Path) -> None:
    """Gold hybrid search indexes Hansard corpus and performs semantic retrieval."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "hansard" / "corpus.parquet"
    _create_sample_hansard_parquet(parquet_path)

    search_engine = GoldHybridSearchEngine()
    indexed_count = search_engine.index_parquet_corpus(parquet_path)
    assert indexed_count == 2

    results = search_engine.search(
        "Health Funding Pae Ora", limit=5, domain_filter="hansard"
    )
    assert len(results) >= 1
    assert "Ayesha Verrall" in results[0].title


def test_cli_query_hansard_integration(tmp_path: Path) -> None:
    """CLI query command runs SQL and semantic queries against Hansard corpus."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "hansard" / "corpus.parquet"
    _create_sample_hansard_parquet(parquet_path)

    exit_code_sql = query_command(
        sql="SELECT count(*) as total FROM silver_hansard",
        silver_dir=silver_dir,
        format="json",
    )
    assert exit_code_sql == 0

    exit_code_search = query_command(
        semantic="Pae Ora",
        domain="hansard",
        silver_dir=silver_dir,
        format="json",
    )
    assert exit_code_search == 0
