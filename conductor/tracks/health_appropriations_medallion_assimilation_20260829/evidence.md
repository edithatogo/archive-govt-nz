# Evidence

## Pure historical canonical consumer — 2026-09-03 UTC

Commits `02d36bc` and `13e8d85` add an in-memory bridge that accepts only an
exact recomputation of the historical canonical projection and parent receipt.
Twenty-two focused tests pass at 100% line and branch coverage over 98 critical
statements and 16 branches; Ruff and scoped basedpyright pass. The tests cover
raw-order independence, canonical physical order, typed JSON aliases, Decimal
and period boundaries, reversible lineage/accounting and public historical
analysis equivalence. Cold mutation, full native and hosted delivery remain
pending. No file fixity, rights, analysis execution or publication is claimed.

## Additive inventory planner — 2026-08-31 UTC

`c6d0e37` implements fixity and recorded-rights reconciliation only. It performs
no candidate construction, semantic Parquet validation, rights assessment or
publication. All four pinned source packages retain their original manifests.
Two live calls verify 94 base files / 39,390,246 bytes and 16 proposed additional
files / 1,965,259 bytes, with identical receipt SHA-256
`26102f7aa1ea2b4bce96ae9bf861d3838848d48606cd63bbc7ec19ad7fe86951`.

Local focused assurance: 102 tests, 100% critical line/branch coverage and all
78 cold unfiltered mutants killed with zero timeouts/errors/survivors/pardons.
Independent review found no actionable issue. The required native harness
passed pre-test gates but exited 124 at the 300-second test deadline after two
unidentified failure markers; no final summary/coverage or post-test gates.
This is incomplete native assurance, not a pass. Exact-head hosted checks are
pending. Detailed commands and retained receipt hashes are in `runlog.md`.

## Plot context-style correction — 2026-08-31 UTC

Three red regressions exposed a lost legend key for disconnected same-context
segments and colliding abbreviated labels. All 23 renderer tests now pass at
100% line/branch coverage (132 statements, 30 branches), with Ruff clean.
Renderer SHA-256: `07674afbc970aed73a662e43a8c2450560d40e587524a86c2901fba835566df5`.

The initial cold-cache, two-worker mutation run selected 21 unit/protocol tests
and excluded the two documented slow full-PNG integration tests only from
mutation subprocesses. All 67 mutants ran without coverage-guided filtering:
42 killed, 25 timed out, zero survived/errored/pardoned. Timeouts are not kills;
this is incomplete mutation assurance. Report SHA-256:
`bcf99622a4e7339017896f5896b567de3246eb8653c064690b7146aa65de8b03`.

A new temporary CLI rebuild from reviewed Gold pin
`ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`
matches all eight retained V2 files byte-for-byte. Its manifest remains
`a04b1b8785d7a4da67ad1b83d6449592838ed0359de792368bb8f150155786d2`.
No original, retained derivative or publication was modified. Full-harness
and hosted outcomes remain separate from this focused/local evidence.

Required native validation was run twice. The first attempt stopped on five
new-test typing diagnostics; explicit array equality/line-handle narrowing
fixed these, with targeted strict typing and the three regressions passing.
The corrected attempt passed lock, Conductor, format, lint and types, then
exited 124 at the unchanged 300-second pytest stage. It collected 1913 tests
and showed one unidentified failure marker before timeout, without a final
summary or coverage result. Post-test gates were not reached. Neither a full
local pass nor an unrelated-failure diagnosis is claimed; exact-head hosted
validation and resolution of any hosted failure remain pending.

## Donor failure conformance — 2026-08-31 UTC

`4454d75` binds full compile observations to all three script hashes and adds
the synthetic broken-processor independence regression. No donor imports or
execution occurred. See `donor-behavior.md` for the risk-to-test mapping and
`donor-script-observation-20260831.json` for the bounded observation.
253 focused tests pass; final native harness passes 1,907 tests at 96.48%
coverage, eight SQLite warnings, all schema/parity/mutation/supply-chain gates,
and 111-component SBOM. Read-only CLI verification of the retained 341-fact raw
run passes. This closes donor-intended pipeline conformance, not full source
coverage or publication. Hosted delivery is separately pending.

## Final source plot local assurance — 2026-08-31 UTC

Functional commit `eeb6200` passes the full isolated repository harness:
1,906 tests, 96.48% overall coverage, eight existing SQLite warnings,
40 schemas/30 documents, 70 tracks, 9/9 parity, every native mutation and
supply-chain gate, and 111-component SBOM. All 48 focused tests achieve
100% critical line/branch coverage. Current reader/contract/renderer mutation
counts are 44/26/58 kills, with no survivors/timeouts/pardons. Renderer mutation
uses the documented 18-test unit/protocol selection; two full-PNG integration
tests remain in normal execution. See `raw-plots.md` for report hashes.
Three independent V2 builds match all eight files. All 23 preserved donor
objects and their manifest reverify. Hosted delivery is pending; no originals
or Hugging Face bytes changed.

## Gold delivery and source plot QA — 2026-08-31 UTC

Gold PR #261 merged `15b47b946a27a47efd4715002f0c1aff563149d4` at
04:50:48 UTC after all seven checks passed on head
`3895434eea49dec019ae48bdcdf70626ae1b1c71` (CI run `33358094163`).
Health-domain source/tests are unchanged between the checked head and merge;
the complete trees differ because intervening RIopa work is included. Earlier
local timing failures and the earlier Windows throughput failure remain
recorded. Hosted success is not a retroactive local pass or an HF update.

Source plots now have a pinned Gold reader, six pure contracts, deterministic
Agg renderer and dry-run-first CLI. Corrected retained package
`gold/raw-plots-20260831-v2` has manifest
`a04b1b8785d7a4da67ad1b83d6449592838ed0359de792368bb8f150155786d2`.
Its independent rebuild matches all eight files. All six views were inspected;
growth gaps, tick spacing, negative values, hatch contrast and exact breakdown
labels are explicit. Point counts: 53 nominal, 48 growth, 53 GDP shares, four
breakdown, six Health and six unclassified; five growth omissions remain null.
V1 remains preserved as a superseded QA build. Renderer focused validation is
15 tests at 100% line/branch coverage. Whole-increment mutation/full assurance
and hosted plot delivery are pending; neither publication nor originals changed.

## Verified Gold export — 2026-08-31 UTC

Implementation `b38069ce5d560525e19dab22c90eca9dd3d20f3a`, provenance
review fix `0d864d44e776b2763b80de8c463051fae35b93eb`. Shared bounded
reading, canonical identities and source/amount lineage feed both persistence
paths. Gold CLI preflights by default and exclusively creates five typed tables,
exact input/lineage sidecars and a manifest.

Four eight-file builds match; manifest
`ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`.
All 321 selected facts and 4,798 lineage records accounted for; the 20 forecast
facts are explicitly excluded from these views, not removed from Silver.
All 16 Budget aggregates/four breakdown values match exactly. Historical
comparison preserves 29 extra source years and discloses float tolerances,
the 1997 basis guard and the legacy 2020-to-2000 comparison repaired to 2019.
Compatibility export remains byte-identical to its four retained files.

46 focused tests pass at 100% critical line/branch coverage. Final mutation
attempt: 63 kills, 16 timeouts, zero survivors/pardons; timeouts are not kills.
Full local harness attempts did not pass: a generation health-check failure,
two 300-second timeouts, and a fail-fast diagnosis of unrelated legislation
timing variability. Keep these limits explicit; hosted assurance remains
pending. Schema validation passes 37 schemas/27 documents; Conductor 69 tracks.
No original or HF publication changed. See raw-gold/runlog for detailed receipts.

## Pure source-derived analytics — 2026-08-30 UTC

Functional commit `0bf14b07ac07ef5271a5e44626e4a8857907641b` implements
historical nominal/growth/GDP and Budget classification calculations without
reading donor SQLite. Verified retained snapshots produce 53 historical rows,
48 comparable growth values and 53 period-aligned GDP shares; 215 appropriation
IDs contribute to 16 trend and four 2025 Estimated Actual breakdown groups.
Source objects, vintages, amount types and accounting/period breaks stay explicit.

Seventy-nine focused tests and 30 generated growth cases pass; both modules
have 100% critical line/branch coverage. All 71 historical and 33 Budget
unfiltered mutants killed without pardons. Full isolated harness exit 0:
1,656 tests, 96.09% coverage, eight existing SQLite resource warnings,
35 schemas/25 documents, 9/9 parity, all mutation and supply-chain gates,
validated 110-component SBOM. See raw-analytics for detailed policies/hashes.
Persistence, CLI and plots remain pending; no originals or publication changed.

Compatibility PR #254 merged independently at
`4e4586ec2b3732367c4ff8732957b6d40126e0e2` after six exact-head checks passed.
Hosted/tested tree equality: `1f983d17cfc44e877bed8c19e1d7fd505083058a`.

## Persistent raw compatibility export — 2026-08-30 UTC

Functional commit `e91d24b97fad312ae2c4418f31fc4435f9afd5c1` exports verified
canonical Parquet into a five-table database plus exact-record and field-lineage
sidecars. Two independent builds match all four files; manifest
`fb405a2fdbb2809093cb03d62ddbe1fcb1a1f6f91d304666e8ef0964813f73fb`.
Read-only donor comparison retains all five schemas and 312 donor rows, adding
29 historical Health observations. Exact source values remain authoritative:
15 binary representation flags are not conflated with the prior source/donor
precision reconciliation. All 341 facts and 4,918 lineage rows are retained.

Twenty-eight focused tests have 100% critical line/branch coverage; 52/52
unfiltered mutants killed, zero pardons; report
`5dd74daa8824b3e4b4e3b6230251190ec0b41a69e2aa218aa12e5d9e6a53801d`.
Final isolated full harness exit 0: 1,577 tests, 96.05% coverage, eight existing
SQLite resource warnings, 69 Conductor tracks, 35 schemas/25 documents, 9/9
parity, all mutation and supply-chain gates; SBOM 110 components. The invalid
shared-mock mutation attempt and isolated lint/type corrections are recorded
in the run log. Original bytes and the published HF candidate are unchanged;
this receipt claims local validation, not hosted delivery or public promotion.

## Raw compatibility projection — 2026-08-30

Commit `42cee7d` provides pure, loss-aware legacy value projection for all five
table shapes. The verified raw run projects 341 facts and flags 15 exact
decimal-to-binary representation differences, preserving exact amounts and
source context. It does not yet write a database or replace published products.
All 27 focused tests pass at 100% critical line/branch coverage; all 35
explicitly unfiltered mutants are killed without pardons. Final full harness
exits zero: 1,508 tests, 95.97% coverage, seven pytest warnings plus an additional
SQLite ResourceWarning, 33 schemas/23 documents, 9/9 parity and all mutation
and supply-chain checks, including a 110-component SBOM. Evidence is local.

Inspector PR #245 independently merged at
`32fbbe391a169d00d760a051c39c9793a95f9109` after all seven exact-head checks
passed. Its merged and tested trees match. This does not mark the larger
compatibility export or full assimilation complete.

## Typed workbook inspection — 2026-08-30

Commit `446a82d` adds hash-pinned, bounded read-only sheet inventory and decoded
previews, without formula evaluation or canonical-fact claims. Twenty-two
focused tests pass at 100% critical line/branch coverage; all 40 unfiltered
mutants are killed without pardons (report SHA-256
`cb0dbd2222665a8aba4c9d48b2028917f9e0348a07dd78d226005f3ec7edc44d`).
The full harness exits zero, including mutation and supply-chain gates and a
110-component SBOM. Targeted schema validation passes 33 schemas/23 documents.
Live inspection lists eight Budget sheets and previews 34 selected cells;
the pinned original SHA-256 remains unchanged. No HF bytes were changed.
See `workbook-inspection.md` for limits and invocation.

PR #243 (read-only verification) separately passed all seven hosted checks
and merged at `d85c810ebc272163341e6517dd541a4cf3ee1dbd`; its tree equals
the exact tested head. Inspector hosted delivery is not implied by that merge.

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
## 2026-08-31 — Eight-record-set structural foundation

Functional commit `d67bd41` adds eight immutable structural Arrow schemas,
not row validation or source promotion. The final focused suite passes 34
tests with 100% coverage (10 statements, no branches). Cold unfiltered
one-worker mutation testing killed all 30 mutants in 45.41 seconds: zero
survivors, timeouts, errors, pardons or cache hits. Report SHA-256:
`bfe6dc084d9533d64ce7fd2c977d56ff204c63209e57e98418e026f6665a0248`.
Ruff and strict typing pass. Independent review requested complete field-type
and nullability assertions; those are included before mutation assurance.
Exact Parquet nested shapes and DuckDB-compatible decimal bounds are tested.
The full native harness remains pending at this receipt. No v1 schema,
source package, original or publication was changed.
## 2026-08-31 — Record-set full local pass

The full native harness at `6895083` completed exit 0 with 2,424 tests,
96.98% coverage, 41 schemas/31 samples, 9/9 parity and all mutation/security/
supply-chain gates. The durable log hashes to
`fdea8f19263999b33dea5583e6635dc5477ff730c4697f8f55d1c665d61f6507`.
This satisfies local assurance for the bounded structural registry; row-level
validation, canonical projections, full Phase 3 completion and hosted delivery
are not inferred from it. No existing source package or publication changed.
