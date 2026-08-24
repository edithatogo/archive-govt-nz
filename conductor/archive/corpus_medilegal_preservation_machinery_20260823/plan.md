# Implementation Plan: Medico-Legal Case Law Preservation Machinery

### Phase 1: Domain Schemas, Anonymization Sanitizer & Raw Bronze Acquisition [COMPLETED]
- [x] Task: Define JSON schema `schemas/medilegal-case-v1.schema.json` and PyArrow schema for NZ medico-legal tribunal decisions.
- [x] Task: Implement `src/archive_govt_nz/domains/medilegal/sanitizer.py` for deterministic redaction of sensitive health data while preserving legal statutory citations.
- [x] Task: Implement `src/archive_govt_nz/domains/medilegal/parser.py` extracting case headings, tribunal findings, and statutory references.
- [x] Task: Implement `src/archive_govt_nz/domains/medilegal/adapter.py` connecting case payloads to Bronze CAS storage.
- [x] Task: Add characterization tests for sanitizer, parser, and Bronze ingest.
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Silver Bitemporal Normalization & Statutory Cross-Referencing [COMPLETED]
- [x] Task: Implement `src/archive_govt_nz/domains/medilegal/normalizer.py` generating bitemporal Silver Parquet (`data/silver/medilegal/corpus.parquet`).
- [x] Task: Wire cross-domain statutory links (Tribunal findings ↔ HPCA Act, Medicines Act, Pae Ora legislation).
- [x] Task: Add Silver normalization and statutory link test suite (>=95% coverage).
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Gold Analytical Engine, Semantic Search & Mutation Gates [COMPLETED]
- [x] Task: Register DuckDB analytical views and zero-copy federation hooks for Medico-Legal decisions.
- [x] Task: Integrate case law corpus into Gold embedded LanceDB hybrid search index.
- [x] Task: Expose Medico-Legal case queries via CLI (`archive-govt-nz query`) and FastMCP server.
- [x] Task: Add mutation testing gates in `tools/mutation_medallion.py` for sanitizer and case normalizer.
- [x] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [x] Task: Conductor Track Review & Final Certification.
