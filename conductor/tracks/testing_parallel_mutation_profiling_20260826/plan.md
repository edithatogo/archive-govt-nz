# Implementation Plan: Testing Modernization (Pytest-Gremlins, Parallelisation, Property Testing & Scalene)

### Phase 1: Pytest-Gremlins Integration & Dedicated Mutation Runner
- [x] Task: Ensure `pytest-gremlins` is locked in `pyproject.toml` and configure gremlins settings. (`ab4ed66`)
- [x] Task: Create `tools/run_gremlins.py` runner script that executes mutation testing and emits `build/gremlins-report.json`. (`86dbbed`)
- [x] Task: Add test for gremlins runner in `tests/tools/test_run_gremlins.py`. (`af9aa2e`)
- [x] **Review Fixes:** Exclude generated coverage shards from the source secret scan. (`bce9206`)

### Phase 2: Parallel Test Execution Harness (`pytest-xdist`)
- [x] Task: Configure `pytest-xdist` parallel execution options in `tools/check.py` and `src/archive_govt_nz/assurance.py`. (`05add7a`)
- [x] Task: Verify that parallel execution passes 100% across all 1,100+ tests without cross-test race conditions. (`90.31s`, 1,163 passed)

### Phase 3: Property-Based Testing Suite (`hypothesis`)
- [x] Task: Implement `tests/properties/test_urn_properties.py` for URN parsing invariants. (`007e68e`)
- [x] Task: Implement `tests/properties/test_multihash_properties.py` for BLAKE3/SHA256/CIDv1 invariants. (`45db8ed`)
- [x] Task: Implement `tests/properties/test_schema_properties.py` for PyArrow and Croissant schema invariants. (`0b444f6`)
- [x] Task: Implement `tests/properties/test_statutory_matcher_properties.py` for statutory matcher fuzzing. (`c5930c0`)

### Phase 4: Scalene Memory & Performance Profiling Harness
- [ ] Task: Create `tools/profile_scalene.py` executing CPU, native memory, and copy overhead profiling over the Medallion pipeline.
- [ ] Task: Generate structured profiling receipts in `build/profiling-scalene.json`.
- [ ] Task: Add test suite in `tests/tools/test_profile_scalene.py`.

### Phase 5: Assurance Gate Synchronization & Full Harness Validation
- [ ] Task: Update `src/archive_govt_nz/assurance.py` with `profile-scalene` and updated gate stages.
- [ ] Task: Update `tests/test_assurance_harness.py` and `README.md`.
- [ ] Task: Run `./scripts/validate.sh` and ensure all stages pass green with >= 95% branch coverage.
