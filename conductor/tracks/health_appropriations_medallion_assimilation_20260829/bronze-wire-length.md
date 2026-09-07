# Phase 2.1 — encoded response-body length contract

Local-only follow-up after process-recovery commit
`d90e878e0bf57015d2ef1996d95844ae78fc9f9a`. No live source request, parent edit,
full harness, dependency, rights, census or Phase 3 change.

## Semantics reviewed before implementation

The installed, pinned HTTPX 0.28.1 implementation in `_models.py` increments
`num_bytes_downloaded` on each raw transport-body chunk in `aiter_raw`, before
`aiter_bytes` invokes its content decoder. `Content-Length` is therefore
comparable with that counter for a newly consumed encoded stream, not with the
number of decoded bytes yielded to CAS. Identity responses continue to use the
directly observed payload count. Existing decoded size/decompression bounds,
timeout, temporary cleanup, hashing, CAS promotion and WARC behavior are retained.

HTTPX's `Response(content=...)` constructor preloads/decodes content and then
resets its raw counter to zero. A consumed response bypasses the raw iterator.
An advertised length on an already-consumed encoded response now fails closed
as `wire_length_unverifiable`, even if a preceding consumer may have measured
it. There is no fallback to decoded size or an assumed encoded count. Failure
has a redacted attempt outcome and occurs before CAS/WARC promotion.

For a newly consumed encoded stream, the final raw transport-body count must
equal the advertised length, otherwise `length_mismatch` is raised before
promotion. No second consumption, raw buffering or private HTTPX API is used.
Absent `Content-Length` means no exact-length assertion can be made; existing
bounded capture semantics remain. The existing CAS and WARC body remains the
decoded representation. This change does not promise raw-wire preservation,
TLS/socket framing measurement, bytes outside HTTP framing, complete gzip codec
conformance, or authentic source content merely because lengths agree.

## TDD, properties and negative paths

Three initial red tests returned successful captures instead of rejecting:
complete gzip with an advertised length one byte shorter/longer, and a
prebuffered encoded response without observable raw-byte accounting.

Eleven new executable cases cover those failures, gzip/deflate/stacked decoder
counts with/without length, a truncated gzip trailer despite decoded payload
availability, and a 20-example arbitrary-bytes/chunk-size roundtrip property
(including empty payload). They exercise the real HTTPX decoders using a
one-shot MockTransport body, not a fake counter. Rejection checks no promoted
CAS/WARC and no leftover capture spool. Existing identity/decompression tests
are rerun unchanged.

Final affected suite: **161 passed**, capture coverage **99.02%** (158/159 lines,
45/46 branches). The new code is covered; only the pre-existing unreachable
valid-config redirect-loop fallback remains uncovered. No coverage exclusion,
threshold relaxation or assertion weakening was introduced. One existing
SQLite ResourceWarning was observed in the affected suite and not suppressed.
Ruff check/format and basedpyright pass.

Four independent in-memory mutants are caught by tests: decoded count instead
of encoded count (4 failures), skipping encoded comparison (3), skipping
observability rejection (1), inverted length comparison (7). Two initial
mutation substitutions did not match Ruff's multiline formatting; those were
runner setup failures, not kills, and were corrected before these results.
During test development an incorrect receipt attribute and a misplaced WARC
assertion were fixed; neither was a production failure or a weakened check.

```sh
PYTHONPATH=src COVERAGE_FILE=build/health-wire.coverage /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_capture_wire_length.py tests/domains/health_appropriations/test_capture_process_recovery.py tests/domains/health_appropriations/test_capture_checkpoint.py tests/domains/health_appropriations/test_bronze_ingestion_contracts.py tests/capture/test_capture.py tests/object_store/test_object_store.py tests/recovery/test_capture_recovery_integration.py tests/recovery/test_recovery.py tests/bronze/test_multihash.py tests/warc/test_warc.py tests/capture/test_capture_reconciliation.py tests/policy/test_resource_policy.py tests/capture/test_batch_eligibility.py tests/capture/test_run_capture_batch.py tests/policy/test_source_policy.py tests/domains/health_appropriations/test_inventory.py tests/domains/health_appropriations/test_donor.py --cov=archive_govt_nz.capture --cov-branch --cov-report=term-missing --cov-report=json:build/health-wire-coverage.json -q
```

Self-review: the two requested missing semantic slices now have executable
acceptance. All named Phase 2.1 behaviors have the shared/Health evidence mapped
by this and the preceding audits. Phase 2.1 is not blanket-completed: M-18/AC-16
still requires resolution/classification of the defensive capture fallback's
critical coverage, and the parent-owned coherent full assurance checkpoint.
These remaining requirements are not source qualification or rights promotion.
