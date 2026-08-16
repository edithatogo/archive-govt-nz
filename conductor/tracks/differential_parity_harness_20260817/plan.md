# Track 9 Plan: Differential/Parity Harness

## Phases

### Phase 1: Test Fixtures & Network Recording
- [ ] Record offline deterministic response fixtures for Bluesky, Threads, X, YouTube, Feeds, and Email.
- [ ] Save fixtures under `tests/fixtures/differential_parity/`.

### Phase 2: Parity Harness Implementation
- [ ] Implement `tools/differential_parity_harness.py`.
- [ ] Build structural JSON diffing and binary SHA-256 CAS comparison logic.

### Phase 3: Matrix Verification & Gate Execution
- [ ] Execute differential parity across all adapters.
- [ ] Generate verified parity receipts in `evidence/migrations/sm-govt-nz/`.
