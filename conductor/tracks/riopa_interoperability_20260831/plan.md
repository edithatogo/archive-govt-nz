# Plan: RIOPA interoperability integration

## Phase 1: contract

- [x] Define the receipt-to-RIOPA mapping schema and version policy.
- [x] Add deterministic fixtures for complete, partial and negative attempts.

## Phase 2: implementation

- [x] Implement export and replay validation using archived inputs only.
- [x] Preserve rights, source-health, capability and legal-status boundaries.
- [x] Add stale-revision and digest-mismatch failure paths.

## Phase 3: assurance

- [ ] Run the full repository validation harness on Python 3.14 after this slice.
- [ ] Run an agent-panel review of implementation and evidence.
- [ ] Record hosted handoff evidence without claiming external participation or release.
