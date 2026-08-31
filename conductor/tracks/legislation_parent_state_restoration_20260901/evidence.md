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

## Local closeout

Native validation passed at commit `834f79446ec7be1f625f0e20bb474ae066a49807`, integrated from main `f41ef9b984c15dc84a9afa3e39236388bfcf2197`: 3,580 tests, five warnings, 97.20% combined coverage; all native mutation, schema, parity and supply-chain stages passed. Scoped restoration tests: 93 passed, 320/320 statements and 60/60 branches covered; 32/32 explicit integrity mutants killed. Four restoration schema definitions and representative runtime documents are checked in the focused suite.

Receipt: `evidence/migrations/corpus-legislation-nz/parent-state-restoration/local-validation.json`

SHA-256: `b0618508d77c7a93fd6a24d485d0fe25b13e16d5c047c4b82bbcb1dc1fecaa49`

The receipt inventories exact source, test, schema, log and security hashes, and preserves prior failed attempts. Whole-repository actionlint reports two unchanged SC2086 diagnostics outside legislation; scoped actionlint passes. Aggregate source branch coverage remains below 95%, as already handed off in [issue #299](https://github.com/edithatogo/archive-govt-nz/issues/299#issuecomment-5480374548); no source code or thresholds in that aggregate were changed by this issue. The new critical helper is fully covered.

PR [#317](https://github.com/edithatogo/archive-govt-nz/pull/317) is the sole delivery PR. Final hosted checks and merge/readback are recorded separately on issue #312; local validation is not a remote restoration or publication claim.
