"""Unit tests for semantic search and DCAT-AP knowledge graph generation."""

from archive_govt_nz.semantic_search import (
    SemanticKnowledgeSearchIndex,
    _cosine_similarity,
    _generate_dense_vector,
    build_dcat_ap_knowledge_graph,
    extract_semantic_documents,
)


def test_extract_semantic_documents_and_vector_generation() -> None:
    """Validate extraction of titles, tags, formats and dense vector projection."""
    scope_manifest = {
        "datasets": [
            {
                "id": "ds-health-01",
                "title": "Hospital Admissions and Emergency Wait Times",
                "notes": "Quarterly public hospital statistical releases.",
                "organization": {"title": "Health New Zealand"},
                "tags": [{"name": "health"}, "public-health", 123],
                "resources": [{"format": "CSV"}, {"format": "JSON"}],
            },
            {
                "id": "ds-transport-01",
                "title": "State Highway Traffic Volumes",
                "notes": "Annual traffic monitoring data across regions.",
                "organization": "NZ Transport Agency",
                "tags": ["roads", "infrastructure"],
                "resources": [{"format": "GeoJSON"}],
            },
        ]
    }

    docs = extract_semantic_documents(scope_manifest)
    assert len(docs) == 2
    assert docs[0].dataset_id == "ds-health-01"
    assert docs[0].organization == "Health New Zealand"
    assert "health" in docs[0].tags
    assert "public-health" in docs[0].tags
    assert docs[0].formats == ("CSV", "JSON")
    assert len(docs[0].vector) == 64

    # Dense vectors should have unit norm
    norm = sum(x * x for x in docs[0].vector) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_dense_vector_edge_cases() -> None:
    """Validate empty tokens and cosine similarity safety."""
    empty_vec = _generate_dense_vector([])
    assert empty_vec == tuple([0.0] * 64)

    sim_mismatch = _cosine_similarity((1.0, 0.0), (1.0, 0.0, 0.0))
    assert sim_mismatch == 0.0

    sim_empty = _cosine_similarity((), ())
    assert sim_empty == 0.0


def test_build_dcat_ap_knowledge_graph() -> None:
    """Validate DCAT-AP 3.0 JSON-LD ontology structure."""
    scope_manifest = {
        "datasets": [
            {
                "id": "ds-001",
                "title": "Treasury Financial Statements",
                "notes": "Crown accounts and economic forecasts.",
                "organization": {"title": "The Treasury"},
                "tags": [{"name": "finance"}, {"name": "budget"}],
                "resources": [{"format": "CSV"}],
            }
        ]
    }

    graph = build_dcat_ap_knowledge_graph(scope_manifest)
    assert graph["@type"] == "dcat:Catalog"
    assert graph["@context"]["dcat"] == "http://www.w3.org/ns/dcat#"
    assert len(graph["dcat:dataset"]) == 1
    ds = graph["dcat:dataset"][0]
    assert ds["@type"] == "dcat:Dataset"
    assert ds["dct:title"] == "Treasury Financial Statements"
    assert ds["dct:publisher"]["foaf:name"] == "The Treasury"


def test_semantic_knowledge_search_hybrid_query() -> None:
    """Validate hybrid lexical BM25 and vector cosine similarity search."""
    scope_manifest = {
        "datasets": [
            {
                "id": "ds-climate-01",
                "title": "National Greenhouse Gas Inventory",
                "notes": "Annual emissions reporting across key sectors.",
                "organization": {"title": "Ministry for the Environment"},
                "tags": [{"name": "climate"}, {"name": "emissions"}],
                "resources": [{"format": "CSV"}],
            },
            {
                "id": "ds-marine-01",
                "title": "Coastal Marine Water Quality",
                "notes": "Monitoring data for coastal and estuarine water.",
                "organization": {"title": "Ministry for the Environment"},
                "tags": [{"name": "water"}, {"name": "marine"}],
                "resources": [{"format": "GEOJSON"}],
            },
        ]
    }

    docs = extract_semantic_documents(scope_manifest)
    index = SemanticKnowledgeSearchIndex(docs)
    assert index.document_count == 2

    # Query for emissions
    results = index.search("emissions greenhouse gas", top_k=5)
    assert len(results) >= 1
    assert results[0].dataset_id == "ds-climate-01"
    assert results[0].score > 0.0

    # Empty query should return empty
    empty_results = index.search("   ")
    assert empty_results == []

    # Unmatched query
    unmatched = index.search("xyznonexistentterm123")
    assert isinstance(unmatched, list)

    # Format filtering
    csv_results = index.search("environment", format_filter="CSV")
    assert all("CSV" in r.formats for r in csv_results)
