# Plan

## Phase 1: Contract and red tests

- [x] Add adversarial legislation CLI and compatibility tests.
- [x] Define shared authenticated local-state inspection.

## Phase 2: Implementation

- [x] Route sync through the corrected archive service.
- [x] Make discovery, validation, manifest, coverage, changes, status, replay,
  publication, doctor, and compatibility mappings fail closed.

## Phase 3: Validation and sequence handoff

- [x] Run focused coverage and full repository validation. All local gates,
  PyPI audit, and OSV audits passed.
- [x] Complete local implementation self-review.
- [x] Rebase and open only after service and global CLI predecessors complete. Completed via PR #158 (`bc5acda`) and PR #159 (`c16ad20`).
