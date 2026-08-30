# Evidence

## Read-only run verification — 2026-08-30

Commit `d25fd8d` adds separate hash-pinned CLI/MCP verification. Both live
interfaces verified the retained raw run and returned the same receipt, with
no normalization or file creation. All 63 focused/interface tests pass with
100% critical line/branch coverage; all 82 explicitly unfiltered mutants are
killed without pardons. The exact pinned manifest remains
`da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.

Final full harness exits zero: 1,459 tests, 95.92% coverage, eight warnings,
32 schemas, 22 representative documents, 9/9 parity and all mutation and
supply-chain gates, including a validated 110-component SBOM. No original,
derivative or HF bytes changed. Hosted checks and merge remain separate.

## Original-workbook orchestration — 2026-08-30

Commit `578235c` provides typed read-only preflight and explicit four-stage
raw-workbook rebuilding from the pinned donor manifest and Bronze CAS.
Two live runs match all 18 files byte for byte; complete reuse reverified
sources and outputs. There are 341 selected facts and no rejected values.
The run manifest is
`da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
See `raw-rebuild.md` for the retained path, invocation and boundaries.

All 41 focused tests pass with 100% critical line/branch coverage; all 74
explicitly unfiltered mutants are killed, no pardons. Final full harness exits
zero: 1,452 tests, 95.91% coverage, three pytest warnings plus five unclosed
SQLite ResourceWarnings emitted during coverage collection, 32 schemas,
22 representative documents, 9/9 differential parity and every mutation and
supply-chain gate, including the validated 110-component SBOM. CAS benchmark
was 521.51 MB/s. No HF or Bronze original bytes were changed by this work.
Hosted checks/merge, MCP projection and partial-stage resume remain separate.

## Raw historical extraction — 2026-08-30

Commit `3376695` retains 106 original Health/GDP facts, 1,143 lineage rows and
1,503 cell dispositions. Reconciliation retains 76 exact matches, 29 annotated
source-only years and one exact stored-token difference, without changing
either original. Independent library/CLI outputs and comparison ledgers are
byte-identical. Paths, hashes and interpretation boundaries: `raw-historical.md`.

All 65 focused and 226 domain tests pass. Both new modules have 100% line and
branch coverage, with all 99 explicitly unfiltered mutants killed, no pardons.
The final full harness exits zero: 1,411 tests, 95.84% coverage, eight warnings,
31 schemas, 21 representative documents, 9/9 parity and all mutation and
supply-chain gates, including the validated 110-component SBOM. These are
local gates; no hosted CI, publication or complete assimilation is implied.

## Raw forecast extraction — 2026-08-30

Commit `801783d` extracts literal BEFU/HYEFU Health summaries directly from
verified originals. Both ten-row donor oracles match in order, with 120
field-lineage rows and 4,665 cell dispositions. Three builds per source,
including the retained external-archive copies, are byte-identical. Original
hashes remain unchanged. See `raw-forecast.md` for retained paths and digests.

All 99 focused tests and 161 domain tests pass; the four critical workbook
modules have 100% line/branch coverage. All 135 unfiltered focused mutants
are killed, without pardons. Full harness exits zero: 1,346 tests, 95.72%
coverage, eight SQLite ResourceWarnings, all schema/parity/mutation and
supply-chain gates, including a validated 110-component SBOM.

Actual/Forecast and vintage are source-derived. Fiscal-year endpoints remain
unverified, rights are not inferred, and unselected workbook areas remain
explicitly preserved-only/excluded. No HF candidate or donor archive state
was changed. This local extraction receipt does not claim hosted CI or merge.

## Raw Budget extraction — 2026-08-30

Commit `d26e769` extracts from the pinned original Budget workbook, rather than
the donor SQLite derivative. All 6,504 input rows have dispositions: 215 Health
facts, 6,289 non-Health exclusions and zero rejected/blank rows. The 3,655
field-lineage records preserve every source column and exact cell addresses.
All seven oracle appropriation fields match in order, and two independent
builds produce identical files. Bronze CAS and original-byte hashes agree.

The four-file validation derivative is retained separately under the external
archive's `silver/raw-budget-d26e769`. Its manifest SHA-256 is
`03f41d39395b02169202e88e98f04a892a3dbb55c2083a328391d909af8f7d57`.
Its fixed observation-time test context is not a new capture attestation.
Neither financial-year basis nor redistribution rights is inferred; existing
Silver/Gold and HF publication remain unchanged.

The full local harness exits zero: 1,296 tests, 95.66% coverage, 30 schemas,
20 representative documents, 9/9 parity checks, all mutation/supply-chain
gates and a validated 110-component SBOM. Eight SQLite ResourceWarnings were
recorded. Focused extractor coverage is 100% line/branch, 49 focused tests and
111 domain tests pass, and all 73 unfiltered generated mutants are killed.
The machine receipt pins source, implementation, output and mutation hashes.
Hosted CI and merge are separate from this local evidence.

## Workbook part contracts and continuation — 2026-08-30

Commit `ee54bc9` corrects false-positive macro-part basename matching and adds
five fixture cases for macro markers, external references and opaque embedded
content. Originals remain byte-exact; no external linked resource is fetched.
The marker does not validate executable VBA or establish workbook safety.
Commit `3932caf` adds the milestone-based continuation route without activating
a scheduler or expanding publication authority.

Sequential focused results: 37 tests, 100% format-module line/branch coverage,
31/31 unfiltered mutations killed; mutation report SHA-256
`cf59aa2b52b49f60358179d614f4b72c8b5b6d8889b70bfd47e0e2c5ba5fb7fb`.
Fresh full harness: exit zero, 1,247 tests, 95.60% overall coverage, all schema,
parity, mutation and supply-chain gates, and a 110-component SBOM. Earlier
overlapping coverage reports were invalid and are not used as assurance.
Hosted checks remain a separate observation. Source bytes and HF publication
were not changed.

## Current-state reconciliation — 2026-08-30

Commit `11117f7` replaces scaffold-era current-state claims with canonical
receipt-backed counts and pinned publication identity. One offline regression
contract failed before the correction and passed afterward; Ruff, formatting
and basedpyright passed. The baseline full harness exited zero; the updated
full pytest suite passed 1,242 tests at 95.60% coverage. Production code was
unchanged. The baseline supply-chain checks and 110-component SBOM passed.

Public HF metadata readback confirmed revision
`9b85bac06597d4435fd078f6bed0f30bb008542b` and collection item
`6a92b824597df1d081fc4108`; this did not repeat the earlier 94-entry byte audit.
Parent #205 was observed closed, reopened to match the active plan, then
independently read back as open. The donor remains unarchived. Original bytes,
existing publication and historical observations were not changed.

## Rich workbook census — 2026-08-30

Commit `dffa310` adds deterministic ranges, hidden spans, scoped defined names,
formula/comment coordinates and ZIP member names to the bounded workbook
inventory. Existing counts remain; formulas are not evaluated, comment content
is not exported and the original bytes remain unchanged in repeat-run fixtures.

Local validation: 30 focused tests, 100% format-module line/branch coverage,
23/23 unfiltered mutants killed. Final `./scripts/validate.sh` exited 0 with
1,239 tests at 95.59% coverage and all schema/parity/security/supply-chain gates.
The earlier uv/SBOM launcher interruption is not counted as a full pass.
Cached-value interpretation, broader source coverage, CLI/scheduler work and
whole-track completion remain pending. No publication or donor retirement.

## Workbook safety prerequisite — 2026-08-30

Commit `b2956a7` rejects platform-ambiguous and duplicate ZIP members and bounds
the cumulative rectangular formula scan at 2,000,000 cells. Synthetic fixtures
verify unchanged original bytes on success and rejection. This is a traversal
bound after workbook loading, not an unrestricted-parser sandbox claim.

Local assurance: 27 focused tests, 100% format-module line/branch coverage,
22/22 generated mutants killed, and full `./scripts/validate.sh` passed with
1,236 tests at 95.59% coverage plus schema/parity/security/supply-chain gates.
No donor retirement or Hugging Face mutation occurred. Wider workbook census,
CLI/scheduler and whole-track completion remain pending.

## Evidence boundary

This scaffold records local planning and read-only observations. It does not
prove Bronze capture, Silver normalization, donor parity, source completeness,
resource rights, hosted CI, Hugging Face upload, remote verification,
collection membership, public release, donor retirement or Zenodo release.
Those states have separate tasks and gates.

## Approval evidence

| Claim | State | Evidence |
| --- | --- | --- |
| Track objective | approved | User requested complete donor assimilation into Archive Govt NZ and corresponding Hugging Face collection |
| Revised recommendations | approved | User explicitly approved medallion alignment, retention of every raw/original file, and consideration of directly/indirectly relevant features and datasets on 2026-08-29 |
| Implementation | not started | Track artifacts only |
| External publication | not authorized by readiness evidence | Exact payload candidate, resource rights and remote verification remain pending |

## Donor planning evidence

| Observation | Value |
| --- | --- |
| Repository | `https://github.com/edithatogo/nz_health_appropriations` |
| Commit | `4668e6c3b1b492086941d4c1ef96e299250a8301` |
| Tree | `c6d44ff79eda73cfc6ba7db5764e27ce01b890e1` |
| Deterministic archive SHA-256 | `9c8ab0feaa752ead08163463a634623d55a62a69608772b73127b3d7b709157e` |
| Tracked inventory | 23 files; 6,604,301 bytes |
| Original source files | eight: seven XLSX, one PDF |
| Donor SQLite | five tables; 312 total rows |
| Donor scripts | three Python files |
| Donor plots | six PNG files |
| Compile characterization | `process_data.py` raises `IndentationError`; intended behavior is not accepted as executable parity evidence |

The donor repository declares Apache-2.0 for repository code. No inference is
made that this licence grants redistribution rights to every government source
payload contained in the repository.

## Repository validation baseline

The pre-scaffold `./scripts/validate.sh` run passed all stages, including 1,161
tests and 95.36% coverage. Four timestamp-bearing evidence files changed only
through harness generation, were inspected, and were restored rather than
included in an unrelated track-initialization change.

The post-scaffold `./scripts/validate.sh` run also passed: lock, format, lint,
strict typing, 1,161 tests in 190.84 seconds, 95.36% coverage, 30 schemas and
20 representative documents, 9/9 parity checks, all mutation lanes, hygiene,
590.54 MB/s CAS throughput, dependency audit, licence inventory, secret scan,
and a validated 102-component SBOM. This is local repository-readiness
evidence, not hosted CI or external publication evidence.

## Source and platform observations

The official URLs in `spec.md` were inspected as discovery/coverage leads.
Exact downloadable resources, observed bytes, time ranges and rights must be
frozen during Phase 1. The existing Hugging Face HEOR collection was observed
as public with one member; the proposed health-appropriations dataset did not
exist under the inspected account state. These are time-sensitive read-only
observations, not publication receipts.

## Open evidence requirements

- complete donor Bronze import and byte reconstruction;
- cutoff-bound official source census and per-item disposition;
- workbook/sheet/range extraction census;
- resource-level rights evidence;
- five-table/312-row parity or repair ledger;
- four-analysis-family/six-plot behavioral parity;
- Silver/Gold/Platinum reconstruction evidence;
- dependency evaluation and lock/supply-chain evidence if adopted;
- exact-head hosted CI;
- checksum-pinned HF candidate approval;
- upload, remote readback, Dataset Viewer/Parquet, revision and collection
  membership receipts; and
- explicit public release state.

## Phase 0.1 reconciliation

At `2026-08-29T08:26:05Z`, the pinned donor identity and complete inventory
were re-observed without drift: 23 paths, 6,604,301 bytes, eight source
originals, five SQLite tables containing 312 rows, three scripts and six PNG
plots. The no-prefix `git archive` SHA-256 remains
`9c8ab0feaa752ead08163463a634623d55a62a69608772b73127b3d7b709157e`.

The target Hugging Face dataset remained absent and the HEOR collection still
contained one unrelated dataset. Eight official landing pages were probed:
four returned HTTP 200 and four returned HTTP 403 to the bounded command-line
client. A 403 landing-page observation is not interpreted as resource absence;
Phase 1 must use source-family discovery and explicit dispositions. No external
state was mutated by this task.

## Hosted traceability

GitHub issue #205 is the parent for phase sub-issues #206 through #216. The
sub-issue relationship was read back after creation. This proves hosted issue
traceability only; it does not prove implementation, CI, merge, publication or
release.

## Phase 0 checkpoint

The Phase 0 claim/leakage review found no drift, unsupported completion claim,
credential, signed URL or restricted payload in the track artifacts. The full
local validation harness passed with 1,182 tests, 95.33% coverage, all schema,
parity and mutation checks, and green dependency, licence, secret and SBOM
gates. Hosted CI remains a separate, unclaimed state.

## Bronze donor preservation and format census

All 23 donor files and 6,604,301 bytes are now retained as distinct external
Bronze CAS objects and reconstruct successfully. Compact Git evidence pins the
external manifest and format-census digests. The structural census covers all
seven workbooks, the 471-page PDF and the five-table/312-row SQLite derivative;
the source bytes remain unchanged and outside Git.

## Source census and dependency state

The first cutoff-bound census contains 79 explicitly `discovered` records,
including all 66 links returned for the Treasury Vote Health index and 13
current direct/context resources. It is deliberately marked partial until the
remaining annual Budget/forecast vintages and exact Stats NZ series are frozen.

`openpyxl` and Matplotlib are locked, tested adapters. Audit, licence,
tracked-source scan and a 110-component SBOM passed. This establishes software
adoption evidence, not source redistribution rights.

## Bronze through Platinum checkpoint

The final source census has 141 explicit dispositions: 73 eligible official
originals captured with WARC evidence and 68 discovery pages retained as
out-of-scope pointers to their authoritative files. The complete capture
manifest covers 38,584,141 bytes and has no failed or unresolved resource.

Donor preservation and functional parity are evidenced independently. Bronze
reconstructs all 23 donor paths and the pinned Git archive. Silver contains
312 typed facts and 1,699 field-lineage rows. Gold rebuilds the donor's five
SQLite tables, five analytical tables and six plots. A clean-room run
reproduced the pinned Silver and Gold bytes exactly.

Candidate v4 contains 94 pre-manifest files and 39,390,246 bytes. Its exact
manifest SHA-256 is
`9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`.
This is local release-candidate evidence only. Upload, hosted readback,
collection membership and public release are not yet claimed.

## Hosted publication and readback

PR #217 merged at `622ec15d53b162916a0b1b390ec5dab6f2f6f3a7` after the
Ubuntu, macOS, Windows, CodeQL, dependency-review, workflow-policy and Codecov
patch checks passed on exact head `3953f4a02417c7ac5a31bfd12113e23a2ed1dd26`.

After the checksum-pinned candidate was presented, the user instructed the
next steps to proceed. Candidate v4 was published publicly as
`edithatogo/nz-health-appropriations` at immutable revision
`9b85bac06597d4435fd078f6bed0f30bb008542b`. A fresh download of that revision
reproduced manifest SHA-256
`9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e` and all
94 manifest entries verified with zero mismatches. The HEOR collection was
then updated and independently read back with dataset item object ID
`6a92b824597df1d081fc4108` and the pinned revision in its note.

## Formula cache characterization — 2026-08-30

Commit `f73d678` adds coordinate/type/presence observations without exporting
formula or cached contents. Thirty-two focused tests pass with 100% line and
branch coverage for `formats.py`; all 30 unfiltered mutations were killed
(report SHA-256 `b64d673ed95c1a633a09e24f6c84b0e0a989ce5c85d032258947889fcdaf55dd`).
Ruff and basedpyright pass. Baseline and final full harness runs exit zero;
final results are 1,241 tests, 95.60% overall coverage, 30 schemas, 20 sample
documents, 9/9 parity checks, all mutation and supply-chain checks, and a
110-component SBOM. Evidence is local; hosted CI is separately verified.
Originals and the existing HF publication were not changed. Cache freshness,
complete format support and donor retirement are not claimed.
