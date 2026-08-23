# Requirements: Medallion Architecture Consolidation

- **Track ID:** `medallion_architecture_consolidation_20260823`
- **Methodology:** MoSCoW
- **Alignment:** 100% aligned with `global-medicines-atlas` architecture and Conductor workflow standards.

---

## 1. Functional Requirements

### 1.1 MUST Have
- **MUST-1 (Bronze Layer Standard):** Standardize all 6 domains (Legislation, Gazette, CKAN data.govt.nz, Health/MoH, Treasury, Feeds/Social) into an immutable Bronze capture tier using CAS (`sha256/` and `blake3/`), WARC/WACZ containers, and raw snapshot manifests.
- **MUST-2 (Silver Parquet Normalization):** Build vectorized Polars and PyArrow transformation pipelines generating schema-validated canonical Parquet files (`data/silver/{domain}/corpus.parquet`) with JSON schema conformance.
- **MUST-3 (Silver Relational Interlinking):** Unify cross-domain entity identifiers (Statutes ↔ Gazette Notices ↔ Health Datasets ↔ CKAN packages) into a relational linkage table with explicit confidence scoring and provenance joins.
- **MUST-4 (Gold DuckDB Analytical Engine):** Provide zero-copy, embedded DuckDB database views and analytical SQL queries over Silver Parquet tables.
- **MUST-5 (Gold Embedded LanceDB Hybrid Search):** Generate local LanceDB vector + BM25 hybrid search indexes directly from Silver Parquet, providing zero-network local semantic lookup without external SaaS lock-in.
- **MUST-6 (Gold Knowledge Graph Export):** Export semantic linked data adhering to W3C DCAT-AP 3.0, schema.org / Croissant, and RO-Crate 1.1 JSON-LD metadata models.
- **MUST-7 (CLI & MCP Query Interface):** Expose Gold DuckDB, LanceDB, and Knowledge Graph operations through `archive-govt-nz query` and FastMCP server tools.

### 1.2 SHOULD Have
- **SHOULD-1 (Deterministic Reconstructibility):** Ensure any Gold product can be wiped and regenerated bit-for-bit from Silver, and Silver can be regenerated from Bronze CAS bitstreams.
- **SHOULD-2 (Benchmark Receipt):** Record query latencies, index sizes, and transformation throughput in automated benchmark receipts.

### 1.3 COULD Have
- **COULD-1 (Tantivy Fast Lexical Fallback):** Optional embedded Tantivy lexical index for sub-millisecond keyword queries on resource-constrained devices.

### 1.4 WON'T Have (Out of Scope)
- **WONT-1 (Heavyweight External Graph/Vector DBs):** Will not spin up external Neo4j, Milvus, Qdrant, Pinecone, or cloud triplestores; all indexes must remain embedded, zero-cost, and file-based.
- **WONT-2 (Unvalidated Re-encoding):** Will not rewrite or mutate original Bronze bitstreams during transformation.
