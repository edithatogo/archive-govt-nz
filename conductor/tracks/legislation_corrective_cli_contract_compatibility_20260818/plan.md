# Plan: Real Legislation CLI Service Integration and nzlc Compatibility

1. **Phase 1: Real Subcommand Implementation in `src/archive_govt_nz/cli.py`**
   - Implement real handlers for `discover`, `sync`, `validate`, `manifest`, `coverage`, `changes`, `status`, `replay`, `publication-plan`, `publication-verify`, `doctor`.
   - Remove 33,693 count, 68 batches, 100% fixed coverage, and simulated statuses.
   - Redirect `capture --source-type legislation` to `legislation sync`.
2. **Phase 2: Legacy `nzlc` Compatibility Mapping in `src/archive_govt_nz/cli_compat.py`**
   - Parse legacy `nzlc` command-line arguments and invoke the corresponding real service action with deprecation warnings.
3. **Phase 3: Schema Registration & Validation**
   - Ensure CLI JSON outputs validate against strict JSON schemas.
4. **Phase 4: Comprehensive CLI Tests & Negative Controls**
   - Test dynamic manifest count sensitivity, absent manifest, corrupt records, API failure, and legacy `nzlc` parity in `tests/cli/test_cli.py`.
5. **Phase 5: Full 19-Stage Gate & Evidence Generation**
   - Run `tools/check.py`, verify >=95% patch coverage, and update track runlog/evidence/review.
