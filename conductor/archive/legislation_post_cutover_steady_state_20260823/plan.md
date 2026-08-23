# Implementation Plan: Legislation Post-Cutover Production Steady-State Operations [COMPLETED]

### Phase 1: Contract Promotion to Version 2.0.0 [COMPLETED]
- [x] Task: Version `contracts/schedule/legislation-archive-slo.contract.yaml` to `2.0.0`.
- [x] Task: Update `evidence/migrations/corpus-legislation-nz/operational-gate-authorization.json` to record steady-state authorization.

### Phase 2: Source-Set Configuration & Workflow Crons [COMPLETED]
- [x] Task: Update `config/source-sets/legislation.yml` to `execution_mode: "scheduled_and_dispatch"` and `schedule: "weekly"`.
- [x] Task: Add weekly cron (`0 18 * * 0`) to `.github/workflows/scheduled-legislation-harvest.yml`.
- [x] Task: Add monthly cron (`0 6 1 * *`) to `.github/workflows/monthly-legislation-reconciliation.yml`.

### Phase 3: Static Controls & Independent Completion Evaluation [COMPLETED]
- [x] Task: Update `tests/tools/test_legislation_workflow_integrity.py` to enforce the new steady-state contract invariants.
- [x] Task: Run `tools/validate_contracts.py` on all contracts.
- [x] Task: Run `tools/evaluate_legislation_completion.py` to regenerate `final-adversarial-verification.json`.
- [x] Task: Verify clean completion status on `main`.
