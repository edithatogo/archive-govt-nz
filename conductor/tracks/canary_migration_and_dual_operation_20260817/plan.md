# Track 10 Plan: Canary Migration and Dual Operation

## Phases

### Phase 1: Canary Schema & Pipeline Runner
- [x] Create `schemas/canary/v1/canary-receipt.schema.json`.
- [x] Implement `ShadowPipelineRunner` and `CanaryExecutionReceipt` in `src/archive_govt_nz/canary/`.

### Phase 2: Shadow Dual-Run & Rollback Rehearsal
- [x] Implement dual-store capture simulation and zero-divergence validation.
- [x] Implement instantaneous rollback rehearsal simulation.
- [x] Build `tools/run_canary_shadow.py` runner tool.

### Phase 3: Canary Test Suite & Quality Gates
- [x] Implement test suite in `tests/canary/test_shadow_runner.py`.
- [x] Run full 18-stage assurance check suite.
