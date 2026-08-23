"""Tests for the Gold embedded hybrid vector and lexical search engine."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.gold.search import (
    GoldHybridSearchEngine,
    compute_deterministic_embedding,
    cosine_similarity,
)
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA, NormalizedSilverRecord


def test_deterministic_embedding_and_similarity() -> None:
    vec1 = compute_deterministic_embedding("Public Records Act 2005")
    vec2 = compute_deterministic_embedding("Public Records Act 2005")
    vec3 = compute_deterministic_embedding("Ministry of Health COVID daily summary")

    assert len(vec1) == 64
    assert cosine_similarity(vec1, vec2) > 0.99
    assert cosine_similarity(vec1, vec3) < cosine_similarity(vec1, vec2)


def test_gold_hybrid_search_engine_indexing_and_retrieval(tmp_path: Path) -> None:
    parquet_path = tmp_path / "corpus.parquet"

    # Create dummy multi-domain dataset
    recs = [
        NormalizedSilverRecord(
            nz_source_record_id="rec-001",
            nz_acquisition_id="b-001",
            nz_content_id="c-001",
            nz_observed_at="2026-08-23T00:00:00Z",
            nz_schema_fingerprint="fp-001",
            domain="legislation",
            entity_type="act",
            canonical_uri="nzlc:act/2005-0123",
            title="Public Records Act 2005",
            body_text="An Act to provide for the custody and preservation of public records in New Zealand.",
            body_format="text",
            valid_from="2005-04-21",
            valid_to=None,
            source_observed_at="2026-08-23T00:00:00Z",
            is_current=True,
            source_url="https://legislation.govt.nz/act/2005/0123",
            cas_path="cas/sha256/11",
            sha256_payload="1111",
            blake3_payload="2222",
            byte_size=1000,
        ),
        NormalizedSilverRecord(
            nz_source_record_id="rec-002",
            nz_acquisition_id="b-002",
            nz_content_id="c-002",
            nz_observed_at="2026-08-23T00:00:00Z",
            nz_schema_fingerprint="fp-002",
            domain="gazette",
            entity_type="gazette_notice",
            canonical_uri="nzgazette:notice/2026-001",
            title="Disposal Authority Notice for Health Records",
            body_text="Notice regarding authorization for disposal of legacy health clinic records.",
            body_format="text",
            valid_from="2026-01-15",
            valid_to=None,
            source_observed_at="2026-08-23T00:00:00Z",
            is_current=True,
            source_url="https://gazette.govt.nz/notice/2026-001",
            cas_path="cas/sha256/33",
            sha256_payload="3333",
            blake3_payload="4444",
            byte_size=800,
        ),
    ]

    pydict = {
        field.name: [r.to_dict()[field.name] for r in recs]
        for field in SILVER_ARROW_SCHEMA
    }
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, parquet_path)

    engine = GoldHybridSearchEngine()
    indexed = engine.index_parquet_corpus(parquet_path)
    assert indexed == 2

    # Query for "Public Records"
    results = engine.search("Public Records", limit=5)
    assert len(results) == 2
    assert results[0].canonical_uri == "nzlc:act/2005-0123"
    assert results[0].score > 0.0

    # Query with domain filter
    gaz_results = engine.search("records", domain_filter="gazette")
    assert len(gaz_results) == 1
    assert gaz_results[0].domain == "gazette"
