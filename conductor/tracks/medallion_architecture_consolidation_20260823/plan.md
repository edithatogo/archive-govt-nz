# Implementation Plan: Medallion Architecture Consolidation

## Primary Focus: Phase 1 (Bronze Ingestion & Preservation Layer)

---

## Phases & Tasks

### Phase 1: Bronze Ingestion Layer & Immutable Storage Standardization (PRIMARY FOCUS)
- [ ] Task: Formalize Bronze storage hierarchy (`data/bronze/{domain}/`, CAS object stores `sha256/` and `blake3/`, WARC/WACZ bitstream trees).
- [ ] Task: Standardize Bronze ingestion manifest model across all core domains (Legislation, Gazette, CKAN data.govt.nz, Health/MoH, Treasury, Feeds/Social).
- [ ] Task: Incorporate newly discovered domain feeds into Bronze ingestion manifests:
    - [ ] Courts NZ Public Notices archive (`edithatogo/courts-nz-public-notices-archive`) into Gazette/Notices adapter
    - [ ] NZ COVID-19 Official Data (`edithatogo/nz-covid-data`) into Health domain
    - [ ] Pae Ora Health System Reform releases (`edithatogo/pae_ora_reform`) into Health domain
- [ ] Task: Write characterization, fixity, and zero-loss unit tests for Bronze storage and CAS streaming across all domains.
- [ ] Task: Conductor - User Manual Verification 'Bronze Ingestion Layer' (Protocol in workflow.md).

### Phase 2: Silver Layer Parquet Pipelines (Polars / PyArrow)
- [ ] Task: Implement standardized Silver normalizer base in `src/archive_govt_nz/silver/base.py` with Arrow schema validation.
- [ ] Task: Build vectorized Polars/PyArrow normalizers producing canonical Parquet (`data/silver/{domain}/corpus.parquet`).
- [ ] Task: Encode bitemporal timeline tracking (`source_observed_at` vs. valid statutory/notice effective dates).
- [ ] Task: Write unit and property-based tests verifying 100% field parity and schema conformance.
- [ ] Task: Conductor - User Manual Verification 'Silver Layer Parquet Pipelines' (Protocol in workflow.md).

### Phase 3: Silver Cross-Domain Interlinking & Relational Lineage Graph
- [ ] Task: Elevate `tools/build_identifier_interlink.py` into canonical Silver interlinking engine (`src/archive_govt_nz/silver/interlink.py`).
- [ ] Task: Build cross-domain relational graph joins (Legislation ↔ Gazette ↔ Courts ↔ Health ↔ CKAN).
- [ ] Task: Generate unified Silver provenance and lineage manifests.
- [ ] Task: Add test suite verifying bidirectional resolution and cycle safety.
- [ ] Task: Conductor - User Manual Verification 'Silver Cross-Domain Interlinking' (Protocol in workflow.md).

### Phase 4: Gold Layer DuckDB Analytical Engine & DCAT-AP Knowledge Graph
- [ ] Task: Implement Gold DuckDB view layer in `src/archive_govt_nz/gold/analytics.py` for cross-domain SQL queries.
- [ ] Task: Implement DCAT-AP 3.0 / schema.org Croissant / RO-Crate 1.1 Gold metadata exporter.
- [ ] Task: Implement zero-copy DuckDB remote/local federation hooks for `global-medicines-atlas` and `fyi-archive`.
- [ ] Task: Add unit and integration tests for DuckDB views, federation hooks, and knowledge graph serialization.
- [ ] Task: Conductor - User Manual Verification 'Gold DuckDB & Knowledge Graph' (Protocol in workflow.md).

### Phase 5: Gold Layer Embedded LanceDB Hybrid Vector Index
- [ ] Task: Implement embedded LanceDB index generator in `src/archive_govt_nz/gold/search.py` consuming Silver Parquet.
- [ ] Task: Integrate deterministic dense vector projections with BM25 hybrid ranking (zero external API dependencies).
- [ ] Task: Benchmark search recall, index construction speed, and zero-network execution.
- [ ] Task: Add unit and regression tests for vector and lexical retrieval.
- [ ] Task: Conductor - User Manual Verification 'Gold LanceDB Hybrid Index' (Protocol in workflow.md).

### Phase 6: Unified CLI & MCP Query Surface
- [ ] Task: Implement `archive-govt-nz query` CLI command supporting `--sql`, `--semantic`, and `--graph` modes.
- [ ] Task: Expose Gold DuckDB, LanceDB, and Knowledge Graph tools via FastMCP server (`src/archive_govt_nz/mcp_server.py`).
- [ ] Task: Write CLI and MCP contract tests against representative multi-domain fixture data.
- [ ] Task: Conductor - User Manual Verification 'CLI & MCP Query Surface' (Protocol in workflow.md).

### Phase 7: Quality Gates, Mutation Testing & End-to-End Evidence
- [ ] Task: Add mutation testing suite for Medallion transformation pipeline (`tools/mutation_medallion.py`).
- [ ] Task: Run full 19-stage validation harness (`tools/check.py`) with >=95% branch coverage.
- [ ] Task: Record end-to-end evidence receipt in `evidence/medallion/medallion-consolidation-receipt.json`.
- [ ] Task: Conductor - User Manual Verification 'Quality Gates & Evidence' (Protocol in workflow.md).
