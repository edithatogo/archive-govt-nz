# Implementation Plan: Medallion NLP Bi-Directional Bridge, Bleeding-Edge OCR & Ontological Synthesis

### Phase 1: Ontological Schemas, Dynamic FastMCP & Unified Normalizer Registry (`archive-govt-nz`)
- [x] Task: Extend `src/archive_govt_nz/schemas/medallion.py` with Akoma Ntoso 3.0, ELI, NZBN, and WHO ATC ontological mappings.
- [x] Task: Unify normalizer discovery in `src/archive_govt_nz/silver/pipeline.py` to derive directly from `DOMAIN_REGISTRY`.
- [x] Task: Refactor `src/archive_govt_nz/mcp_server.py` to dynamically generate FastMCP tools and schemas from `DOMAIN_REGISTRY`.
- [x] Task: Add test suites in `tests/schemas/test_ontological_schemas.py` and `tests/mcp/test_dynamic_domain_tools.py`.

### Phase 2: Bleeding-Edge Layout Parsing, CAS Deduplication & Aho-Corasick Matcher (`nlp-policy-nz`)
- [x] Task: Implement layout-aware multi-column segmentation and de-hyphenator in `nlp-policy-nz/src/nlp_policy_nz/extraction/layout.py`.
- [x] Task: Implement CAS-based boilerplate extraction cache in `nlp-policy-nz/src/nlp_policy_nz/extraction/dedup.py`.
- [x] Task: Implement Aho-Corasick multi-pattern statutory citation matcher in `nlp-policy-nz/src/nlp_policy_nz/extraction/matcher.py`.
- [x] Task: Add test suite in `nlp-policy-nz/tests/test_layout_and_matcher.py`.

### Phase 3: Resilient Polars Streaming, Context-Manager I/O & Silver Checkpointing (`archive-govt-nz`)
- [x] Task: Refactor file handles, DuckDB connections, and Parquet writers in `src/archive_govt_nz/silver/pipeline.py` to use strict context managers.
- [x] Task: Implement stateful offset checkpointing and bounded memory buffers (< 64MB) with `.checkpoint` marker recovery.
- [x] Task: Add test suite in `tests/silver/test_checkpoint_recovery.py`.

### Phase 4: Ingestion CLI Bridge, Sub-50ms Lazy Imports & spaCy Pipeline Components (`nlp-policy-nz`)
- [x] Task: Implement `nlp-policy-nz ingest` CLI command in `nlp-policy-nz/src/nlp_policy_nz/cli/ingest.py`.
- [x] Task: Implement lazy module resolution (`__getattr__`) across `storage`, `semantic`, and `pipeline` in `nlp-policy-nz` for sub-50ms CLI startup.
- [x] Task: Implement packaged spaCy pipeline components in `nlp-policy-nz/src/nlp_policy_nz/pipeline/components.py`.
- [x] Task: Add test suite in `nlp-policy-nz/tests/test_pipeline_components.py`.

### Phase 5: Reverse Gold Knowledge Graph Ingestion & LanceDB Entity Search (`archive-govt-nz`)
- [x] Task: Implement `GoldKnowledgeGraphIngestor` in `src/archive_govt_nz/gold/analytics.py` registering `v_gold_extracted_entities` and `v_gold_statutory_graph`.
- [x] Task: Add entity relationship vector search in `src/archive_govt_nz/gold/search.py`.
- [x] Task: Add test suite in `tests/gold/test_knowledge_graph_feedback.py`.

### Phase 6: Supply-Chain Hardening, Test Tiering & Full 22-Stage Assurance Gate
- [x] Task: Synchronize dev environment and `uv.lock` in `nlp-policy-nz` (installing `ruff`, `pytest-cov`, `basedpyright`).
- [x] Task: Implement targeted mutation test lane in `tools/mutation_nlp_bridge.py`.
- [x] Task: Run full 22-stage assurance harness `./scripts/validate.sh` ensuring 100% pass and >= 95% branch coverage.
