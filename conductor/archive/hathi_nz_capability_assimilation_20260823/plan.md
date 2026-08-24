# Implementation Plan: HathiTrust NZ Historic Corpus Capability Assimilation

### Phase 1: Domain Schemas, METS/MODS Parser & Raw Bronze Acquisition [COMPLETED]
- [x] Task: Define JSON schema `schemas/hathi-volume-v1.schema.json` and PyArrow tabular schema for historic NZ HathiTrust volumes.
- [x] Task: Implement `src/archive_govt_nz/domains/hathi/parser.py` parsing METS/MODS volume metadata and extracting OCR text bitstreams.
- [x] Task: Implement `src/archive_govt_nz/domains/hathi/adapter.py` connecting HathiTrust volume payloads to Bronze CAS storage.
- [x] Task: Add characterization tests for Hathi METS/OCR extraction and Bronze ingest.
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Silver Bitemporal Normalization & Public Domain Rights Classification [COMPLETED]
- [x] Task: Implement `src/archive_govt_nz/domains/hathi/normalizer.py` generating bitemporal Silver Parquet (`data/silver/hathi/corpus.parquet`).
- [x] Task: Integrate deterministic Public Domain / Crown Copyright rights classifier for historical NZ publications.
- [x] Task: Wire cross-domain citations (Historical publications ↔ Early NZ Statutes & Gazette notices).
- [x] Task: Add Silver normalization and rights classification test suite (>=95% coverage).
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Gold Analytical Engine, Semantic Search & Mutation Gates [COMPLETED]
- [x] Task: Register DuckDB analytical views and zero-copy federation hooks for HathiTrust corpus.
- [x] Task: Integrate historic texts into Gold embedded LanceDB hybrid search index.
- [x] Task: Expose HathiTrust volume search via CLI (`archive-govt-nz query`) and FastMCP server.
- [x] Task: Add mutation testing gates in `tools/mutation_medallion.py` for Hathi volume parser and normalizer.
- [x] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [x] Task: Conductor Track Review & Final Certification.

