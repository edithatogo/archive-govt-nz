# Implementation Plan: Medallion Architecture Consolidation

## Primary Focus: Phase 1 (Bronze Ingestion & Preservation Layer)

---

## Phases & Tasks

### Phase 1: Bronze Ingestion Layer & Immutable Storage Standardization [COMPLETED]
- [x] Task: Formalize Bronze storage hierarchy (`data/bronze/{domain}/`, CAS object stores `sha256/` and `blake3/`, WARC/WACZ bitstream trees).
- [x] Task: Standardize Bronze ingestion manifest model across all core domains (Legislation, Gazette, CKAN data.govt.nz, Health/MoH, Treasury, Feeds/Social).
- [x] Task: Incorporate newly discovered domain feeds into Bronze ingestion manifests:
    - [x] Courts NZ Public Notices archive (`edithatogo/courts-nz-public-notices-archive`) into Gazette/Notices adapter
    - [x] NZ COVID-19 Official Data (`edithatogo/nz-covid-data`) into Health domain
    - [x] Pae Ora Health System Reform releases (`edithatogo/pae_ora_reform`) into Health domain
- [x] Task: Write characterization, fixity, and zero-loss unit tests for Bronze storage and CAS streaming across all domains.
- [x] Task: Conductor Review & Automated Phase Gate Verification (`tools/conductor_phase_gate.py --phase phase_1_bronze`).
- [x] Task: Apply Phase 1 review findings, code fixes, and advance to Phase 2.

### Phase 2: Silver Layer Parquet Pipelines (Polars / PyArrow) [COMPLETED]
- [x] Task: Implement standardized Silver normalizer base in `src/archive_govt_nz/silver/base.py` with Arrow schema validation.
- [x] Task: Build vectorized Polars/PyArrow normalizers producing canonical Parquet (`data/silver/{domain}/corpus.parquet`).
- [x] Task: Encode bitemporal timeline tracking (`source_observed_at` vs. valid statutory/notice effective dates).
- [x] Task: Write unit and property-based tests verifying 100% field parity and schema conformance.
- [x] Task: Conductor Review & Automated Phase Gate Verification (`tools/conductor_phase_gate.py --phase phase_2_silver`).
- [x] Task: Apply Phase 2 review findings, code fixes, and advance to Phase 3.

### Phase 3: Silver Cross-Domain Interlinking & Relational Lineage Graph [COMPLETED]
- [x] Task: Elevate `tools/build_identifier_interlink.py` into canonical Silver interlinking engine (`src/archive_govt_nz/silver/interlink.py`).
- [x] Task: Build cross-domain relational graph joins (Legislation ↔ Gazette ↔ Courts ↔ Health ↔ CKAN).
- [x] Task: Generate unified Silver provenance and lineage manifests.
- [x] Task: Add test suite verifying bidirectional resolution and cycle safety.
- [x] Task: Conductor Review & Automated Phase Gate Verification (`tools/conductor_phase_gate.py --phase phase_3_silver_interlink`).
- [x] Task: Apply Phase 3 review findings, code fixes, and advance to Phase 4.

### Phase 4: Gold Layer DuckDB Analytical Engine & DCAT-AP Knowledge Graph [COMPLETED]
- [x] Task: Implement Gold DuckDB view layer in `src/archive_govt_nz/gold/analytics.py` for cross-domain SQL queries.
- [x] Task: Implement DCAT-AP 3.0 / schema.org Croissant / RO-Crate 1.1 Gold metadata exporter.
- [x] Task: Implement zero-copy DuckDB remote/local federation hooks for `global-medicines-atlas` and `fyi-archive`.
- [x] Task: Add unit and integration tests for DuckDB views, federation hooks, and knowledge graph serialization.
- [x] Task: Conductor Review & Automated Phase Gate Verification (`tools/conductor_phase_gate.py --phase phase_4_gold_duckdb`).
- [x] Task: Apply Phase 4 review findings, code fixes, and advance to Phase 5.

### Phase 5: Gold Layer Embedded LanceDB Hybrid Vector Index [COMPLETED]
- [x] Task: Implement embedded LanceDB index generator in `src/archive_govt_nz/gold/search.py` consuming Silver Parquet.
- [x] Task: Integrate deterministic dense vector projections with BM25 hybrid ranking (zero external API dependencies).
- [x] Task: Benchmark search recall, index construction speed, and zero-network execution.
- [x] Task: Add unit and regression tests for vector and lexical retrieval.
- [x] Task: Conductor Review & Automated Phase Gate Verification (`tools/conductor_phase_gate.py --phase phase_5_gold_lancedb`).
- [x] Task: Apply Phase 5 review findings, code fixes, and advance to Phase 6.

### Phase 6: Unified CLI & MCP Query Surface [COMPLETED]
- [x] Task: Implement `archive-govt-nz query` CLI command supporting `--sql`, `--semantic`, and `--graph` modes.
- [x] Task: Expose Gold DuckDB, LanceDB, and Knowledge Graph tools via FastMCP server (`src/archive_govt_nz/mcp_server.py`).
- [x] Task: Write CLI and MCP contract tests against representative multi-domain fixture data.
- [x] Task: Conductor Review & Automated Phase Gate Verification (`tools/conductor_phase_gate.py --phase phase_6_cli_mcp`).
- [x] Task: Apply Phase 6 review findings, code fixes, and advance to Phase 7.

### Phase 7: Quality Gates, Mutation Testing & End-to-End Evidence
- [ ] Task: Add mutation testing suite for Medallion transformation pipeline (`tools/mutation_medallion.py`).
- [ ] Task: Run full 19-stage validation harness (`tools/check.py`) with >=95% branch coverage.
- [ ] Task: Record end-to-end evidence receipt in `evidence/medallion/medallion-consolidation-receipt.json`.
- [ ] Task: Conductor Track Review & Final Certification (`tools/conductor_phase_gate.py --phase phase_7_gates`).
