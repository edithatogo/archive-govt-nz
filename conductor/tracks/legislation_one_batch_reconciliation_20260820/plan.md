# Plan

## Phase 1: Replacement contract

- [~] Add adversarial tests and a versioned receipt schema for exactly one real
  batch reconciliation.
- [ ] Replace the synthetic parity generator and invalidate its generated
  success receipts without erasing historical provenance.

## Phase 2: Local validation and review

- [ ] Run focused coverage, Ruff, BasedPyright, schema validation, and the full
  locked repository harness.
- [ ] Complete self-review and record local-only evidence.

## Phase 3: Ordered real execution

- [ ] Rebase after service, global CLI, legislation CLI, MCP, and workflow
  corrections; open only the one allowed successor PR at its sequence point.
- [ ] Execute exactly one bounded real batch and retain its reconciled receipt.
  This remains pending and cannot be satisfied by fixtures or generated state.

