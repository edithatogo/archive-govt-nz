# Implementation Plan: Platinum Layer Cross-Jurisdiction Federation, Croissant ML Metadata & Citable Synthesis

### Phase 1: Medallion Schema-as-Code & Croissant Generator (TDD)
- [ ] Task: Implement unified schema generator in `src/archive_govt_nz/schemas/medallion.py` mapping Silver/Gold fields to Arrow, Pydantic, DCAT-AP 3.0, and MLCommons Croissant (`croissant.json`).
- [ ] Task: Add test suite `tests/schemas/test_medallion_croissant.py` validating Croissant schema compliance across all 7 domain datasets.

### Phase 2: Polars LazyFrame Ingestion & Streaming Optimization
- [ ] Task: Refactor `SilverPipeline` in `src/archive_govt_nz/silver/pipeline.py` to use `polars.LazyFrame` with streaming chunk processing for large historical batches.
- [ ] Task: Add performance regression tests in `tests/silver/test_streaming_performance.py`.

### Phase 3: Universal Hugging Face Dataset Hub & Publication Router
- [ ] Task: Implement dataset card and Croissant bundle builder in `src/archive_govt_nz/distribution/publisher.py` for all 7 datasets (`nz-legislation`, `nz-gazette`, `nz-hansard`, `nz-hathitrust-historic`, `nz-cases-medilegal`, `archive-govt-nz-treasury`, `nz-ckan-catalogs`).
- [ ] Task: Implement remote readback verifier in `src/archive_govt_nz/distribution/verifier.py` with fail-closed SHA-256 hash assertions.
- [ ] Task: Add tests in `tests/distribution/test_publisher.py` and `tests/distribution/test_verifier.py`.

### Phase 4: Zero-Copy Cross-Repository Federation & `nlp-policy-nz` Export Contracts
- [ ] Task: Implement pre-built DuckDB federation views in `src/archive_govt_nz/gold/federation.py` joining NZ statutory/gazette data with `global-medicines-atlas` (`gma_*`) and `fyi-archive` (`fyi_*`).
- [ ] Task: Define typed export contracts and test fixtures in `src/archive_govt_nz/gold/nlp_export.py` for downstream consumption by `nlp-policy-nz`.
- [ ] Task: Add tests in `tests/gold/test_federation_views.py` and `tests/gold/test_nlp_export.py`.

### Phase 5: Five-Donor Archival Readiness & Claim Drift Enforcement
- [ ] Task: Extend `tools/check_claim_drift.py` to monitor archival state across all 5 donor repositories (`sm-govt-nz`, `corpus-legislation-nz`, `corpus-nz-hansard`, `hathi-nz`, `corpus-cases-medilegal-nz`).
- [ ] Task: Generate retirement readiness receipts in `evidence/migrations/` for Hansard, HathiTrust, and Medico-Legal case law.
- [ ] Task: Add tests in `tests/tools/test_check_claim_drift.py`.

### Phase 6: CLI, MCP & 19-Stage Assurance Gate
- [ ] Task: Extend `archive-govt-nz query` CLI with `--federated`, `--croissant-export`, and `--hf-manifest` options.
- [ ] Task: Register FastMCP tools in `src/archive_govt_nz/mcp/` for federated queries.
- [ ] Task: Implement mutation testing lane in `tools/mutation_platinum.py`.
- [ ] Task: Run full 19-stage assurance harness `./scripts/validate.sh` and ensure >= 95% test coverage.
