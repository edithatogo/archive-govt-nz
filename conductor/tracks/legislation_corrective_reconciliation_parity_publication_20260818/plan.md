# Plan: Historical Reconciliation, Parity, and Publication Identity

Track: `legislation_corrective_reconciliation_parity_publication_20260818`

## Execution Phases

### Phase 1: Contract & Test Specification (Commit A)
- Update track requirements and execution plan.
- Establish acceptance contracts for differential parity and publication readback gating.
- Validate contract schemas via `tools/validate_contracts.py`.

### Phase 2: Implementation & Parity Evidence Generation (Commit B)
- Reconcile multi-batch CAS accounting in `tools/generate_executable_legislation_parity.py`.
- Execute differential parity comparisons against historical donor payloads.
- Enforce honest token gating in `tools/generate_publication_metadata.py` and `tools/evaluate_legislation_completion.py`.
- Run focused unit and integration tests under `tests/parity/`.

### Phase 3: Assurance & Evidence Verification
- Run `./scripts/validate.sh` / `tools/check.py`.
- Confirm 0 lint/type errors, 100% mutant kill rate, and >= 95% coverage.
- Record evidence and update runlog/review documentation.
