# Programme Plan: Legislation Corpus Consolidation

## Phases & Tracks

### Phase 1: Pre-Acquisition Discovery & Baseline Audit
- [x] Execute mandatory pre-acquisition discovery across Git, HF, Zenodo, and local stores.
- [x] Freeze baseline commit SHAs and build comprehensive capability matrix.
- [x] Build complete workflow route table for all 25 donor workflows.

### Phase 2: Donor Lineage & Issue Reconciliation
- [x] Import donor Conductor track history to `conductor/archive/imported/corpus-legislation-nz/`.
- [x] Reconcile all 65 donor GitHub issues individually with target tracking.

### Phase 3: External Identity & Publication Registry
- [x] Create publication registry in `registry/publications/legislation.yml`.
- [x] Reconcile Hugging Face and Zenodo identifiers in `external-identities.json`.

### Phase 4: Target Adapters & Domain Architecture
- [x] Implement `src/archive_govt_nz/adapters/nz_legislation.py` and `nz_gazette.py`.
- [x] Implement `src/archive_govt_nz/domains/legislation/` and `domains/gazette/`.
- [x] Implement schemas in `schemas/legislation/v1/` and `schemas/gazette/v1/`.
- [x] Create checked-in source sets `config/source-sets/legislation.yml` and `nz-gazette.yml`.

### Phase 5: Corpus Pipeline, Parity & CLI/MCP Surfaces
- [x] Implement CLI legislation subcommands and `nzlc` compatibility entrypoint.
- [x] Execute differential parity test suite (fixtures, batches, public smoke).
- [x] Generate parity receipts and parity report.

### Phase 6: Staged Cutover & Final Closeout
- [x] Write architectural specifications (`docs/architecture/`).
- [x] Write cutover runbook and closeout report.
- [x] Verify full 19-stage assurance suite and merge to main.
