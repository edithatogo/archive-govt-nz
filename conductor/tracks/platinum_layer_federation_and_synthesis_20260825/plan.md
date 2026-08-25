# Implementation Plan: Platinum Layer Cross-Jurisdiction Federation, Croissant ML Metadata & Citable Synthesis

### Phase 1: Cross-Repository Federation Engine (TDD)
- [ ] Task: Implement federated DuckDB join views in `src/archive_govt_nz/gold/federation.py` connecting NZ statutory & gazette data with `global-medicines-atlas` and `fyi-archive`.
- [ ] Task: Add test suite `tests/gold/test_federation_pipeline.py` testing zero-copy attaches, schema alignment, and composite URN cross-references.

### Phase 2: Croissant ML Dataset Metadata Generator
- [ ] Task: Implement full Croissant JSON-LD builder in `src/archive_govt_nz/distribution/croissant.py` supporting RecordSets, Fields, and Columnar Parquet mappings.
- [ ] Task: Validate generated Croissant metadata against MLCommons schema with unit tests in `tests/distribution/test_croissant_spec.py`.

### Phase 3: Multi-Target Publication Staging & Remote Readback
- [ ] Task: Implement automated remote readback verifier in `src/archive_govt_nz/distribution/verifier.py` for Hugging Face and Zenodo artifacts.
- [ ] Task: Wire publication receipts into the unified evidence ledger `evidence/archive-evidence-ledger.json`.

### Phase 4: CLI & FastMCP Federation Interface
- [ ] Task: Extend `archive-govt-nz query` CLI with `--federated` and `--croissant-export` options.
- [ ] Task: Register federated query tools in `src/archive_govt_nz/mcp/`.

### Phase 5: Assurance Gate & Mutation Testing
- [ ] Task: Add mutation testing lane in `tools/mutation_platinum.py` or extend `tools/mutation_medallion.py`.
- [ ] Task: Run full 19-stage assurance harness `./scripts/validate.sh` and ensure >= 95% test coverage.
