# Phase 2.1 — process-death ownership recovery

Follow-up to `3daedf4c`; local-only and isolated. The fiscal runner previously
used an empty directory lock and could not distinguish a dead owner from a live
one. PID existence/age-based deletion would not safely resolve that ambiguity.

The runner now holds a standard-library SQLite `BEGIN EXCLUSIVE` transaction
at `<manifest>.lock` for the entire capture. Zero lock timeout fails closed
against an active owner. Closing the connection or process death releases OS
ownership. The lock file is never unlinked, replaced or vacuumed by the runner;
all cooperating writers keep using the same file. No new dependency, lock
expiry heuristic, PID reuse assumption or automatic deletion was introduced.
Existing legacy directory locks still require ownership review and are never
removed automatically. This compatibility boundary is not a stale lock created
by the new implementation. Use a local filesystem supporting SQLite locking;
network filesystems and hostile concurrent path replacement are not qualified.

## Executable evidence

`test_capture_process_recovery.py` starts the actual runner in a subprocess,
with only the HTTP boundary replaced by deterministic local CAS/WARC writes.
After the first durable checkpoint, the second capture announces readiness and
blocks. A competing explicit resume fails without a request. The test kills
the owning process, waits for termination, then resumes the same manifest.
Only the second resource is requested; the first receipt/WARC is unchanged.
Another resume is idempotent and the persistent lock file identity is retained.
Every subprocess read/wait is bounded to ten seconds and cleanup kills only the
test-owned process. No external requests occur.

Red: post-kill resume raised `FileExistsError` on the old directory lock.
Green: 44 focused tests pass. Runner coverage is 141/141 lines and 32/32
branches. Ruff check/format and basedpyright pass after fixing one import-order
finding. Three independent in-memory mutations (deferred lock, omitted lock,
omitted legacy guard) each cause one test failure. The actual subprocess uses
unmodified source; the mutated competing/resuming runner is checked against it.

```sh
PYTHONPATH=src COVERAGE_FILE=build/health-process.coverage /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m coverage run --branch --source=tools -m pytest tests/domains/health_appropriations/test_capture_process_recovery.py tests/domains/health_appropriations/test_capture_checkpoint.py tests/domains/health_appropriations/test_bronze_ingestion_contracts.py -q
COVERAGE_FILE=build/health-process.coverage /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m coverage report --include='*/tools/capture_health_resources.py' --show-missing --fail-under=95
```

Self-review: process-death resume now satisfies the previously missing bounded
contract without bypassing retained fixity verification. Power-loss filesystem
durability, automatic orphan adoption and legacy directory reclamation are not
claimed. Phase 2.1 remains partial for compressed-wire length verification and
the separately documented capture fallback coverage/integrated assurance gate.
No census, rights, global registry, parent, Phase 3 or full-harness changes.
