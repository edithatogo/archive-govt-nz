# Track 14 Plan: Post-Consolidation Extension and RIOPA Interoperability

## Phases

### Phase 1: RIOPA Export Schema & Bridge
- [x] Create `schemas/riopa/v1/riopa-export-receipt.schema.json`.
- [x] Implement `RiopaInteropBridge` and `RiopaExportReceipt` in `src/archive_govt_nz/riopa/`.

### Phase 2: Interoperability Runner & Boundary Enforcement
- [x] Implement strict corpus boundary enforcement.
- [x] Build `tools/run_riopa_interop_export.py` export tool.

### Phase 3: RIOPA Test Suite & Quality Gates
- [x] Implement test suite in `tests/riopa/test_riopa_interop.py`.
- [x] Run full 19-stage assurance check suite.rnal analysis tools.
- [x] Validate cross-repository citation and dataset linkage.
