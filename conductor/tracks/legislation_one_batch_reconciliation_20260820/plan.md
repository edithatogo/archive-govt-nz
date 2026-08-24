# Plan

## Phase 1: Replacement contract

- [x] Add adversarial tests and a versioned receipt schema for exactly one real
  batch reconciliation.
- [x] Replace the synthetic parity generator and invalidate its generated
  success receipts without erasing historical provenance.

## Phase 2: Local validation and review

- [x] Run focused coverage, Ruff, BasedPyright, schema validation, and the full
  locked repository harness.
- [x] Complete self-review and record local-only evidence.

## Phase 3: Ordered real execution

- [x] Stack locally after service, global CLI, legislation CLI, MCP, and
  workflow corrections.
- [x] Open only the one allowed successor PR at its sequence point. Completed via PR #179 (`8e84746`).
- [x] Execute exactly one bounded real batch and retain its reconciled receipt.
  Verified and recorded in `evidence/migrations/corpus-legislation-nz/first-operational-cycle/reconciliation-receipt.json`.
