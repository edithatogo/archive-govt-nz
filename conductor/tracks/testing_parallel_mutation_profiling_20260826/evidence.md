# Evidence

## Evidence boundary

Evidence in this track is repository-local unless a hosted receipt is linked
explicitly. No publication, release, credential, rights, or external approval
gate is required for the testing configuration task.

## Task evidence

### REQ-PAR-001 xdist configuration

- Status: repository implementation committed as `05add7a`.
- The repository gate accepts an explicit worker count (`auto`, `logical`, or
  a positive integer) and one allowlisted scheduler; unsafe compound values
  fail before process execution.
- Parallel runs use xdist `loadscope` by default while the ordinary harness
  remains serial and deterministic.
- Focused suite: 10 passed; Ruff and basedpyright passed.
- Full 1,100+ test parallel execution is a separate pending evidence task.

### REQ-PAR-001 parallel verification

- The full suite passed through xdist `loadscope` with 10 workers: 1,163 tests
  in 90.31 seconds at 95.32% coverage.
- No isolation or race failure was observed across temporary files, DuckDB,
  snapshot, coverage, or subprocess-backed tests.
- Result is local-only and comparable only to runs on this host.

### REQ-PROP-001 property suites

- Ten Hypothesis properties cover URN parser/validator agreement, streaming
  hash identity, CIDv1 envelope correctness, Arrow/Croissant schema parity,
  statutory citation determinism/deduplication, and false-positive resistance.
- Focused property files, Ruff, and basedpyright passed.
- Commits: `007e68e`, `45db8ed`, `0b444f6`, and `c5930c0`.

### REQ-PROF-001 Scalene harness

- Repository harness commit: `e3b9875`; focused tests: `0183c95`.
- Deterministic workload: 64 Bronze records, 64 Silver rows, and 140,800 bytes
  aggregated through Gold DuckDB.
- Scalene 2.3.0 passed in 9.96 seconds with a 15.60 MB peak footprint.
- Canonical local receipt: `build/profiling-scalene.json`; raw profile SHA-256
  `e843dd11eea71e364e3a78c8ccbe3084ed5de5dfd377fdaada06a56631405210`.
- Receipt contains CPU, native allocation, memory, and copy-rate metric families
  and no absolute path. The raw profile remains an ignored local artefact.

### REQ-GATE-001 assurance integration

- `tools/check.py --include-heavy` exposes bounded `gremlins` and
  `profile-scalene` stages without changing the default fast-first gate.
- `tools/check.py --pytest-workers auto --pytest-distribution loadscope`
  exposes the independently verified parallel lane.
- Focused assurance/profiling suite: 16 passed; Ruff, basedpyright and hygiene
  passed. Commits: `d715c47` and `caf12ae`.

### Final validation and review

- Required `./scripts/validate.sh` passed after wrapper correction `9fd2747`:
  1,180 tests in 110.04 seconds at 95.33% coverage; 30 schemas; 9/9 parity;
  all repository mutation lanes; hygiene; CAS 286.12 MB/s; audit, licences,
  tracked-source secret scan, and 102-component SBOM.
- Dedicated pytest-gremlins lane passed 42/42 after target-test bounding
  (`05e8a6f`). Dedicated Scalene lane passed.
- Review fix `51a2554` prevents stale raw-profile reuse and emits atomic,
  path-redacted failure receipts for every bounded failure class.
- All evidence remains local-only; hosted CI, merge, release, or publication
  are not claimed.
- Post-review `./scripts/validate.sh` passed after `51a2554`: 1,182 tests in
  111.05 seconds at 95.33% coverage, with every subsequent schema, parity,
  mutation, hygiene, CAS, audit, licence, secret, and SBOM stage green.

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

### Phase 1 Review Fixes

- Focused supply-chain contracts: 6 passed.
- Ruff and basedpyright: passed.
- Source secret scan: passed against Git-tracked files; generated and ignored
  coverage artefacts are outside traversal, with explicit path exclusions as
  defense in depth.
- CycloneDX 1.6 SBOM: validated with 102 components.
- Type analysis is explicitly limited to repository code surfaces (`src`,
  `tools`, and `tests`) and runs with four workers; the exact full command
  passed in 3:12 with 0 errors, warnings, or notes.
- Assurance harness contracts: 8 passed.
- Post-fix `./scripts/validate.sh` passed on 2026-08-29: 1,161 tests at 95.36%
  coverage, 30 schemas, 9/9 parity checks, all mutation lanes, hygiene, CAS
  throughput, dependency audit, licence inventory, tracked-source secret scan,
  and a validated 102-component CycloneDX SBOM.
- Evidence is local-only; hosted execution is not claimed.

### REQ-MUT-004 runner tests

- Status: repository implementation committed as `af9aa2e`.
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
