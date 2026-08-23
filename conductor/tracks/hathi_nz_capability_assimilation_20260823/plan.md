# Implementation Plan: HathiTrust NZ Historic Corpus Capability Assimilation

### Phase 1: Domain Schemas, METS/MODS Parser & Raw Bronze Acquisition
- [ ] Task: Define JSON schema `schemas/hathi-volume-v1.schema.json` and PyArrow tabular schema for historic NZ HathiTrust volumes.
- [ ] Task: Implement `src/archive_govt_nz/domains/hathi/parser.py` parsing METS/MODS volume metadata and extracting OCR text bitstreams.
- [ ] Task: Implement `src/archive_govt_nz/domains/hathi/adapter.py` connecting HathiTrust volume payloads to Bronze CAS storage.
- [ ] Task: Add characterization tests for Hathi METS/OCR extraction and Bronze ingest.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Silver Bitemporal Normalization & Public Domain Rights Classification
- [ ] Task: Implement `src/archive_govt_nz/domains/hathi/normalizer.py` generating bitemporal Silver Parquet (`data/silver/hathi/corpus.parquet`).
- [ ] Task: Integrate deterministic Public Domain / Crown Copyright rights classifier for historical NZ publications.
- [ ] Task: Wire cross-domain citations (Historical publications ↔ Early NZ Statutes & Gazette notices).
- [ ] Task: Add Silver normalization and rights classification test suite (>=95% coverage).
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Gold Analytical Engine, Semantic Search & Mutation Gates
- [ ] Task: Register DuckDB analytical views and zero-copy federation hooks for HathiTrust corpus.
- [ ] Task: Integrate historic texts into Gold embedded LanceDB hybrid search index.
- [ ] Task: Expose HathiTrust volume search via CLI (`archive-govt-nz query`) and FastMCP server.
- [ ] Task: Add mutation testing gates in `tools/mutation_medallion.py` for Hathi volume parser and normalizer.
- [ ] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [ ] Task: Conductor Track Review & Final Certification.

