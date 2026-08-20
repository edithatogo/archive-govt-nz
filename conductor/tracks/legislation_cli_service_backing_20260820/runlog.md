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
