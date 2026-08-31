# Plan: RIOPA interoperability integration

## Phase 1: contract

- [x] Define the receipt-to-RIOPA mapping schema and version policy.
- [x] Add deterministic fixtures for complete, partial and negative attempts.

## Phase 2: implementation

- [x] Implement export and replay validation using archived inputs only.
- [x] Preserve rights, source-health, capability and legal-status boundaries.
- [x] Add stale-revision and digest-mismatch failure paths.

## Phase 3: assurance

- [x] Run the full repository validation harness on Python 3.14 after this slice (PR #279 hosted Assurance on all three platforms, `174b766`).
- [x] Run an agent-panel review of implementation and evidence (`delivery_audit`, `repair_272`, root; PR #279).
- [x] Record hosted handoff evidence without claiming external participation or release (`hosted-closeout.json`).

## Review fixes

- [x] Reject unqualified capture/legal states and explicitly disable claims while preserving source observations; verify negative paths and schema compatibility.
- [x] Complete full assurance and archive reconciliation after the correction passes hosted checks (PR #279 merged as `1b2d7c0`; broader gates remain outside this track).
