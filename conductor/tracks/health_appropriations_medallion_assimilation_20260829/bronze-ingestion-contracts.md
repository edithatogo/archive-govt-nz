# Phase 2.1 Bronze ingestion contract audit — 2026-09-07

Bounded implementation on `1f53a6e80873a99acc67c746fa6f1478b78b24aa` in an
independent worktree. The original Phase 2.1 test task remains `[~]`; Phase 2.4
is unchanged. No source-census state, live rights decision, publication, parent
checkout or global registry was changed. Full integration belongs to the parent.

## Audit before implementation

The retained “Bronze through Platinum checkpoint” in `evidence.md` describes
73 captured originals with WARC, donor reconstruction and a prior full gate.
It does not identify a fault-injected HTTP length test or durable interrupted
health-batch continuation test. The completed Phase 2.4 line is historical
checkpoint evidence, not proof of every unchecked Phase 2.1 contract.

| Named contract | Existing evidence reused | Added verification / exact limit |
| --- | --- | --- |
| Streaming / single pass | `tests/object_store/test_object_store.py`, `tests/bronze/test_multihash.py` | One-shot HTTP body with multi-chunk iteration; no second source consumption. HTTP still spools then reads into CAS; this is not a single disk-write pipeline. Donor import materializes Git payloads before chunking. |
| Expected length | Donor import/reconstruction rejects length mismatch | New short/overlong identity-encoded HTTP bodies below max_bytes failed red; fixed before CAS/WARC promotion. Empty/exact/no-header/gzip boundaries pass. Compressed wire-length verification is not implemented by this decoded-byte guard. |
| SHA-256/BLAKE3/CID | Existing known CID vectors and multihash chunk parity | Independent payload digests and decoded CID version/raw-codec/multihash bytes agree with the CAS receipt. CID is derived from SHA-256; not added to the capture receipt schema. |
| Dedup / atomicity | CAS corruption, invalid chunk, interruption and dedup tests | Reopened-store retry and fsync/spool/promotion fault injection preserve originals and leave no promoted partial object. |
| WARC linkage | Existing response/redaction fixtures | Parse actual WARC body and verify payload digest against captured CAS, plus complete WARC byte count/hash. Runner reuses source_id.warc; version preservation remains open below. |
| Resume / interruption | Generic capture retry, recovery inventory and donor reconstruction; later Silver resume tests are a different layer | New mid-body disconnect leaves no CAS/WARC; reopening store and retry works. Runner cancellation test demonstrates no durable per-resource continuation and repeated first request. |
| Changed / unchanged | Existing reconciliation decision tests | Decisions over real CAS digests preserve both historical/current byte versions; unchanged reuses object identity. |
| Restriction / withdrawal / tombstones | Existing resource-policy, batch-eligibility, source-policy and reconciliation tests | 403/410 never become successful captures. Withdrawal/disappearance/policy-change tombstones leave prior/current CAS objects intact. No rights status is inferred from a transport result. |
| Corrupt ZIP | Health appropriation `test_inventory.py` malformed-package/traversal/size tests | Existing tests rerun; no duplicate new ZIP implementation/test family. |
| Donor manifest | `test_donor.py` path/count/Git identity/archive/length tests | Rerun existing tests; completed adjacent donor-manifest task retained. |

Generic `tests/domains/test_health_bronze.py` covers COVID/Pae Ora, not fiscal
capture. `tools/capture_health_resources.py` is the actual fiscal capture path;
no pre-existing test referenced it. Its current hostname-based rights selection
was not promoted into a resource-specific decision by this work.

## Concrete unresolved acceptance

1. **Phase 2.1 “resume, interruption”; design `Retryable -> Fetching` and
   M-15/AC-13:** `_capture` retains results only in memory; `main` writes the
   manifest after the whole loop. The new offline test interrupts after the
   first resource and confirms that the next invocation requests it again.
   CAS dedup/retry is proved, durable per-resource batch continuation is not.
   Byte-range HTTP resume is explicitly rejected by existing capture tests;
   it is not silently substituted for this missing batch-resume proof.
2. **Phase 2.1 “WARC linkage”, M-04/S-01/AC-04; spec Bronze material HTTP
   context:** the runner uses `<source_id>.warc` for every observation. The
   cancellation/retry test confirms that a completed first WARC is overwritten
   on replay, even for the same CAS object. A prior manifest's WARC digest can
   therefore stop resolving. Versioned/non-overwriting WARC storage and durable
   recovery of its manifest linkage require an owning implementation slice.
3. **Phase 2.1 “expected-length mismatch”:** the new guard compares decoded
   bytes only for identity encoding. An encoded response's advertised wire
   length is not compared here. The gzip success test prevents the incorrect
   comparison of compressed length to decompressed length; it does not claim
   compressed-wire truncation detection by the application.
4. **M-18/AC-16:** the changed length guard is fully exercised and three seeded
   guard mutants are killed. The affected module reaches 153/154 lines and
   43/44 branches, not 100% overall. The sole remaining branch is the pre-existing
   redirect-loop exhaustion fallback (`129 -> 379`), unreachable with an ordinary
   validated nonnegative redirect bound because all last-iteration paths return
   or raise. No exclusion or threshold change was introduced. Parent still owns
   the full integrated checkpoint and classification of that defensive branch.

These are specific executable/source-contract gaps, not live rights or source
promotion gates. No broad completion claim is made from the new tests.

## Red, green and bounded validation

New test file: `tests/domains/health_appropriations/test_bronze_ingestion_contracts.py`
(23 cases). Production change: `src/archive_govt_nz/capture.py` only: compare
the final identity-encoded body length to Content-Length before promotion;
raise redacted `CaptureError("length_mismatch")`, retaining the attempt receipt
and existing temporary-file cleanup. The expected header value is bound to the
current attempt. No dependency or output schema changes.

Red: two `DID NOT RAISE CaptureError` failures for declared lengths 2 and 8
against a six-byte body. Existing code returned captured CAS/WARC results.
Green: both reject and leave no object/WARC/temp file. Additional no-network
tests cover real mid-body failure, fresh store instance retry, duration bounds,
fsync failure, storage failure, HTTP denials/retry status and changed validators.

First broad scoped coverage run: 117 tests passed but command exited 1 at
86.87% coverage. Added missing relevant negative paths. One intermediate test
edit displaced a WARC assertion and caused a NameError; corrected before final
validation. Final: **129 passed**, scoped coverage **98.99%**, exit 0 without
overriding the configured 95% gate. One ResourceWarning from an existing SQLite
test's unclosed connection was observed; no warning suppression was added.
Ruff lint/format and basedpyright pass for both changed Python files.

```sh
PYTHONPATH=src COVERAGE_FILE=build/health-bronze.coverage /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_bronze_ingestion_contracts.py tests/capture/test_capture.py tests/object_store/test_object_store.py tests/recovery/test_capture_recovery_integration.py tests/recovery/test_recovery.py tests/bronze/test_multihash.py tests/warc/test_warc.py tests/capture/test_capture_reconciliation.py tests/policy/test_resource_policy.py tests/capture/test_batch_eligibility.py tests/capture/test_run_capture_batch.py tests/policy/test_source_policy.py tests/domains/health_appropriations/test_inventory.py tests/domains/health_appropriations/test_donor.py --cov=archive_govt_nz.capture --cov-branch --cov-report=term-missing --cov-report=json:build/health-bronze-coverage.json -q
```

Three independent subprocesses compiled one in-memory source mutation each,
then ran the new file with `-k length_ -q -p no:cacheprovider`. Disabled mismatch
guard: 2 failures; inverted comparison: 4 failures; removed encoding guard:
1 failure. Each exited 1; no production source was edited for mutation testing.
Machine receipt: `bronze-ingestion-validation.json`.

Self-review: no private payloads/live traffic, no source eligibility changes,
no new publication authority; byte-count rejection occurs before promotion;
encoded and decoded lengths are not conflated. Existing parent/original files
are untouched. This is a bounded safe fix with explicit remaining Phase 2.1 work.

## Independent preceding follow-up review

Read-only `origin/main..1f53a6e8` review in the parent's checkout found no
actionable issue in the follow-up changes. Reviewed synthetic recovery
correction `ccdd40bf`, FOI reconciliation and HF track archival/evidence.
FOI report regeneration matched both checked-in files exactly. Seven primary
and two supplementary indexed assurance hashes matched; archived HF gate files
exist and the Prompt13 operational-proof digest matches its metadata pin.
Synthetic cycles remain explicitly tagged, top-level observed count is zero,
and real BLAKE3 is used. HF archival retains its separate Prompt13 continuation
boundary. These checks validate retained evidence, not fresh live HF access.
No parent writes or full harness were performed by this reviewer.
