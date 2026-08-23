"""Silver Cross-Domain Interlinking Engine and Relational Lineage Graph.

Extracts bidirectional references and citation links across New Zealand statutory
instruments, Gazette notices, Courts notices, Health/COVID datasets, and CKAN packages,
exporting typed relational graph manifests and Parquet tables.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

INTERLINK_SCHEMA = "archive-govt-nz.identifier-interlink/v1"

# Known statutory and notice reference patterns
ACT_CITATION_REGEX = re.compile(r"([A-Z][A-Za-z0-9\s,-]+Act\s+(?:18|19|20)\d{2})")
GAZETTE_CITATION_REGEX = re.compile(
    r"Gazette,\s*(?:18|19|20)\d{2},\s*(?:p\s*\d+|Notice\s*\d+)"
)
COURT_CASE_REGEX = re.compile(r"\[(18|19|20)\d{2}\]\s*NZ(HC|CA|SC|DC|EnvC|EmpC)\s*\d+")


@dataclass(frozen=True, slots=True)
class RelationalEdge:
    """A directed semantic or provenance edge between two archival entities."""

    source_uri: str
    target_uri: str
    relation_type: (
        str  # e.g., "cites", "amends", "notifies", "authorizes", "derived_from"
    )
    confidence: float
    observed_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_uri": self.source_uri,
            "target_uri": self.target_uri,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "observed_at": self.observed_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class EntityNode:
    """A canonical entity node in the Silver relational graph."""

    canonical_uri: str
    domain: str
    entity_type: str
    title: str
    observed_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "canonical_uri": self.canonical_uri,
            "domain": self.domain,
            "entity_type": self.entity_type,
            "title": self.title,
            "observed_at": self.observed_at,
            "metadata": dict(self.metadata),
        }


class CrossDomainInterlinkGraph:
    """Cross-domain graph engine for statutory, notice, and dataset relationships."""

    def __init__(self) -> None:
        """Initialize empty nodes registry and edge adjacency mappings."""
        self.nodes: dict[str, EntityNode] = {}
        self.edges: list[RelationalEdge] = []
        self._adjacency: dict[str, list[RelationalEdge]] = {}

    def add_node(
        self,
        *,
        canonical_uri: str,
        domain: str,
        entity_type: str,
        title: str,
        observed_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EntityNode:
        """Register a node in the graph."""
        timestamp = observed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        node = EntityNode(
            canonical_uri=canonical_uri,
            domain=domain,
            entity_type=entity_type,
            title=title,
            observed_at=timestamp,
            metadata=metadata or {},
        )
        self.nodes[canonical_uri] = node
        return node

    def add_edge(
        self,
        *,
        source_uri: str,
        target_uri: str,
        relation_type: str,
        confidence: float = 1.0,
        observed_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RelationalEdge:
        """Create a directed relation between two registered or external URIs."""
        timestamp = observed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        edge = RelationalEdge(
            source_uri=source_uri,
            target_uri=target_uri,
            relation_type=relation_type,
            confidence=confidence,
            observed_at=timestamp,
            metadata=metadata or {},
        )
        self.edges.append(edge)
        self._adjacency.setdefault(source_uri, []).append(edge)
        return edge

    def resolve_outgoing(self, uri: str) -> list[RelationalEdge]:
        """Return all outgoing relation edges from a source URI."""
        return self._adjacency.get(uri, [])

    def resolve_incoming(self, uri: str) -> list[RelationalEdge]:
        """Return all incoming relation edges targeting a URI."""
        return [e for e in self.edges if e.target_uri == uri]

    def extract_and_link_text(
        self,
        source_uri: str,
        text_content: str,
        observed_at: str | None = None,
    ) -> list[RelationalEdge]:
        """Heuristically extract citations from free-text and link to entities."""
        discovered: list[RelationalEdge] = []
        timestamp = observed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Extract Act references
        for match in ACT_CITATION_REGEX.finditer(text_content):
            act_title = match.group(1).strip()
            target_uri = (
                f"nzlc:act/{hashlib.sha256(act_title.encode('utf-8')).hexdigest()[:12]}"
            )
            edge = self.add_edge(
                source_uri=source_uri,
                target_uri=target_uri,
                relation_type="cites_act",
                confidence=0.90,
                observed_at=timestamp,
                metadata={"matched_text": act_title},
            )
            discovered.append(edge)

        # Extract Court Case citations
        for match in COURT_CASE_REGEX.finditer(text_content):
            case_cite = match.group(0).strip()
            target_uri = f"nzcourt:case/{hashlib.sha256(case_cite.encode('utf-8')).hexdigest()[:12]}"
            edge = self.add_edge(
                source_uri=source_uri,
                target_uri=target_uri,
                relation_type="cites_case",
                confidence=0.95,
                observed_at=timestamp,
                metadata={"case_citation": case_cite},
            )
            discovered.append(edge)

        return discovered

    def detect_cycles(self, relation_types: set[str] | None = None) -> list[list[str]]:
        """Check for hierarchical cycles (e.g. A amends B amends A)."""
        visited: set[str] = set()
        path: list[str] = []
        cycles: list[list[str]] = []

        def dfs(u: str) -> None:
            visited.add(u)
            path.append(u)
            for edge in self._adjacency.get(u, []):
                if relation_types and edge.relation_type not in relation_types:
                    continue
                v = edge.target_uri
                if v in path:
                    cycle_start = path.index(v)
                    cycles.append([*path[cycle_start:], v])
                elif v not in visited:
                    dfs(v)
            path.pop()

        for node in list(self.nodes.keys()):
            if node not in visited:
                dfs(node)

        return cycles

    def export_lineage_manifest(self) -> dict[str, Any]:
        """Export standardized OpenLineage and interlink manifest."""
        return {
            "schema_version": INTERLINK_SCHEMA,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "nodes_count": len(self.nodes),
            "edges_count": len(self.edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }
