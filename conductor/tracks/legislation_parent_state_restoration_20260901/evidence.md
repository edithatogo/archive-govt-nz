# Evidence

## Restoration audit

- `scheduled-legislation-harvest.yml`: latest-run discovery, ignored download failure and implicit empty bootstrap. Replace restoration only, preserve discovery inputs and cadence.
- `monthly-legislation-reconciliation.yml`: latest-run discovery and direct extraction to working state. Replace with pinned verification; no reconciliation execution.
- `quarterly-legislation-recovery.yml`: selected run alone and direct extraction. Replace with the same pinned verifier; do not dispatch recovery.
- `tools/run_legislation_harvest.py`: acquires into caller-selected state, no remote restoration. Workflow must verify before invoking it and seal only after success.
- `tools/run_legislation_reconciliation.py`, `tools/run_legislation_recovery_drill.py`: independently authenticate already local linked state; no remote download. Preserve execution semantics.
- `tools/verify_final_donor_state.py`, `tools/merge_legislation_states.py`: bounded offline verification / separately scoped merge. Reuse pure verification helpers only, never execute merge.
- `tools/verify_operational_continuity_and_recovery.py`: synthetic local checkpoint rehearsal; not an Actions restoration ingress. No changes.

Validation and delivery results are pending. No source access, state restoration or recovery execution is claimed.
