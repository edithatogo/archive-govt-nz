# GitHub Issue Hierarchy & Cross-References

Target repository: `edithatogo/archive-govt-nz`
Federated alignment: `edithatogo/global-medicines-atlas`

---

## Parent Epic

**Track Epic: Medallion Architecture Consolidation with Integrated Vector & Knowledge Graph Products**
- **Track ID:** `medallion_architecture_consolidation_20260823`
- **Track Context:** [`conductor/tracks/medallion_architecture_consolidation_20260823/`](./index.md)

---

## Nested Phase Subissues

### 1. Phase 1: Bronze Ingestion Framework & Immutable Storage Standardization
- **Scope:** Formalize `data/bronze/` layout, CAS object storage (`sha256/`, `blake3/`), and WARC/WACZ bitstreams across all 6 domains.
- **Requirements:** MUST-1
- **Evidence Path:** `evidence/medallion/bronze-ingestion-receipt.json`

### 2. Phase 2: Silver Layer Parquet Pipelines & Cross-Domain Normalization
- **Scope:** Vectorized Polars/PyArrow extractors producing schema-conformed `data/silver/{domain}/corpus.parquet` and JSONL files.
- **Requirements:** MUST-2
- **Evidence Path:** `evidence/medallion/silver-transformation-receipt.json`

### 3. Phase 3: Silver Cross-Domain Interlinking & Relational Lineage Graph
- **Scope:** Build cross-domain entity joins (Legislation ↔ Gazette ↔ Health ↔ CKAN), provenance joins, and lineage graph.
- **Requirements:** MUST-3
- **Evidence Path:** `evidence/medallion/silver-interlink-receipt.json`

### 4. Phase 4: Gold Layer DuckDB Analytical Engine & DCAT-AP Knowledge Graph
- **Scope:** Embedded DuckDB analytical database views, cross-domain SQL joins, and W3C DCAT-AP 3.0 / Croissant / RO-Crate 1.1 JSON-LD export.
- **Requirements:** MUST-4, MUST-6
- **Evidence Path:** `evidence/medallion/gold-analytics-receipt.json`

### 5. Phase 5: Gold Layer Embedded LanceDB Hybrid Vector Search
- **Scope:** Embedded LanceDB hybrid search index generator derived directly from Silver Parquet, dense vector projection, and BM25 ranking.
- **Requirements:** MUST-5
- **Evidence Path:** `evidence/medallion/gold-search-receipt.json`

### 6. Phase 6: Unified CLI & MCP Query Surface
- **Scope:** Global CLI `archive-govt-nz query` (`--sql`, `--semantic`, `--graph`) and FastMCP server tools.
- **Requirements:** MUST-7
- **Evidence Path:** `evidence/medallion/cli-mcp-receipt.json`

### 7. Phase 7: Quality Gates, Mutation Testing & End-to-End Evidence
- **Scope:** Add mutation suite `mutation_medallion.py`, 100% patch coverage, >=95% branch coverage on Python 3.14, and end-to-end receipt.
- **Requirements:** SHOULD-1, SHOULD-2
- **Evidence Path:** `evidence/medallion/medallion-consolidation-receipt.json`
