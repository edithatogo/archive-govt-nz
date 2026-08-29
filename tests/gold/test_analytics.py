"""Tests for the Gold DuckDB analytical engine, cross-domain views, and DCAT-AP exporter."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.gold.analytics import (
    GoldAnalyticsEngine,
    GoldKnowledgeGraphIngestor,
)
from archive_govt_nz.gold.dcat import DCATAPMetadataExporter
from archive_govt_nz.gold.federation import FederationManager
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA, NormalizedSilverRecord


def test_gold_duckdb_analytics_and_views(tmp_path: Path) -> None:
    silver_dir = tmp_path / "silver"
    leg_dir = silver_dir / "legislation"
    leg_dir.mkdir(parents=True)

    # Create dummy silver parquet
    rec = NormalizedSilverRecord(
        nz_source_record_id="act-001",
        nz_acquisition_id="batch-001",
        nz_content_id="content-001",
        nz_observed_at="2026-08-23T00:00:00Z",
        nz_schema_fingerprint="fp-001",
        domain="legislation",
        entity_type="act",
        canonical_uri="nzlc:act/001",
        title="Public Records Act 2005",
        body_text="An Act to provide for the custody and preservation of public records.",
        body_format="text",
        valid_from="2005-04-21",
        valid_to=None,
        source_observed_at="2026-08-23T00:00:00Z",
        is_current=True,
        source_url="https://legislation.govt.nz/act/2005/001",
        cas_path="cas/sha256/11",
        sha256_payload="1111",
        blake3_payload="2222",
        byte_size=1234,
        metadata_json='{"category": "governance"}',
    )
    pydict = {field.name: [rec.to_dict()[field.name]] for field in SILVER_ARROW_SCHEMA}
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, leg_dir / "corpus.parquet")

    engine = GoldAnalyticsEngine(silver_base_dir=silver_dir)

    # Query specific view
    res = engine.query(
        "SELECT title, domain FROM silver_legislation WHERE domain = 'legislation'"
    )
    assert res.row_count == 1
    assert res.to_pylist()[0]["title"] == "Public Records Act 2005"

    # Query unified view
    res_union = engine.query("SELECT COUNT(*) AS total FROM v_gold_all_entities")
    assert res_union.to_pylist()[0]["total"] == 1

    engine.close()


def test_gold_federation_partner_hook(tmp_path: Path) -> None:
    engine = GoldAnalyticsEngine(silver_base_dir=tmp_path / "empty_silver")

    # Create mock federated parquet table (e.g. GMA table)
    fed_path = tmp_path / "gma_medicines.parquet"
    gma_table = pa.Table.from_pydict(
        {
            "gma_medicine_id": ["MED-001", "MED-002"],
            "substance_name": ["Paracetamol", "Amoxicillin"],
            "nz_approved": [True, True],
        }
    )
    pq.write_table(gma_table, fed_path)

    # Register federated partner
    engine.register_federation_partner("global-medicines-atlas", fed_path)

    res = engine.query(
        "SELECT substance_name FROM fed_global_medicines_atlas WHERE nz_approved = true"
    )
    assert res.row_count == 2
    assert [row["substance_name"] for row in res.to_pylist()] == [
        "Paracetamol",
        "Amoxicillin",
    ]

    engine.close()


def test_dcat_ap_and_ro_crate_exporter() -> None:
    exporter = DCATAPMetadataExporter(publisher_name="Test Publisher")
    datasets = [
        {
            "domain": "legislation",
            "title": "NZ Legislation Corpus",
            "parquet_url": "data/silver/legislation/corpus.parquet",
        }
    ]

    catalog = exporter.export_dcat_ap_catalog(datasets)
    assert catalog["@type"] == "dcat:Catalog"
    assert len(catalog["dcat:dataset"]) == 1
    assert catalog["dcat:dataset"][0]["dct:identifier"] == "nz-archive-legislation"

    crate = exporter.export_ro_crate_manifest(
        "NZ Legislation Dataset", [{"path": "corpus.parquet", "sha256": "abc"}]
    )
    assert "@graph" in crate
    assert len(crate["@graph"]) == 3


def test_federation_manager_named_partners(tmp_path: Path) -> None:
    """FederationManager named attach helpers register partner datasets."""
    engine = GoldAnalyticsEngine(silver_base_dir=tmp_path / "empty_silver")
    fed_path = tmp_path / "partner.parquet"
    pq.write_table(
        pa.Table.from_pydict({"nz_canonical_urn": ["urn:x"], "value": [1]}),
        fed_path,
    )

    manager = FederationManager(engine)
    manager.attach_global_medicines_atlas(fed_path)
    manager.attach_fyi_archive(fed_path)


def test_register_domain_table_updates_view(tmp_path: Path) -> None:
    """Explicit domain table registration creates a queryable silver view."""
    engine = GoldAnalyticsEngine(silver_base_dir=tmp_path / "silver")

    rec_path = tmp_path / "corpus.parquet"
    pq.write_table(pa.Table.from_pydict({"urn": ["u1"]}), rec_path)
    engine.register_domain_table("health", rec_path)

    result = engine.query("SELECT COUNT(*) AS n FROM silver_health")
    assert result.row_count == 1


def test_query_returns_empty_result_on_none_relation(tmp_path: Path) -> None:
    """query() returns an empty columnar result when the relation is None."""
    engine = GoldAnalyticsEngine(silver_base_dir=tmp_path)
    # A DDL statement yields a None relation from DuckDB, exercising the
    # empty-result branch of query().
    result = engine.query("CREATE OR REPLACE TEMP TABLE patch_probe AS SELECT 1 AS v")
    assert result.row_count == 0
    assert result.column_names == []


def test_attach_nlp_extractions_missing_path_is_noop(tmp_path: Path) -> None:
    """attach_nlp_extractions returns early when the extractions path is absent."""
    engine = GoldAnalyticsEngine(silver_base_dir=tmp_path)
    GoldKnowledgeGraphIngestor.attach_nlp_extractions(
        engine, tmp_path / "missing.parquet"
    )
