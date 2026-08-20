# Run log

- 2026-08-20T06:35:25Z: Reconciled live state. PRs #150-#155 were already
  merged; further merges frozen. Donor repository was found archived and was
  restored to unarchived status under the explicit operator directive.
- 2026-08-20T06:35:25Z: Started corrective branch
  `codex/legislation-service-correction` from current clean `main`.
- 2026-08-20T06:38:26Z: Red phase confirmed with 10 expected failures across
  coverage denominator, discovery identity, adapter conditional capture,
  cumulative state, and reconciliation defaults; 26 focused tests passed.
- 2026-08-20T06:47:14Z: Green phase passed 37 focused tests. Focused Ruff and
  BasedPyright checks passed with zero findings. Remaining fixed 33,693 use is
  isolated to the separately gated merged parity generator; historical donor
  narrative is retained as provenance.
- 2026-08-20T06:49:00Z: Direct `./scripts/validate.sh` invocation could not
  start because the tracked file mode is `100644`. Executed its exact command
  through `bash scripts/validate.sh`; the full locked harness passed 642 tests
  at 95.21% coverage plus schemas, mutation, hygiene, benchmark, audit,
  licence, secrets, and SBOM gates.
- 2026-08-20T07:03:51Z: Applied review fixes for cold-304 integrity,
  fail-closed rights disposition, and manifest hash aliases. Focused suite
  passed 38 tests; the complete locked harness then passed 643 tests at 95.22%
  coverage and all remaining gates.
- 2026-08-20T07:05:41Z: Pushed commit `e70a70d` and opened PR #156 against
  unchanged current `main` (`3b38d10`). The PR is intentionally unmerged under
  the active freeze.
- 2026-08-20T08:00:05Z: Reopened the track for a second exact-head review-fix
  phase. Negative controls exposed acceptance of malformed manifest/checkpoint
  state, identity collisions, unauthenticated discovered denominators, partial
  batches marked complete, and explicit targets unable to prove no-change.
- 2026-08-20T08:58:03Z: Review fixes passed 83 affected tests. The exact locked
  harness then passed 690 tests at 95.79% coverage plus every schema, mutation,
  hygiene, benchmark, audit, licence, secrets, and SBOM gate. Functional commit
  `84ca569` is ready for hosted validation; PR #156 remains unmerged.
- 2026-08-20T09:10:21Z: A third exact-head audit found that malformed target
  graphs could still contain an empty work identity or duplicate supplied
  expression/manifestation identities. Red controls reproduced all three
  acceptance paths before the pre-acquisition validator was hardened.
- 2026-08-20T09:16:49Z: Review-fix phase III passed 86 affected tests. The
  exact locked harness passed 693 tests at 95.76% coverage and all remaining
  repository gates. Functional commit `84d8562` is ready for hosted validation;
  PR #156 remains unmerged.
