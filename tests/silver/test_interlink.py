"""Tests for the Silver cross-domain interlink graph, citation parser, and lineage manifest."""

from archive_govt_nz.silver.interlink import INTERLINK_SCHEMA, CrossDomainInterlinkGraph


def test_interlink_graph_nodes_and_edges() -> None:
    graph = CrossDomainInterlinkGraph()

    # Add Legislation node
    leg_node = graph.add_node(
        canonical_uri="nzlc:act/DLM123",
        domain="legislation",
        entity_type="act",
        title="Public Records Act 2005",
    )

    # Add Gazette Notice node
    gaz_node = graph.add_node(
        canonical_uri="nzgazette:notice/2026-0456",
        domain="gazette",
        entity_type="gazette_notice",
        title="Disposal Authority Notice",
    )

    # Connect edge
    edge = graph.add_edge(
        source_uri=gaz_node.canonical_uri,
        target_uri=leg_node.canonical_uri,
        relation_type="authorizes",
        confidence=1.0,
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.resolve_outgoing(gaz_node.canonical_uri) == [edge]
    assert graph.resolve_incoming(leg_node.canonical_uri) == [edge]


def test_interlink_text_citation_extraction() -> None:
    graph = CrossDomainInterlinkGraph()
    text = (
        "Pursuant to the Public Records Act 2005 and following [2024] NZHC 1234, "
        "the Chief Archivist issues this directive under the Official Information Act 1982."
    )

    discovered = graph.extract_and_link_text(
        source_uri="nzgazette:notice/2026-0999",
        text_content=text,
    )

    assert len(discovered) >= 2
    relation_types = {e.relation_type for e in discovered}
    assert "cites_act" in relation_types
    assert "cites_case" in relation_types


def test_interlink_cycle_detection() -> None:
    graph = CrossDomainInterlinkGraph()
    graph.add_node(
        canonical_uri="uri:A", domain="leg", entity_type="act", title="Act A"
    )
    graph.add_node(
        canonical_uri="uri:B", domain="leg", entity_type="act", title="Act B"
    )
    graph.add_node(
        canonical_uri="uri:C", domain="leg", entity_type="act", title="Act C"
    )

    # Create cycle: A -> B -> C -> A
    graph.add_edge(source_uri="uri:A", target_uri="uri:B", relation_type="amends")
    graph.add_edge(source_uri="uri:B", target_uri="uri:C", relation_type="amends")
    graph.add_edge(source_uri="uri:C", target_uri="uri:A", relation_type="amends")

    cycles = graph.detect_cycles(relation_types={"amends"})
    assert len(cycles) > 0
    assert "uri:A" in cycles[0]


def test_export_lineage_manifest() -> None:
    graph = CrossDomainInterlinkGraph()
    graph.add_node(
        canonical_uri="nzlc:act/1",
        domain="legislation",
        entity_type="act",
        title="Act 1",
    )
    graph.add_node(
        canonical_uri="nzhealth:data/1",
        domain="health",
        entity_type="data",
        title="Health 1",
    )
    graph.add_edge(
        source_uri="nzhealth:data/1",
        target_uri="nzlc:act/1",
        relation_type="authorized_by",
    )

    manifest = graph.export_lineage_manifest()
    assert manifest["schema_version"] == INTERLINK_SCHEMA
    assert manifest["nodes_count"] == 2
    assert manifest["edges_count"] == 1
    assert len(manifest["nodes"]) == 2
    assert len(manifest["edges"]) == 1
