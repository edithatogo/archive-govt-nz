# Evidence

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
