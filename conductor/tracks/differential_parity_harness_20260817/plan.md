# Track 9 Plan: Differential/Parity Harness

## Phases

### Phase 1: Parity Schema & Models
- [x] Create `schemas/parity/v1/parity-receipt.schema.json`.
- [x] Implement `ParityComparisonResult` and `ParityReceipt` in `src/archive_govt_nz/parity/models.py`.

### Phase 2: Differential Parity Engine
- [x] Implement `DifferentialParityHarness` comparing donor vs canonical payloads.
- [x] Build `tools/run_differential_parity.py` runner script.

### Phase 3: Property Fuzzing & Quality Verification
- [x] Add Hypothesis property-based fuzzing tests in `tests/parity/test_parity_harness.py`.
- [x] Run full 18-stage assurance check suite.ffing and binary SHA-256 CAS comparison logic.

### Phase 3: Matrix Verification & Gate Execution
- [x] Execute differential parity across all adapters.
- [x] Generate verified parity receipts in `evidence/migrations/sm-govt-nz/`.
