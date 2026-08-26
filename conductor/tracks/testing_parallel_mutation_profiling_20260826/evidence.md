# Evidence

## Evidence boundary

Evidence in this track is repository-local unless a hosted receipt is linked
explicitly. No publication, release, credential, rights, or external approval
gate is required for the testing configuration task.

## Task evidence

### REQ-MUT-001 and REQ-MUT-002

- Status: repository implementation complete; functional commit pending.
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
