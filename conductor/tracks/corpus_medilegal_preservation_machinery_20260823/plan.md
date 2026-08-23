# Implementation Plan: Medico-Legal Case Law Preservation Machinery

### Phase 1: Domain Schemas, Anonymization Sanitizer & Raw Bronze Acquisition
- [ ] Task: Define JSON schema `schemas/medilegal-case-v1.schema.json` and PyArrow schema for NZ medico-legal tribunal decisions.
- [ ] Task: Implement `src/archive_govt_nz/domains/medilegal/sanitizer.py` for deterministic redaction of sensitive health data while preserving legal statutory citations.
- [ ] Task: Implement `src/archive_govt_nz/domains/medilegal/parser.py` extracting case headings, tribunal findings, and statutory references.
- [ ] Task: Implement `src/archive_govt_nz/domains/medilegal/adapter.py` connecting case payloads to Bronze CAS storage.
- [ ] Task: Add characterization tests for sanitizer, parser, and Bronze ingest.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Silver Bitemporal Normalization & Statutory Cross-Referencing
- [ ] Task: Implement `src/archive_govt_nz/domains/medilegal/normalizer.py` generating bitemporal Silver Parquet (`data/silver/medilegal/corpus.parquet`).
- [ ] Task: Wire cross-domain statutory links (Tribunal findings ↔ HPCA Act, Medicines Act, Pae Ora legislation).
- [ ] Task: Add Silver normalization and statutory link test suite (>=95% coverage).
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Gold Analytical Engine, Semantic Search & Mutation Gates
- [ ] Task: Register DuckDB analytical views and zero-copy federation hooks for Medico-Legal decisions.
- [ ] Task: Integrate case law corpus into Gold embedded LanceDB hybrid search index.
- [ ] Task: Expose Medico-Legal case queries via CLI (`archive-govt-nz query`) and FastMCP server.
- [ ] Task: Add mutation testing gates in `tools/mutation_medallion.py` for sanitizer and case normalizer.
- [ ] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [ ] Task: Conductor Track Review & Final Certification.

