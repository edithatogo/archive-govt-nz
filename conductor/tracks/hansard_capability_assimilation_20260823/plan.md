# Implementation Plan: Hansard Corpus Capability Assimilation

### Phase 1: Domain Schemas, XML Streaming Parser & Raw Bronze Acquisition [COMPLETED]
- [x] Task: Define JSON schema `schemas/hansard-debate-v1.schema.json` and PyArrow tabular schema for NZ Parliamentary Debates.
- [x] Task: Implement `src/archive_govt_nz/domains/hansard/parser.py` supporting fast streaming XML parsing of Hansard sitting day records.
- [x] Task: Implement `src/archive_govt_nz/domains/hansard/adapter.py` integrating Bronze CAS payload storage and manifest generation.
- [x] Task: Add characterization tests for Hansard XML parsing and Bronze ingest.
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Silver Bitemporal Normalization & Speaker Entity Reconciliation
- [ ] Task: Implement `src/archive_govt_nz/domains/hansard/normalizer.py` vectorizing speeches into bitemporal Silver Parquet (`data/silver/hansard/corpus.parquet`).
- [ ] Task: Integrate Member of Parliament (MP) identity reconciliation and speech segment typing.
- [ ] Task: Wire cross-domain reference extraction (Debate speeches ↔ Legislation Acts & Bills).
- [ ] Task: Add comprehensive Silver transformation and entity linkage test suite (>=95% coverage).
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Gold Analytical Engine, Semantic Search & Mutation Gates
- [ ] Task: Register DuckDB analytical views and zero-copy federation hooks for Hansard corpus.
- [ ] Task: Integrate Hansard debate corpus into Gold embedded LanceDB hybrid search.
- [ ] Task: Expose Hansard queries through CLI (`archive-govt-nz query`) and FastMCP server.
- [ ] Task: Add mutation testing gates in `tools/mutation_medallion.py` for Hansard normalizer and parser.
- [ ] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [ ] Task: Conductor Track Review & Final Certification.

