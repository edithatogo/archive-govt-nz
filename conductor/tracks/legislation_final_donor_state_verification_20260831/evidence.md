# Evidence

Evidence directory: `evidence/migrations/corpus-legislation-nz/final-donor-state/`.

- `acquisition.json`, `github-metadata.json`, `expectations.json`: authenticated metadata and independently audited pins; donor archived.
- `verification-01/`: retained failed verifier attempt, explained by `verifier-correction.json`.
- `verification-02/`: passed operational-state receipt, report, all-file inventory and SHA256SUMS. Observed 500/500/500/500, no mismatches.
- `quarantine-readback.json`: independent local readback of 511 files and outer ZIP; read-only content-addressed input.
- `parent-run-readback.json`: parent run metadata only, not parent payload recovery.
- `mutation-01.json`: 10/10 named invariant bypass mutants killed by assertion failures; baseline focused suite 102 passed at 100% line/branch coverage.
- `development-log-hashes.json`: retained focused/typing/mutation attempt hashes.
- `full-validation-handoff.json`: full harness failed (124); pytest 2281 passed, 3 failed, 96.90% overall coverage. Isolated recheck 2 passed, 1 unchanged acceptance-check timeout failed.
- `workflow-lint-handoff.json`: two SC2086 findings independently reproduced from unchanged baseline workflow bytes; no suppression or out-of-scope edits.
- `README.md`: exact package/receipt hashes, reusable invocation and Prompt 04 boundaries.

Corpus bytes remain exclusively in external quarantine. Full validation and workflow lint are not green; issue completion and merge readiness are not claimed. Hosted observation is recorded separately after PR creation.
