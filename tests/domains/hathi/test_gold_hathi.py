"""Gold Layer analytics, search, and CLI tests for HathiTrust NZ corpus."""

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


def _create_sample_hathi_parquet(parquet_path: Path) -> None:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    cid_a = "bafybeia" + "a" * 51
    pages = [
        {
            "nz_canonical_urn": CanonicalURN.format(
                "hathi", "page", "hvd.32044012345678_p0001"
            ),
            "nz_source_record_id": "hvd.32044012345678_p0001",
            "nz_acquisition_id": "batch-hathi-001",
            "nz_content_id": "a" * 64,
            "nz_content_cidv1": cid_a,
            "nz_observed_at": "2026-08-24T12:00:00Z",
            "nz_schema_fingerprint": "f" * 64,
            "domain": "hathi",
            "entity_type": "historical_publication:page",
            "canonical_uri": "nzhathi:volume/hvd.32044012345678#p=1",
            "title": "HathiTrust NZ: AJHR 1890 (Page 1)",
            "body_text": "Report under Public Revenues Act 1882 presented.",
            "body_format": "text",
            "valid_from": "1890-01-01",
            "valid_to": None,
            "source_observed_at": "2026-08-24T12:00:00Z",
            "is_current": True,
            "source_url": "https://babel.hathitrust.org/record/001",
            "cas_path": "data/cas/h1",
            "sha256_payload": "a" * 64,
            "blake3_payload": "b" * 64,
            "byte_size": 66,
            "metadata_json": json.dumps(
                {
                    "publication_year": 1890,
                    "rights_status": "crown_copyright_expired",
                    "act_references": ["Public Revenues Act 1882"],
                }
            ),
        },
    ]

    pydict: dict[str, list[object]] = {
        name: [s[name] for s in pages] for name in SILVER_ARROW_SCHEMA.names
    }
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, parquet_path)


def test_gold_duckdb_hathi_analytics(tmp_path: Path) -> None:
    """Gold analytics engine queries HathiTrust historic corpus."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "hathi" / "corpus.parquet"
    _create_sample_hathi_parquet(parquet_path)

    engine = GoldAnalyticsEngine(silver_base_dir=silver_dir)
    try:
        res = engine.query("SELECT count(*) as total FROM silver_hathi")
        assert res.row_count == 1
        rows = res.to_pylist()
        assert rows[0]["total"] == 1
    finally:
        engine.close()


def test_gold_search_hathi_indexing(tmp_path: Path) -> None:
    """Gold hybrid search retrieves historical HathiTrust pages."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "hathi" / "corpus.parquet"
    _create_sample_hathi_parquet(parquet_path)

    search_engine = GoldHybridSearchEngine()
    count = search_engine.index_parquet_corpus(parquet_path)
    assert count == 1

    results = search_engine.search(
        "Public Revenues Act", limit=5, domain_filter="hathi"
    )
    assert len(results) >= 1
    assert "AJHR 1890" in results[0].title


def test_cli_query_hathi_integration(tmp_path: Path) -> None:
    """CLI query command runs SQL against HathiTrust dataset."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "hathi" / "corpus.parquet"
    _create_sample_hathi_parquet(parquet_path)

    code = query_command(
        sql="SELECT * FROM silver_hathi",
        silver_dir=silver_dir,
        format="json",
    )
    assert code == 0
