# Track 12 Plan: Release Cutover and Publication Continuity

## Phases

### Phase 1: Workflow Harmonization & Secret Setup
- [x] Ensure all required secrets (`HF_TOKEN`, `ZENODO_TOKEN`, `HARVEST_WEBHOOK_URL`) are active in `archive-govt-nz`.
- [x] Configure scheduled GitHub Actions workflows for unified multi-source harvesting.

### Phase 1: Cutover Schema & Orchestrator
- [x] Create `schemas/cutover/v1/cutover-receipt.schema.json`.
- [x] Implement `CutoverOrchestrator` and `ReleaseCutoverReceipt` in `src/archive_govt_nz/cutover/`.

### Phase 2: Production Rehearsal & Validation
- [x] Implement root fixity hash verification across Hugging Face and Zenodo endpoints.
- [x] Build `tools/run_release_cutover.py` rehearsal script.

### Phase 3: Cutover Test Suite & Quality Gates
- [x] Implement test suite in `tests/cutover/test_cutover_orchestrator.py`.
- [x] Run full 19-stage assurance check suite.s and public dataset card provenance links.
