"""Gold Layer analytics, search, and CLI tests for Medico-Legal case law corpus."""

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


def _create_sample_medilegal_parquet(parquet_path: Path) -> None:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    cid_a = "bafybeia" + "a" * 51
    cases = [
        {
            "nz_canonical_urn": CanonicalURN.format(
                "medilegal", "decision", "HDC-21HDC01234"
            ),
            "nz_source_record_id": "HDC-21HDC01234",
            "nz_acquisition_id": "batch-medilegal-001",
            "nz_content_id": "a" * 64,
            "nz_content_cidv1": cid_a,
            "nz_observed_at": "2026-08-24T12:00:00Z",
            "nz_schema_fingerprint": "f" * 64,
            "domain": "medilegal",
            "entity_type": "medico_legal:decision:hdc",
            "canonical_uri": "nzml:decision/HDC-21HDC01234",
            "title": "Breach of Right 4(1) under HDC Code of Rights",
            "body_text": (
                "Finding of professional breach regarding prescription error "
                "under Medicines Act 1981."
            ),
            "body_format": "text",
            "valid_from": "2023-05-12",
            "valid_to": None,
            "source_observed_at": "2026-08-24T12:00:00Z",
            "is_current": True,
            "source_url": "https://www.hdc.org.nz/decisions/21HDC01234",
            "cas_path": "data/cas/m1",
            "sha256_payload": "a" * 64,
            "blake3_payload": "b" * 64,
            "byte_size": 95,
            "metadata_json": json.dumps(
                {
                    "case_id": "HDC-21HDC01234",
                    "tribunal": "HDC",
                    "statutory_provisions": ["Medicines Act 1981"],
                }
            ),
        },
    ]

    pydict: dict[str, list[object]] = {
        name: [c[name] for c in cases] for name in SILVER_ARROW_SCHEMA.names
    }
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, parquet_path, compression="zstd")


def test_gold_duckdb_medilegal_analytics(tmp_path: Path) -> None:
    """Gold analytics engine queries Medico-Legal dataset via DuckDB."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "medilegal" / "corpus.parquet"
    _create_sample_medilegal_parquet(parquet_path)

    engine = GoldAnalyticsEngine(silver_base_dir=silver_dir)
    try:
        res = engine.query(
            "SELECT title, domain, entity_type FROM silver_medilegal "
            "WHERE domain = 'medilegal'"
        )
        assert res.row_count == 1
        rows = res.to_pylist()
        assert "HDC Code of Rights" in rows[0]["title"]
        assert rows[0]["entity_type"] == "medico_legal:decision:hdc"
    finally:
        engine.close()


def test_gold_search_medilegal_indexing(tmp_path: Path) -> None:
    """Gold hybrid search retrieves indexed Medico-Legal decisions."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "medilegal" / "corpus.parquet"
    _create_sample_medilegal_parquet(parquet_path)

    search_engine = GoldHybridSearchEngine()
    count = search_engine.index_parquet_corpus(parquet_path)
    assert count == 1

    results = search_engine.search(
        "prescription error Medicines Act", domain_filter="medilegal", limit=5
    )
    assert len(results) >= 1
    assert "HDC-21HDC01234" in results[0].canonical_uri


def test_cli_query_medilegal_integration(tmp_path: Path) -> None:
    """CLI query command runs SQL against Medico-Legal dataset."""
    silver_dir = tmp_path / "silver"
    parquet_path = silver_dir / "medilegal" / "corpus.parquet"
    _create_sample_medilegal_parquet(parquet_path)

    code = query_command(
        sql="SELECT nz_canonical_urn, title FROM silver_medilegal",
        silver_dir=silver_dir,
        format="json",
    )
    assert code == 0
