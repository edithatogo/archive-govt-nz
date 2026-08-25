"""Tests for GoldKnowledgeGraphIngestor and reverse knowledge graph feed-back views."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.gold.analytics import (
    GoldAnalyticsEngine,
    GoldKnowledgeGraphIngestor,
)


def test_gold_knowledge_graph_ingestor(tmp_path: Path) -> None:
    """Test mounting downstream NLP extraction tables into Gold analytical views."""
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()
    extractions_dir = tmp_path / "extractions"
    extractions_dir.mkdir()

    # Create dummy silver gazette table
    gazette_dir = silver_dir / "gazette"
    gazette_dir.mkdir()
    silver_table = pa.Table.from_pylist(
        [
            {
                "nz_canonical_urn": "urn:nz:gazette:2026:au1001",
                "nz_source_record_id": "2026-au1001",
                "title": "Consent to Distribution of Medicine",
                "domain": "gazette",
                "source_observed_at": "2026-08-26T00:00:00Z",
                "text_content": "Notice under section 24 of Medicines Act 1981",
            }
        ]
    )
    pq.write_table(silver_table, gazette_dir / "corpus.parquet")

    # Create dummy extraction Parquet table
    extractions_file = extractions_dir / "gazette_extracted.parquet"
    ext_table = pa.Table.from_pylist(
        [
            {
                "record_id": "2026-au1001",
                "title": "Consent to Distribution of Medicine",
                "category": "health",
                "publication_date": "2026-08-26",
                "citations_json": json.dumps(
                    [
                        {
                            "act_or_regulation": "Medicines Act 1981",
                            "section": "24",
                            "raw_citation": "section 24 of Medicines Act 1981",
                        }
                    ]
                ),
                "entities_json": json.dumps(
                    [
                        {
                            "name": "ACME Pharmaceuticals",
                            "entity_type": "ORGANIZATION",
                            "registration_number": "1234567",
                            "start_offset": 10,
                            "end_offset": 30,
                        }
                    ]
                ),
                "source_urn": "urn:nz:gazette:2026:au1001",
                "content_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            }
        ]
    )
    pq.write_table(ext_table, extractions_file)

    with GoldAnalyticsEngine(silver_base_dir=silver_dir) as engine:
        GoldKnowledgeGraphIngestor.attach_nlp_extractions(engine, extractions_file)

        # Query extracted entities
        res_entities = engine.query(
            "SELECT record_id, category, source_urn FROM v_gold_extracted_entities"
        )
        assert res_entities.row_count == 1
        assert res_entities.to_pylist()[0]["record_id"] == "2026-au1001"
        assert res_entities.to_pylist()[0]["category"] == "health"

        # Query statutory graph
        res_statutory = engine.query(
            "SELECT record_id, title FROM v_gold_statutory_graph"
        )
        assert res_statutory.row_count == 1

        # Joined cross-view query
        joined_res = engine.query(
            """
            SELECT g.nz_canonical_urn, e.category, g.title
            FROM silver_gazette g
            JOIN v_gold_extracted_entities e
              ON g.nz_source_record_id = e.record_id
            """
        )
        assert joined_res.row_count == 1
        assert joined_res.to_pylist()[0]["category"] == "health"
