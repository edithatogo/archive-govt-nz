# Review Report: Parliament archival streams

## Summary

The bounded public-report lane has manual remote proof; broader submission/advice, scheduling and full-archive acceptance remain incomplete.

## Verification Checks

- [ ] **Plan Compliance**: Partial — report discovery/capture/publication implemented; P1/P3 mixed-source qualification, P4 natural schedule/reconciliation and P5 expansion remain open.
- [x] **Style Compliance**: Pass — Ruff format/lint; whole-project type gate passed after correcting optional schema-version lookup.
- [x] **New Tests**: Yes — 74 synthetic contracts for source drift, integrity, public visibility, immutable provenance, bounded capture and independent recovery.
- [ ] **Test Coverage**: Partial — focused contracts pass; full suite aggregate coverage 97%; repository mutation stages passed; all supply-chain stages passed after exact synthetic-fixture correction. Four added Parliament policy mutants killed; no assertion of 100% policy-critical coverage.
- [x] **Test Results**: Passed tests — 8,423 passed, 14 capability skips; all remaining stages passed; secret scan resumed after exact synthetic-fixture correction. Focused suite 74 passed, strengthened provenance regression passed separately. Native report and metadata-only batches anonymously verified.

## Findings

### High — source access/reuse gates prevent broader acceptance

- **File**: `conductor/tracks/parliament_archive_streams_20261026/evidence.md`
- **Context**: Legacy robots denies crawling; submissions and most committee advice are outside the general reuse grant. The report pilot cannot satisfy the complete mixed business-item acceptance criterion.
- **Resolution**: Keep those lanes gated and parent/phase issues open; no rights bypass, private fallback or completion claim.

### Medium — natural schedule and historical reconciliation remain unproven

- **File**: `src/archive_govt_nz/parliament/worker.py`
- **Context**: Recent first-page windows and resumable offset history can miss late or shifted entries. A manual run does not prove recurrence; acquisition deadlines exclude publication time. Discovery/state overhead is not a qualified whole-root hard spool cap.
- **Resolution**: Retain explicit operational limits; do not claim complete coverage or unattended acceptance. Qualify ongoing scheduling, periodic full reconciliation and total-spool guard before scale-up.

### High — old bytes must retain their original metadata (fixed)

- **File**: `src/archive_govt_nz/parliament/pipeline.py`
- **Context**: Joining captures directly to the current record could relabel an old file with newer title metadata.
- **Resolution**: Immutable observation snapshots now bind source ID, URL, byte hash and record hash. A regression changes metadata and payloads, then asserts old/new titles against their exact hashes. Passed.

### Medium — unknown upload outcomes must not repeat mutations (fixed)

- **File**: `src/archive_govt_nz/parliament/publication.py`
- **Context**: A lost commit response could otherwise cause an unnecessary second write or overwrite.
- **Resolution**: Check the immutable remote namespace, download and compare every existing file, reject partial/conflicting state; use observed parent revision and one mutation at most. Synthetic recovery contracts passed.

Reviewed all new Parliament source modules, CLI entry point, schemas and synthetic tests iteratively, plus changes to the validation-schema registration. No secrets or source personal payloads added to Git; fixtures are fictional. Public report originals remain on Hugging Face with hash-bound eligibility assertions. The unfinished parent track must remain active, not archived.

## Follow-up metadata hardening review

44 native cards and four collection readbacks audited. Corrected stale zero counts, missing source ZIP description, licence/identity overclaims and unsafe table auto-detection. Maintained public card replacements are revision-conflict protected; original payloads and gates preserved. Publication regression tests cover maintained-card preservation, unknown counts and missing explicit-card failure before native writes. The full-suite snapshot mismatch was the expected reviewed metadata change; updated snapshot and eleven affected tests pass. Other assurance stages passed. Remaining hosted conversion acceptance and source acquisition blockers remain explicit; no incomplete track archived. See docs/huggingface-estate-hardening.md and versioned receipts.

Final P6 acceptance: all14 configured tabular datasets and41 first-row probes pass. Historical reader101/RNZ74 rows pass on isolated Python3.15.1. Registry/collection native readbacks and exact revisions retained. Public collection-ID scan findings are adjudicated only for the byte-identical reviewed receipt; 27 supply-chain tests, including changed/unrelated-file rejection, pass. Types pass. Native metadata setup is complete for the44-dataset scope; parent archival gates remain independent and active.

## Windows hosted-check follow-up

Repeated cancellation was diagnosed through native annotation as an aggregate30-minute job timeout, not a reported failing test. A single targeted rerun had the same outcome; no further blind rerun. Reviewed conditional Windows60-minute allowance, unchanged required commands and1200-second per-command gates,55-minute step ceiling, pipefail exit propagation and always-upload diagnostics. Actionlint and21 focused workflow/harness tests passed. Hosted outcome remains pending; no archive scaling or merge accepted.

## Native Windows execution remediation review

The60-minute run also timed out without Windows artifacts, so the earlier budget change was insufficient. Reviewed the owned-PID-only taskkill tree cleanup (absolute system executable, bounded30-second cleanup, finally kill parent), native PowerShell transcript/finalization and exact exit propagation. No gate removed, no allowance increased, no repeated blind retry. The precise stalled stage and Windows acceptance remain unknown.21 focused tests, Actionlint, PowerShell parser and strict types pass; hosted verification required before acquisition/merge.

## Review Report: Account reconciliation and Windows recovery — 27 October 2026

### Summary

Public metadata reconciliation is natively verified; the Windows fix preserves every gate and requires new hosted acceptance before delivery/capture.

### Verification Checks

- [x] **Plan Compliance**: Partial parent; current account scope and bounded diagnostic remediation implemented, external source gates retained.
- [x] **Style Compliance**: Ruff, selected strict types and Actionlint pass.
- [x] **New Tests**: Two real-child tests exercise retained output, nonzero exits and native owned-tree timeout cleanup; existing workflow contract updated.
- [x] **Test Coverage**: Full local suite 8429 passed, 14 capability skips; both snapshots, 83 schemas and 9 parity cases pass. The final cleanup refinement also passes both real-process tests.
- [x] **Test Results**: Full local harness passes, including every mutation stage, dependency audit, licence inventory, tracked-source secret scan and strict SBOM validation (118 components). Hosted Windows acceptance remains pending.

### Findings and resolution

- The retrieved native Windows log stops at an error for a 131073-character parameter-derived node ID. Short explicit IDs preserve the hostile robots input and all fail-closed assertions. The actual cause remains conditional until hosted acceptance.
- PowerShell transcript and runner pipes failed to retain usable artifacts after a stall. A regular-file child log and outer 2700-second watchdog now leave margin before the existing 55-minute step / 60-minute Windows job limits; per-stage 1200-second bounds and every required check are retained. Parent cleanup is in finally, and waiting is bounded.
- The registry distinguishes dataset and Space identities even where names coincide. All 76 public-metadata datasets are registered; five newly discovered private dataset identities are omitted. Updated registry schema, unique identities and canonical links validated; five files anonymously downloaded at 72040c9b4898ff389f795b0ea27fc0650272fd0d and hash-verified. Current 33 additional hosted config/split probes pass; no viewer rows or new private names are included in public Git receipts.

No track archive or source-completeness claim is appropriate while the parent source, hosted delivery and schedule gates remain open.

Hosted Linux follow-up: a newly materialized assurance receipt's explanatory status sentence was a candidate-scan false positive. Reproduced the exact finding locally on the integrated tree, reused the existing benign receipt pass-status convention, and retained scope separately. The affected stage and strict SBOM validation now pass; no detector policy or exemption changed. Hosted full acceptance is still required at the corrected head.

Supervisor refinement: child-log mirroring could itself block deadline enforcement on a stalled console. Removed the mirroring entirely: the supervisor waits with an OS-backed timeout, and complete child output remains in the independently saved artifact. The real-child deadline test allows five seconds of native startup margin without retries.

Final parameter review: Windows permits at most32767 characters in an environment variable, and installed pytest places the complete node ID in PYTEST_CURRENT_TEST. Collection inspection found a second ID of4194409 characters in the hostile API-response case. Added short IDs without changing its4194305-byte body; all8553 collected IDs now fit (maximum4186). The fresh full local harness passes all stages, and focused cases plus Actionlint pass after this ID-only/Windows-preflight change. Hosted acceptance remains required.

Native preflight exposed a portability issue in the new supervisor test import (tools namespace unavailable to the Windows console entry point). Applied the repository's established explicit importlib file loader. The exact console-entry-point preflight passes locally (11 passed, two genuine platform skips), with Ruff and strict typing passed. Production archival behavior is unchanged; require final hosted checks.

## Required hosted budget review fixes

Both unresolved P2 findings were valid and reproduced. Budget-limited files now remain pending for a fresh run, while genuine per-file violations remain failures. Discovery admits a page only with room for its original response, candidate/snapshot representations, bookkeeping and a complete SQLite rollback journal. The same spool bound reaches the worker and explicit CLI discovery; a full-spool deferral stops subsequent capture and packaging. Unadmitted pages do not advance cursors.

All80 affected Parliament tests pass, strict types and Ruff pass, and both new budget guard mutants are killed by the existing Medallion runner. Full repository and corrected-head hosted acceptance remain required before merge. No policy bypass or review-thread dismissal without a fix is authorised.

## P7 pre-delivery review — 27 October 2026

Reviewed durability ordering, shared ownership, unknown native outcomes, typed
projection, cancellation budgets, disk retirement and unchanged rights/card gates.
Fixed additional findings: candidate evidence must survive cold restore inside
immutable snapshots; package restore must hydrate exact object hardlinks before
publication; interrupted work must retain its originating run/attempt; publication
proof cannot be inferred from unrelated successful jobs; legacy CLI roots must
consult shared authority before source access. Dedicated tests cover these cases.
The original SSD is never eligible for automatic scratch retirement.

Remaining acceptance is explicit: complete local assurance, green required hosted
checks, merged code, native HF binding, full anonymous cold restore and actual
cancellation/resumption before enable. No deployment or source-completeness claim.

Additional review fixes: deterministically close SQLite connections during long
continuations; recover an unknown first bootstrap pointer only when the frozen
SSD marker matches its exact owner; allow read-only cold verification while
paused; expose explicit resume without changing enable/authority; retain failed
reports as held before another acquisition. SDK fixtures enforce immutable
namespace, anonymous pinned reads, no permission-as-absence behavior and stable
diagnostics. Exact native execution and bounded artifact ZIP contracts are tested.
Thirty-five hosted tests pass; four new modules have84.67% branch-aware coverage.
Full revised-candidate and native hosted acceptance are still required.

Final startup finding fixed: a disabled scheduler now returns before attempting
to load an incomplete bootstrap snapshot. The exact race failed red and passed
after the change. Full reviewed assurance had passed8581 tests and all gates;
final-commit assurance and hosted acceptance follow. Public acquisition remains
disabled throughout bootstrap and pilot qualification.

PR795 required review fixes are valid and reproduced by three red tests.
Terminal proof is now bound to the current owner; discovery has a total remaining
timeout; bootstrap holds the existing local writer lock before freezing the SSD
and through checkpoint acceptance. Isolated regression tests pass. The operator
CLI now resides in the measured package and has authority/error/cancellation
tests. Codecov's79.50% patch result is retained as first-failure evidence;
the80% requirement is unchanged. Corrected-head hosted acceptance is pending.

Ingress and accounting self-review: applied the existing report PDF qualification
before public object staging, retaining rejected bytes privately and exact hash
evidence publicly. Charged failed-read acquisition time before saving/retrying.
Both defects have isolated red/green regressions; ten affected tests, strict types
and Ruff pass. Final-head complete assurance is required before any native write.
