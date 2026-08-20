# Run log

- 2026-08-20T11:12:00Z: Created local branch
  `codex/legislation-cli-correction` at global CLI head `2c86d90`. Audit found
  duplicated sync transport with a fabricated default work and fixed timestamp,
  flat-CAS counting, record-count denominators, absent change state reported as
  observed, manifest-only publication reported staged, and token-only remote
  publication reported verified. No push, PR, merge, or live action occurred.
- 2026-08-20T11:17:00Z: Added seven adversarial contract tests. The red run
  failed all seven against the merged CLI: absent changes returned success;
  coverage used manifested records as its own denominator; a flat garbage CAS
  returned operational; unknown `nzlc` input silently invoked status; empty
  sync constructed state and returned success; a corrupt manifest root
  validated; and manifest/token publication evidence returned affirmative
  states. This is the expected red baseline.
- 2026-08-20T11:28:00Z: Routed sync through `LegislationArchiveService`, made
  selection and batch identity explicit, authenticated manifest roots and
  discovered-inventory coverage, required linked manifest/checkpoint/sharded
  CAS state for operational status, removed token-only verification, and made
  absent change evidence and unknown compatibility actions non-zero. Focused
  CLI suite passed 32 tests with Ruff and BasedPyright green. Replay linkage,
  expanded adversarial coverage, full harness, and review remain pending.
- 2026-08-20T12:05:00Z: Committed authenticated state projections at
  `c92850b`. `cli_state.py` requires rooted cumulative manifest and discovered
  inventory, validates every v2 record, links checkpoint roots and counters,
  streams sharded CAS verification, and compares manifest SHA-256, BLAKE3, and
  byte counts. Critical module coverage is 100% line and branch.
- 2026-08-20T12:05:00Z: Focused CLI suite passed 43 tests. Affected service,
  model, object-store, CLI, and contract suite passed 119 tests. Contract
  validation passed all 15 contracts.
- 2026-08-20T12:05:00Z: Full harness passed lock, format, lint, typing, 753
  tests at 95.64% overall coverage, schemas, mutations, hygiene, and CAS
  benchmark. The required OSV dependency audit then timed out. Two isolated
  retries also failed at the OSV transport boundary (timeout, then TLS EOF,
  then timeout). The alternate PyPI vulnerability service reported no known
  vulnerabilities. Licence, secret, and SBOM lanes passed separately. The OSV
  harness lane remains pending and is not represented as green.
- 2026-08-20T12:05:00Z: Restored harness-generated evidence timestamps because
  this local branch does not claim a refreshed operational evaluation. No push,
  PR, merge, live batch, publication, or donor archival occurred.
- 2026-08-20T15:10:00Z: Rebased onto global CLI head `5ed8be0` and amended
  service head `51fc8a7`. The first exact harness exposed two legacy CLI tests
  that assumed work IDs manufactured acquisition targets. Updated those tests
  to return canonical discovery graphs; 20 focused tests then passed.
- 2026-08-20T15:10:00Z: The exact corrected stack passed the full locked harness
  with 756 tests, 95.62% branch-aware coverage, and every repository gate. No
  push, PR, merge, source fetch, publication, rights action, or live operation
  occurred.
- 2026-08-20T16:05:00Z: Global CLI PR #157 was squash-merged as `138b17f`.
  Rebased this successor onto that exact `origin/main`; all seven commits
  replayed without conflict. The full locked harness passed again with 756
  tests, 95.62% branch-aware coverage, and all schema, mutation, hygiene,
  benchmark, dependency audit, licence, secret, and SBOM gates green. Generated
  timestamp and donor-snapshot churn was restored. Publication, rights, live
  operation, recovery, cutover, and donor archival remain gated.
- 2026-08-20T21:15:00Z: PR #158 merged as `bc5acda` after the required quality,
  workflow-policy, and CodeQL checks passed. A non-required Codecov patch check
  then appeared with 84.44% against a 94.88% target. Paused the MCP sequence and
  added adversarial coverage for every uncovered changed source line at
  `fb62c84`. The full harness passed 762 tests at 96.12% overall coverage and
  all remaining gates; a coverage-JSON audit against the original PR #158
  source diff found 180/180 executable changed lines hit. Generated timestamp
  and donor-snapshot churn was restored and excluded.
