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
