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

## Superseding final-review validation

The initial receipt above remains immutable. Final review found and fixed nested conditional-cache structure acceptance and ZIP original-name normalization. The failed five-case checkpoint lane and synthetic NUL-member reproduction remain hashed in the new receipt.

Final native validation passed at `1a91be205852beffb96d23f7bb3ca68c83eccfcb`, integrating main `2c7a59913a77badcaece3a87366ee50a4a97c49d`: 4,012 tests, 8 warnings, 97.29% combined coverage; native schemas, parity, mutation gates and supply-chain stages passed. The source and dependencies match the earlier final functional checkpoint `f0be1fefaf68b12ee1d6154d0c70cd3e6a5c70fe` exactly. Focused tests: 99 passed; 323/323 statements and 60/60 branches covered; all 34 integrity mutants killed.

Superseding receipt: `evidence/migrations/corpus-legislation-nz/parent-state-restoration/local-validation-v2.json`

SHA-256: `82f3766f91aa57d181568c6541165e4314274db9bf9562c69cd15895ba2e5343`

Aggregate branch-only coverage is 94.43105%, distinct from native combined coverage and the changed helper's 100%. The existing aggregate handoff and two unrelated SC2086 diagnostics remain; no thresholds or unrelated code were changed. Final metadata/evidence-head hosted checks and guarded merge/readback remain separately recorded on issue #312. No live state restoration or publication was executed.

## Prompt 08/12 integration addendum

Issue #359 supersedes the compatibility limitation without rewriting the earlier
receipts. New seals and continuations require the Prompt 12 v3 accounting
receipt. Explicit legacy adoption continues to read v2, but cannot seal it as a
new continuation. The validator binds v3 execution identity, manifest and
checkpoint roots, record count, and CAS count.

Final local validation: 4,549 tests passed with 97.50% combined coverage; 48
schemas and 38 representative documents passed; parity, dependency, licence,
secret and SBOM gates passed. The final-byte mutation runs killed 37/37
parent-state and 26/26 durable-state mutants. Receipt:
`evidence/migrations/corpus-legislation-nz/parent-state-restoration/integration-v3-validation.json`.
No live restoration, harvest, publication or external mutation was performed.
