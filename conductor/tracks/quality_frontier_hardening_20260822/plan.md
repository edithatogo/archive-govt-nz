# Plan: Quality Frontier Hardening

## Phases

### Phase 1: Gap Audit
- [x] Audit existing assurance stages and mutation coverage; identify the new
      gazette domain validation module as an unprotected policy-critical surface.

### Phase 2: TDD Strengthening
- [x] Add boolean-year rejection test before mutation enforcement.

### Phase 3: Mutation Suite
- [x] Implement `tools/mutation_gazette.py` with 7 bounded mutants.
- [x] Verify 100% kill rate (`killed=7/7, status=passed`).

### Phase 4: Gate Registration
- [x] Register `mutation-gazette` stage in `src/archive_govt_nz/assurance.py`.
- [x] Add per-file lint ignores in `pyproject.toml`.

### Phase 5: Full Assurance Gate
- [x] Run full `tools/check.py`; record result.

> **Status: COMPLETED** — All phases verified. Reviewed and closed 2026-08-22.