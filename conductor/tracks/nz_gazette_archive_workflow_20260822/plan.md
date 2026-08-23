# Plan: NZ Gazette Archive Workflow

> **Status: IN PROGRESS** — Track created 2026-08-22.

## Phases & Deliverables

### Phase 1: Infrastructure Audit & Reuse
- [x] Audit existing `NZGazetteAdapter`, domain models, schema, and source-set config.
- [x] Confirm adapter tests pass and transport contract is reusable as-is.

### Phase 2: Domain Service Layer (TDD)
- [x] Implement `domains/gazette/validate.py` with schema-consistent validation rules.
- [x] Implement `domains/gazette/discovery.py` for typed notice discovery targets.
- [x] Implement `domains/gazette/service.py` (`GazetteArchiveService`) wiring adapter,
      normalisation, manifest, and checkpoint management.
- [x] Manifest construction embedded in orchestrator receipt/manifest emission
      (`archive-govt-nz.gazette-manifest/v1`) — separate module not required.

### Phase 3: Harvest Orchestrator (TDD)
- [x] Implement `tools/run_gazette_harvest.py` with full outcome taxonomy and
      checkpoint restore/promote semantics.
- [x] Implement test suite `tests/tools/test_run_gazette_harvest.py` with negative
      controls (invalid config, disabled source-set, sync failure, validation failure,
      CLI entrypoint).

### Phase 4: CI Scheduling
- [x] Add `.github/workflows/scheduled-gazette-harvest.yml` with pinned SHAs and
      receipt upload.

### Phase 5: Assurance Gate & Evidence
- [x] Run focused tests, then full `tools/check.py` 19-stage gate.
- [x] Record evidence receipts and complete review.

> **Status: COMPLETED** — All phases verified. Reviewed and closed 2026-08-22.