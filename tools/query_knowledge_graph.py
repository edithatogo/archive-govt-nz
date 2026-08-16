"""CLI tool to query the national dataset knowledge graph."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.semantic_search import (
    SemanticKnowledgeSearchIndex,
    build_dcat_ap_knowledge_graph,
    extract_semantic_documents,
)


def main() -> int:
    """Read arguments and query or export the catalogue knowledge graph."""
    parser = argparse.ArgumentParser(
        description="Query the national dataset knowledge graph."
    )
    parser.add_argument(
        "--scope-manifest",
        type=Path,
        default=Path("evidence/global-ckan-scope.json"),
        help="Path to global CKAN scope manifest JSON",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Natural language or keyword search query",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        help="Filter by data format (e.g. CSV, GEOJSON, PARQUET)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum search results to return",
    )
    parser.add_argument(
        "--export-dcat-ap",
        type=Path,
        default=None,
        help="Path to export DCAT-AP 3.0 JSON-LD knowledge graph",
    )
    args = parser.parse_args()

    if not args.scope_manifest.is_file():
        print(f"ERROR: Scope manifest not found at: {args.scope_manifest}")
        return 1

    try:
        scope = json.loads(args.scope_manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: Failed to read scope manifest: {e}")
        return 1

    if args.export_dcat_ap:
        graph = build_dcat_ap_knowledge_graph(scope)
        args.export_dcat_ap.parent.mkdir(parents=True, exist_ok=True)
        args.export_dcat_ap.write_text(
            json.dumps(graph, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Exported DCAT-AP knowledge graph to: {args.export_dcat_ap}")
        if not args.query:
            return 0

    if not args.query:
        print("Specify --query to search or --export-dcat-ap to export graph.")
        return 0

    docs = extract_semantic_documents(scope)
    index = SemanticKnowledgeSearchIndex(docs)
    results = index.search(args.query, top_k=args.top_k, format_filter=args.format)

    print(
        f"\nSearch results for '{args.query}' "
        f"(indexed datasets: {index.document_count}):\n"
    )
    if not results:
        print("No matching datasets found.")
        return 0

    for i, r in enumerate(results, 1):
        formats_str = ", ".join(r.formats) if r.formats else "N/A"
        tags_str = ", ".join(r.matched_tags) if r.matched_tags else "none"
        print(f"{i}. [{r.score:.3f}] {r.title}")
        print(f"   Org     : {r.organization}")
        print(f"   Formats : {formats_str}")
        print(f"   Matched : {tags_str}")
        print(
            f"   Scores  : (lexical={r.lexical_score:.3f}, vector={r.vector_score:.3f})"
        )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
