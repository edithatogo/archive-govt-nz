# Implementation Plan

## Phase 1 — Contracts and security hardening (#45)

- [x] Task: Add failing tests for trusted snapshot URLs and bounded capture
  - [x] Test non-HTTPS, wrong-host, excessive-size, hash, and deterministic cases
  - [x] Add property, metamorphic, contract, and deterministic simulation coverage
- [x] Task: Implement reusable redundancy policy and receipt contracts
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2 — Scheduled discovery, capture, and triangulation (#46)

- [x] Task: Add deterministic triangulation and object verification commands
- [x] Task: Add bounded Save Page Now submission for missing allowlisted URLs
- [x] Task: Add weekly/manual GitHub Actions workflow with retained artefacts
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3 — Hosted assurance and operational evidence (#47)

- [x] Task: Run focused and complete local assurance gates
- [x] Task: Push and verify the exact hosted workflow and issue hierarchy
- [x] Task: Run Conductor self-review and resolve actionable findings
- [x] Task: Reconcile evidence, metadata, registry, and issue states
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)
