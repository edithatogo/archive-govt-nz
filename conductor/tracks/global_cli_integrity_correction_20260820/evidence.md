# Evidence

- Independent review of merged PR #150: ASW rejected at merge commit
  `fefa36d`.
- Local successor base: `51fc8a7`, the exact green head of open PR #156.
- Functional correction commit after rebase: `ed31c24`.
- Red evidence: 11 of 11 adversarial tests failed against the inherited PR #150
  implementation before the correction.
- Focused validation: Ruff passed, BasedPyright reported zero errors and zero
  warnings, and 103 affected tests passed.
- Full validation: `bash scripts/validate.sh` passed with 733 tests and 95.87%
  branch-aware coverage. `cli_integrity.py` reached 100% line and branch
  coverage. Schema, mutation, hygiene, CAS benchmark, audit, licence, secrets,
  and SBOM gates passed.
- Documentation review fix after rebase: `9617bd7`
  removes unsupported command grammar and operational claims from `README.md`,
  `docs/operations/runbook.md`, and the donor interface map. The existing
  migration contract test now rejects regression to PR #150 grammar, a false
  archived-donor claim, and production-harvest wording for the unconfigured
  capture route.
- Post-fix validation: 67 targeted tests passed, followed by the complete locked
  harness with 733 tests and 95.87% branch-aware coverage. All remaining harness
  gates passed. Evidence-generator timestamp and live-snapshot churn was
  excluded from the commit.
- Final CAS boundary correction after rebase: `eb56ead` makes store construction explicitly
  non-creating for replay verification and rejects `cas/sha256` symlinks before
  traversal. Red evidence was two expected test failures; green evidence was 52
  focused tests with 100% line/branch coverage for `cli_integrity.py`.
- Final code-phase harness: 735 tests passed at 95.88% branch-aware coverage;
  all remaining repository gates passed. README follow-up `2694c17` avoids a
  volatile exact test count and passed the migration documentation tests plus
  repository formatting and lint checks.
- No global CLI successor PR has been opened.
- Post-rebase locked validation against service head `51fc8a7`: 738 tests
  passed at 95.86% branch-aware coverage; all remaining repository gates passed.
- Publication authority, redistribution rights, and donor archival remain
  pending.
