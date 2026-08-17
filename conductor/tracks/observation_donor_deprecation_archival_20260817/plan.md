# Track 13 Plan: Observation, Donor Deprecation and Archival

## Phases

### Phase 1: Donor Freeze Schema & Validator
- [x] Create `schemas/archival/v1/donor-archival-receipt.schema.json`.
- [x] Implement `DonorFreezeValidator` and `DonorArchivalReceipt` in `src/archive_govt_nz/archival/`.

### Phase 2: Deprecation & Archival Verification
- [x] Implement deprecation notice and consecutive capture cycle validation.
- [x] Build `tools/run_donor_freeze_validation.py` validation runner.

### Phase 3: Archival Test Suite & Quality Gates
- [x] Implement test suite in `tests/archival/test_donor_freeze.py`.
- [x] Run full 19-stage assurance check suite.
- [x] Update `sm-govt-nz/README.md` with canonical redirect banner.
- [x] Tag donor repository and set to read-only archived status.
- [x] Emit closeout report in `docs/migrations/sm-govt-nz/consolidation-closeout-report.md`.
