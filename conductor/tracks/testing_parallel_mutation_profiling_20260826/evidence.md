# Evidence

## Evidence boundary

Evidence in this track is repository-local unless a hosted receipt is linked
explicitly. No publication, release, credential, rights, or external approval
gate is required for the testing configuration task.

## Task evidence

### REQ-MUT-001 and REQ-MUT-002

- Status: repository implementation committed as `ab4ed66`.
- `pytest-gremlins` 1.9.0 is locked to the compatible `<2` major series.
- Plugin-native configuration fixes mutation operators and targets, emits
  console and JSON reports, enables automatic parallel workers and incremental
  caching, retains coverage-guided selection, and permits no pardons.
- Focused contract test: 1 passed.
- Ruff, basedpyright, and lock checks: passed.
- Dependency audit: no known vulnerabilities; receipt SHA-256
  `da89864c80f79300ef46de58a55790e43f68f0fc9f91630e978d991d06d94eee`.
- Licence inventory: passed; `pytest-gremlins` 1.9.0 reports MIT License;
  receipt SHA-256
  `c1674e9824231159e503ecc7d5261af7a3e31326a434e580b1b538908787a521`.
- Task-scoped secret scan: zero findings. The repository-wide scan was stopped
  because generated coverage files made its scope unbounded; no clean
  whole-repository secret-scan claim is made.
- Evidence is local-only; no hosted execution or publication is claimed.

### REQ-MUT-004 runner tests

- Status: implementation ready for commit; commit identity is recorded in the
  plan after creation.
- Focused suite: 28 passed.
- Targeted runner coverage: 100% line and branch coverage (139 statements,
  30 branches).
- Ruff format/check and basedpyright: passed.
- Missing targets and all plugin-report/process failure modes emit bounded,
  machine-readable failures; raw subprocess output is not retained.
- Full harness evidence is partial: all stages through licences passed, while
  the secret scan was interrupted because generated `.coverage.*` shards were
  not excluded. A Review Fixes task owns that repository-level defect.
- Evidence is local-only; no hosted execution or publication is claimed.

### REQ-MUT-003 runner

- Status: repository implementation committed as `86dbbed`.
- The runner validates target existence and the plugin JSON envelope, rejects
  missing, malformed, stale, empty, surviving, errored, timed-out, or pardoned
  outcomes, and writes its bounded receipt atomically.
- Raw subprocess output is excluded; only SHA-256 digests are retained.
- Fresh-cache mutation result: 42/42 zapped, 100%, zero survivors, errors,
  timeouts, or pardons.
- Plugin report SHA-256:
  `1599db157402b143d53df58f26701f46535e4300e8879bea17e2aee12a39b046`.
- Scope is the Medallion schema/NLP export boundary and completed within the
  repository's 300-second gate. A five-file target set exceeded that bound and
  was rejected rather than weakening the timeout.
- Evidence is local-only; no hosted execution or publication is claimed.
