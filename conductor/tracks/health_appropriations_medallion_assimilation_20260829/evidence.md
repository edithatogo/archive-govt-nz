# Evidence

## 2026-10-25 — Phase 8 concurrent resume attempt contract

- Issue: #214; M-15/M-18, AC-13/AC-16.
- Changed: `tests/domains/health_appropriations/test_resume_execution.py` and
  Phase 8 plan/index/runlog/evidence/review plus the contract receipt.
- Runtime: repo-local CPython 3.15.1 via `uv run --locked`.
- Focused concurrent claim test: passed.
- Resume execution, operations and planner selection: 217 passed.
- Ruff, format and basedpyright passed on the changed test.
- `./scripts/validate.sh` passed on this exact local tree: 8,423 passed,
  14 skipped, 97% coverage, with schema/document, parity, mutation, hygiene,
  dependency, licence, secret-scan and SBOM gates passing. Hosted checks remain
  a separate PR gate.
- The test forces two same-path invocations to pass read-only destination
  preflight together. One creates and verifies the exclusive attempt; the other
  is rejected, with all pre-existing input files unchanged.
- Remaining: this does not establish distributed locking, hostile-filesystem
  safety, remote drift handling, or completion of issue #214. Hosted PR checks
  are pending.

## 2026-10-25 — Phase 8 scheduled discovery regression contract

- Issue: #214; requirement references M-15/M-18 and AC-13/AC-16.
- Changed: `tests/tools/test_workflow_policy.py` and the track-local Phase 8
  plan, index, run log, evidence and contract receipt.
- Runtime: repo-local CPython 3.15.1 via `uv run --locked`.
- Focused test: `uv run --locked pytest tests/tools/test_workflow_policy.py::test_health_discovery_schedule_is_read_only_and_does_not_need_secrets -q --no-cov` — 1 passed.
- Static checks: `uv run --locked ruff check tests/tools/test_workflow_policy.py` and `uv run --locked ruff format --check tests/tools/test_workflow_policy.py` — passed.
- Full harness: `./scripts/validate.sh` — passed on the exact pre-commit tree: 8,408 passed, 14 skipped, 97.07% coverage; 81 schemas/71 representative documents; parity 9/9; configured mutation, hygiene, dependency, licence, secret-scan and SBOM gates passed.
- Scope: local regression assurance for read-only permission, no secret interpolation, non-cancelling concurrency, and discovery-only behavior. No workflow behavior or external state changed.
- Remaining: this does not implement scheduled capture/normalization or triggered reconciliation/reconstruction, and does not complete issue #214.

## Merged RDF validation and bounded task reconciliation — 2026-09-05 UTC

PR #401 merged at `c92c3d2f717b55537b5d338d430689125e95fa66` after all
eight exact-head hosted checks passed on `f111dbf0d7148c13c9fa69caba86c5ebf0506c06`.
GitHub readback confirmed the merge at 08:32:53Z; the merged tree equals the
validated head. CI run `33955010646` passed Ubuntu, macOS and Windows assurance.
The warm-up review thread was resolved after the tested explicit-plugin fix.

The exact-head local `./scripts/validate.sh` also exited 0: 4,774 tests,
15 retained warnings, 97.61% coverage, 48 schemas/38 representative documents,
9/9 parity, all mutation lanes, hygiene, throughput and every supply-chain gate.
The test stage took 122.08 seconds. Test SHA256:
`0f642a6fb234bdd2a3271544fd877e1789ccda36d5a6cbec1559452763f30515`.

Six bounded task checkboxes are reconciled against PRs #397, #398 and #401
and this integrated full assurance. This does not complete historical source
enumeration, the whole metadata/application-profile requirement, rights,
publication, recovery, or track acceptance. The track remains in progress.

## Independent offline RDF interpretation — 2026-09-05 UTC

Added development-only RDFLib 7.6.0, with no existing locked dependency version
changed, after recording its stack/security rationale. The combined RDF/DCAT/
PROV suite passes 47 tests; six new parser tests cover exact expanded triples,
resource/literal types, actual payload checksum bytes and blocked external
contexts. Ruff and typing pass. The 12 upstream parser deprecation warnings
remain visible. Dependency vulnerability and licence gates pass, and the
strict CycloneDX validator accepts the 112-component SBOM.

A separate guarded parse of the two retained historical snapshots yielded
66 triples, six datasets, six distributions and six checksums. The accompanying
replay verified all 20 original/raw/canonical files unchanged. Exact script and
graph hashes are recorded in `runlog.md`. This advances RDF processing evidence
without rewriting the generation helpers' per-call receipts or claiming a full
DCAT application profile, rights decision, publication or graph-index deployment.
Full/hosted assurance for the follow-up is still pending.

## Verified local DCAT projection — 2026-09-05 UTC

`local_dcat.py` composes strict original/raw/canonical snapshot verification
before producing separate Dataset/Distribution nodes for each retained recordset.
The graph and full verification inventory receive deterministic digest bindings.
Twenty-three tests pass in 17.52 seconds at 100% line/branch coverage (24 statements,
two branches). Cases cover all three supported package kinds, deterministic
input-order independence, fresh outputs, no writes, duplicate/untyped inputs,
wrong pins and originals, and re-pinned wrong values/schema metadata/rights.
Targeted typing, Ruff and formatting pass. The initial red test failed because
the implementation module did not yet exist. Mutation and full/hosted assurance
are pending at the initial checkpoint. This is local synthetic-fixture evidence, not retained-corpus replay,
RDF processor conformance, source-specific rights, federation or publication.

Subsequent cold mutation killed 10/10 mutants with no survivors/errors/timeouts/
pardons/cache hits. A read-only retained historical replay then verified both
independently pinned packages, produced six Dataset/Distribution pairs, proved
input-order-independent output and checked all 20 input files unchanged.
Exact replay and mutation hashes are recorded in `runlog.md`. This adds actual
historical-snapshot evidence without claiming all-source metadata coverage or
persisted/released metadata. Full and hosted assurance remain pending.

## Historical source enumeration — 2026-09-05 UTC

See [the human register](./historical-source-register.md) and its paired
[machine observation](./historical-source-register.json). These advance M-02
and M-11 with 30 visible edition obligations and six exact workbook leads.
The focused test `tests/tools/test_health_historical_source_register.py`
passed after an observed missing-artifact failure. Full assurance, payload
fixity, source rights and remaining annual enumeration are not established.

## Pure historical canonical consumer — 2026-09-03 UTC

Commits `02d36bc` and `13e8d85` add an in-memory bridge that accepts only an
exact recomputation of the historical canonical projection and parent receipt.
Twenty-two focused tests pass at 100% line and branch coverage over 107 critical
statements and 18 branches; Ruff and full basedpyright pass. The tests cover
raw-order independence, canonical physical order, typed JSON aliases, Decimal
and period boundaries, reversible lineage/accounting and public historical
analysis equivalence. Hosted delivery remains pending. The
cold-cache, one-worker, unfiltered strict-zero-pardon gate
killed 51/51 mutants with zero cache hits, survivors, errors, timeouts or
pardons. The native harness passed 4,615 tests at 97.53% overall coverage plus
all schema, parity, mutation and supply-chain gates. No file fixity, rights,
analysis execution or publication is claimed.

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
## Analytical context register — 2026-09-05 UTC

Added analytical-context-register.md as a read-only reconciliation of existing
census records and source-specific profiles. It identifies exact CPI, QES, GDP
and HLFS working-age objects, records the resident-population metadata lead
without acquiring it, and keeps Crown-expense definitions source-specific. No
Gold measure, rights decision, new capture or publication state changed.

## Local provenance verifier reconciliation — 2026-09-05 UTC

The read-only verifier task is implemented by the strict local provenance
reader and its retained-source regression suite. It checks marker, original,
raw-package and canonical-file fixity, recomputes pure projections, rejects
altered or unexpected roots, and returns scoped verification evidence. The
descriptor-only PROV helper remains assertion-only and still reports rights,
approval and publication as unresolved. The exact Health full assurance on
the merged follow-up passed 4,774 tests and all configured gates. This task
does not complete Platinum metadata, rights, publication or the track.

## 2026-09-13 — Normalization checkpoint integration

Preserved the final September 6 admission receipt, including the SQLite commit,
with a separate dated snapshot. All four current source/test hashes match;
260 focused tests pass with 100% coverage of both modules. Historical mutation
results remain separately identified. See the paired integration report and
receipt in `normalization-checkpoint-integration-20260913.md`.
## Scheduled discovery heartbeat — 2026-09-28

Local evidence: 22 focused heartbeat/workflow tests passed; the heartbeat
module has 100% branch coverage. Ruff and basedpyright passed.
`tools/validate_schemas.py` validated 50 schemas and 40 representative
documents including the new heartbeat sample. The first full repository
harness passed 7,029 tests, 9 skipped, 98.14% branch coverage, parity 9/9 and
all configured mutation, dependency, licence, secret and SBOM gates. The
coverage follow-up is undergoing a fresh full harness run. Hosted scheduled
workflow execution has not been claimed; the heartbeat is attached to the
next scheduled/manual discovery workflow run after merge.

Two full-harness attempts had transient unrelated failures under xdist; focused
reruns passed all affected cases. The third clean `./scripts/validate.sh`
passed 7,033 tests, 9 skipped, 98.16% branch coverage, 50 schemas/40
representative documents, parity 9/9 and every configured mutation, hygiene,
dependency, licence, secret and SBOM gate. This is local assurance; the hosted
scheduled discovery workflow still needs a post-merge run to produce its first
heartbeat artifact.

## Drift baseline review correction — 2026-09-28

The scheduled discovery command omits `--previous`, so no baseline comparison
is available. The source manifest now carries explicit baseline state, and the
heartbeat leaves drift unavailable unless the prior manifest is observed,
complete and hash-shaped. Focused discovery/heartbeat/schema/workflow tests
passed 28 cases; all 50 schemas/40 samples validated, and Ruff/basedpyright
passed. The first full correction attempt had one unrelated Hypothesis
slow-generation failure under xdist; the focused rerun passed. The subsequent
full `./scripts/validate.sh` passed 7,035 tests, 9 skipped, 98.16% branch
coverage, 50 schemas/40 representative documents, parity 9/9 and every
configured mutation, hygiene, dependency, licence, secret and SBOM gate.
Exact-head hosted checks for the correction are pending.

The first full correction run reported 7,034 passed, 9 skipped and one
unrelated Hypothesis slow-generation health-check failure under xdist; its
focused rerun passed. This remains a candidate result, not full assurance.

## Read-only Health status resource — 2026-09-28

The finite status resource returns the same schema-validated, hash-pinned
manifest provenance receipt as the read-only tool. Direct resource reads and
JSON-RPC `resources/list`/`resources/read` pass; the real Cyclopts command
returns structured JSON for no-state and does not create files. The focused
CLI/MCP protocol suite passed 35 tests, with Ruff and basedpyright clean. No
state is promoted to capture, normalization or publication readiness.

## Bronze-bound canonical CPI recovery — 2026-09-30

Added `cpi_canonical_projection.py` for exact captured Stats NZ CPIQ.SE9A.
The adapter verifies the fixed Silver manifest and every Parquet product against
an independent parse of the pinned Bronze CSV, then emits 449 canonical
`price_population_fact` rows and 3,143 direct-lineage rows. It preserves NA as a
null with an unknown reason; quarter bounds are explicit; index base and rights
remain unresolved; no inflation adjustment or analytical admission is claimed.
The clean-room runner rebuilt Silver and projected the canonical facts twice;
all output paths, lengths and SHA-256 digests matched and the Bronze CAS snapshot
was unchanged. Details: `clean-room-recovery-20260930.json`.

Focused adapter/recovery tests: 7 passed. Full `./scripts/validate.sh`: 7,146
passed, 9 skipped, 98.25% coverage against the 80% floor; 52 schemas/42
representative documents, parity 9/9, configured mutations, hygiene, CAS,
dependency/license/secrets and 113-component SBOM passed. Automatic Conductor
`phase_7_gates` passed with receipt hash
`6681721608e8541ca83da366552ed493fd7f837b403a7250861d629323c9eaa9`.
The track remains in progress: other canonical adapters, source-native profiles,
reports, rights/base qualification and complete Platinum metadata remain open.

## Vote Health 2002/03 Part F revenue — 2026-10-03

Machine receipt: `vote-health-revenue-2002-03-20261003.json`. The source is the
exact 317,126-byte captured Estimates PDF pinned by the source census. A
bounded source operation extracted 16 page-43/44 revenue rows while retaining
the prior-year budget, prior-year estimated actual and current-year budget
columns. Two Silver builds share manifest SHA-256
`6f1c7f3c5b8097543f9897a0fd37908560ca0232bca5ebe20522ec8aa2314907` and output
hashes. Bronze dispatch selected the exact 2002/03 adapter; each of the 16
revenue records matched the Silver package by ID and emitted fields. Dispatch
accounted for 43 total records, 210 lineage entries and all 44 PDF pages.

Focused validation passed 493 tests with 10 skipped. Rights remain
unevaluated, publication is local-only, and this does not establish summary
coverage, other editions, source completeness, Gold qualification or
cross-source comparability. The required full harness passed 7,300 tests with
10 skipped and 98.10% coverage against the 80% floor. Schema, parity, mutation,
supply-chain and automatic Conductor phase review passed; hosted PR checks
remain pending.

## Vote Health 2002/03 overview headlines — 2026-10-03

Machine receipt: `vote-health-estimates-overview-2002-03-20261003.json`. The
source-pinned operation extracts seven named overview headlines from pages 2–3
of the 44-page Estimates PDF: Vote total 8,645.493, increase 940.846,
departmental total 166.917, non-departmental total 8,432.327, other services
26.398, other expenses 19.851, and Crown revenue 292.005 (all `$ million`).
The profile keeps source token and phrase lineage, leaves currency code null,
and does not derive a prior-year total. Rights are unevaluated and all other
page content remains outside this bounded normalization.

## Vote Health 2004/05 overview headlines — 2026-10-03

Machine receipt: `vote-health-estimates-overview-2004-05-20261003.json`. The
source-pinned operation extracts eight reviewed monetary headlines from pages
2–3 of the 48-page Estimates PDF: Vote total 9,917.895, increase 332.540,
departmental functions 168.608, departmental capital contribution 0.955,
non-departmental total 9,748.332, capital funding 543.703, other services
59.666, and Crown revenue and receipts 503.067 (all `$ million`). Exact source
phrases, raw tokens, period labels and field lineage are retained. No totals
are recomputed. Rights and comparability remain unevaluated; all other PDF
content remains outside this bounded normalization. Captured PDF SHA-256 is
`6dac0aaa3fd181fffacf30cffa829b0f189e8b68ebfdbeb0dd5ef88736af96a2`.
The receipt records the eight facts, two page dispositions and hashes for all
three local Parquet outputs.


## Vote Health 2005/06 overview headlines — 2026-10-03

Machine receipt: `vote-health-estimates-overview-2005-06-20261003.json`. The
source-pinned operation extracts eight monetary headlines from pages 2–3 of
the 50-page Estimates PDF: Vote total 9,681, increase 824.6, departmental
functions 150.198, non-departmental total 9,530.767, service funding
9,048.762, other expenses 17.712, capital funding 464.293, and Crown revenue
and receipts 474.340 (all `$ million`). The first seven facts are GST
exclusive and the revenue fact GST inclusive. Exact phrases, raw tokens, period
labels and field lineage are retained; totals are not recomputed. Rights and
comparability remain unevaluated; other PDF content remains outside this
bounded normalization. Captured PDF SHA-256 is
`9a269a87a0cef8fc998fc1b012ae9fd734fb48b111504bb7a1ca01cdcf97c2b4`. The
receipt records the facts, two page dispositions and hashes for all three
local Parquet outputs.


## Vote Health 2006/07 overview headlines — 2026-10-03

Machine receipt: `vote-health-estimates-overview-2006-07-20261003.json`. The
source-pinned operation extracts eight monetary headlines from pages 2–3 of
the 41-page Estimates PDF: Vote total 10,644.927, increase 834.759,
departmental functions 157.408, non-departmental total 10,487.519, service
funding 10,083.830, other expenses 22.912, capital funding 380.777, and Crown
revenue and receipts 529.194 (all `$ million`). Exact phrases, raw tokens,
period labels and field lineage are retained; totals are not recomputed.
Rights and comparability remain unevaluated; other PDF content remains outside
this bounded normalization. Captured PDF SHA-256 is
`866bce96ac216344c5dcdf25fee1f31548d5c32ba3cd94ef4b4977a495f509ea`. The
receipt records the facts, page dispositions and hashes for all three local
Parquet outputs.
## 2026-10-06 — Integrated clean-room recovery and final review

The current integrated recovery runner completed two-build reconstruction for
22 wired product lanes from the pinned Bronze store. Its receipt confirms
repeat-output checks, unchanged Bronze objects, and `partial_with_blockers`;
cross-source comparison, remaining source-native profiles/adapters, and the
complete Platinum profile set are explicitly not rebuilt. Source-health
reconstruction is repeat-identical for 143 records across 13 families (75
captured, 68 out of scope); 11 contextual series remain unqualified with
rights unevaluated. Claim-drift reported zero divergences and Conductor state
validation reported zero errors across 93 tracks. See
`clean-room-recovery-20261006-final.json` and
`final-review-20261006.md`. This evidence does not close the Health track or
repeat the already-completed external publication/collection operations.

## 2026-10-06 — 2025/26 Supplementary Estimates Silver evidence

- Profile: `vote-health-supplementary-2025-26-summary-totals/v1`.
- Bronze source: `575e3744f555d668f3748f46cc55781378bfc0ad35008c9512a942c57279f31f`;
  original bytes unchanged.
- Persistent local Silver: `silver/vote-health-supplementary-2025-26-summary-totals-20261006-v1`,
  manifest `3975a41c38f651569247ed01a047f6b74416ed7340204aad01135ac3471126aa`;
  six facts, 18 field-lineage rows, one page disposition.
- Clean-room recovery: two Bronze builds are identical and match the retained
  Silver manifest; whole receipt remains `partial_with_blockers`.
- Focused checks: `uv run pytest tests/domains/health_appropriations/test_vote_health_supplementary_2025_26.py tests/domains/health_appropriations/test_source_operations.py tests/domains/health_appropriations/test_health_recovery_assurance.py -q`
  passed 526, skipped 10; the new profile module has 100% line and branch
  coverage. Targeted Ruff lint passed.
- `./scripts/validate.sh` passed: 7,555 tests passed, 10 skipped, 97.67%
  overall coverage against the 80% floor; schema, parity, mutation, security
  and supply-chain gates passed. Rights remain unevaluated; publication was not
  performed. Wider source and full-track gates remain open.
- Machine evidence: `vote-health-supplementary-2025-26-summary-totals-20261006.json`
  and `clean-room-recovery-20261006-vote-health-2025-26.json`.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2013/14

- Profile `vote-health-supplementary-2013-14-category-totals/v1` is pinned to
  the captured 44-page Treasury PDF (SHA-256
  `1ec8cf9e4c33d027f3ed02593ab3e8c7cab89883d5b286e0cf4aa4b1e947f5a2`). It
  emits six named totals from pages 2–6, retaining the three printed `$000`
  columns, raw adjustment/dash tokens and 18 field-lineage rows.
- The persistent Silver manifest is
  `c4462b1e042ff7e7f9ff477fb7fe9e0b6e5d525e06cf00bce5b246c01bf2cf2d`.
  Two independent clean-room builds match it and leave Bronze unchanged.
- Focused checks passed 523 tests with 10 skips; profile coverage is 100% line
  and branch. `./scripts/validate.sh` passed 7,566 tests with 10 skips and
  97.68% overall coverage against the 80% floor. All configured formatting,
  lint, typing, schema, parity, mutation, security and supply-chain gates passed.
- Rights remain `not_evaluated`; only the six named rows are normalized.
  Remaining PDF content, cross-edition comparisons, publication and whole-track
  completion are not asserted. Machine receipt and integrated recovery output
  are linked from `index.md`.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2015/16

- Profile `vote-health-supplementary-2015-16-category-totals/v1` is pinned to
  the captured 46-page Treasury PDF (SHA-256
  `694aece23fdb2eac82d96e5dc075339f39ba481b12b33a03db2de5596cf2a47d`). It
  emits seven named totals from pages 2–6, retaining the three printed `$000`
  columns, parenthesized adjustments, and 21 field-lineage rows.
- Persistent Silver manifest SHA-256 is
  `7fa058e52dadf84ec345b2e9352cde12a066855f45e52e72e871e74028ad46cd`.
- Focused checks passed 521 tests with 10 skips; module coverage is 91.67%
  against the 80% floor. Integrated recovery rebuilt twice, matched persistent
  output digests, and confirmed Bronze unchanged. `./scripts/validate.sh` passed
  with 7,580 tests, 10 skipped, 97.64% overall coverage, 56 schemas and 46
  representative documents, 9/9 parity checks, and mutation, security and
  supply-chain gates passed.
- The census records Treasury's CC BY 4.0 notice, while normalized-fact rights
  remain `not_evaluated`. Other PDF rows/pages, cross-edition comparison,
  publication and track completion are not asserted.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2016/17

- Profile `vote-health-supplementary-2016-17-category-totals/v1` is pinned to
  the captured 45-page Treasury PDF (SHA-256
  `5a07182b093c129e4e6ea69bb47679a1ba79ec96b4cdf6196d4590b42c17531f`). It
  emits seven named totals from pages 2–5, retaining three printed `$000`
  columns, source labels, raw tokens, and 21 field-lineage rows.
- Persistent Silver manifest SHA-256 is
  `3675793bbb06c28be58d49ae0399baec4662748fb099bb53757e66843d03f18a`. The
  integrated recovery rebuilt this profile twice, matched persistent output
  digests, and confirmed Bronze objects unchanged; full recovery remains
  `partial_with_blockers` for other required products.
- Focused profile, source-operation, and recovery tests passed (522 passed,
  10 skipped); the adapter has 91.67% line and branch coverage. The required `./scripts/validate.sh` passed with 7,587 tests, 10 skipped,
  97.63% coverage against the 80% floor, 56 schemas/46 representative
  documents, 9/9 differential parity, and mutation, security, and supply-chain
  gates passed.
- The census records Treasury's CC BY 4.0 notice, while normalized-fact rights
  remain `not_evaluated`. Other source rows/pages, cross-edition comparison,
  publication, and track completion are not asserted.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2017/18

- Profile `vote-health-supplementary-2017-18-category-totals/v1` is pinned to
  the captured 48-page Treasury PDF (SHA-256
  `f2c49d272af66dea8cc3cf0d705d4f953d5690a3c71a647fbb43d7ba8769b059`). It
  emits seven named totals from pages 2–5, retaining three printed `$000`
  columns, source labels, raw tokens, and 21 field-lineage rows.
- Persistent Silver manifest SHA-256 is
  `a859be3ac70f022a3c0e236141e6dca1135afdbd85a62a7b436ab32c1a2bd3e2`. The
  integrated recovery evidence and final validation results are recorded in
  the machine receipt.
- Focused profile, source-operation, and recovery tests passed (523 passed,
  10 skipped); adapter line and branch coverage is 91.67%, above the 80%
  floor. `./scripts/validate.sh` passed with 7,594 tests, 10 skipped, 97.61%
  coverage against the 80% floor, 56 schemas/46 representative documents,
  9/9 differential parity, and mutation, security, and supply-chain gates. The
  census records Treasury's CC BY 4.0 notice, while
  normalized-fact rights remain `not_evaluated`. Other source rows/pages,
  cross-edition comparison, publication, and track completion are not asserted.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2011/12

- Profile `vote-health-supplementary-2011-12-category-totals/v1` is pinned to
  the captured six-page Treasury PDF (SHA-256
  `71b905562f6701923961b47578a638a7fbed3731d5d1840fa55b8955300ce0d9`). It
  emits seven edition-specific totals from pages 2–5, retaining three printed
  `$000` columns, dash/null and parenthesized source tokens, and 21 field-lineage
  rows. Departmental and non-departmental other expenses remain separate.
- Persistent Silver manifest SHA-256 is
  `4697ff8edc1a5590d1435e68b4b95fff8f5f393dbcd3870684f26c58510af7a6`. The
  integrated recovery rebuilt this profile twice, matched persistent output
  digests, and confirmed Bronze objects unchanged; broader recovery remains
  `partial_with_blockers`.
- Focused profile, source-operation, and recovery tests passed (524 passed,
  10 skipped); adapter line and branch coverage is 93.75%, above the 80% floor.
  The required `./scripts/validate.sh` passed with 7,601 tests, 10 skipped,
  97.60% coverage against the 80% floor, 56 schemas/46 representative
  documents, 9/9 differential parity, and mutation, security, and supply-chain
  gates passed.
- The census records Treasury's CC BY 4.0 notice; normalized-fact rights
  remain `not_evaluated`. Other source rows/pages, cross-edition comparison,
  publication, and track completion are not asserted.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2010/11

- Profile `vote-health-supplementary-2010-11-category-totals/v1` is pinned to
  the captured seven-page Treasury PDF (SHA-256
  `a5f65c3d741ebc0e426fd8ca5ce4da088718fbfc3930ba2720958ecf3cee556d`). It
  emits six edition-specific totals from pages 2–6, retaining the three
  printed `$000` columns, parenthesized adjustment tokens, and 18 field-lineage
  rows. The separate information-supporting PDF is outside this profile.
- Persistent Silver manifest SHA-256 is
  `d47c18766dc24299aa4004ade3a765e025e109a961377aecb124b4e477eb4951`. The
  integrated recovery receipt records two Bronze rebuilds, repeat stability,
  output digest parity, and unchanged Bronze objects.
- Focused profile, source-operation, and recovery tests passed (525 passed,
  10 skipped). `./scripts/validate.sh` passed with 7,608 tests, 10 skipped,
  97.59% coverage against the 80% floor, 56 schemas/46 representative
  documents, 9/9 differential parity, and mutation, security, and supply-chain
  gates passed.
- The source census records Treasury's CC BY 4.0 notice; normalized-fact
  rights remain `not_evaluated`. Other source rows/pages, cross-edition
  comparison, publication, and track completion are not asserted.

## 2026-10-07 — Vote Health Supplementary Estimates category totals 2007/08

- Profile `vote-health-supplementary-2007-08-category-totals/v1` is pinned to
  the captured 36-page Treasury PDF (SHA-256
  `e76311821f75c2b02c82c8c63d771b9948eb0547caa1af40df662213588ec9f8`). It
  emits six source-labeled totals from pages 2–6, retaining the three `$000`
  columns, a dash token, 18 lineage rows, and five partial-page dispositions.
- Persistent Silver manifest SHA-256 is
  `1a70ef4d79b925096739290c1b20496d33c52c9c254397aa823021196618b84d`. Two
  integrated recovery builds match it byte-for-byte; Bronze remains unchanged.
- Focused profile, source-operation, and recovery tests passed (528 passed,
  10 skipped). The first full harness stopped on Ruff PT018 in the new test;
  after splitting the assertion, `./scripts/validate.sh` passed with 7,629
  passed, 10 skipped, 97.55% coverage against the 80% floor, 56 schemas/46
  representative documents, 9/9 parity, and all mutation, security, and
  supply-chain gates passed.
- Treasury's CC BY 4.0 notice is recorded; normalized-fact rights remain
  `not_evaluated`. Cross-edition comparison, publication, and overall track
  completion are not asserted.

## 2026-10-07 — Vote Health Supplementary Estimates category totals 2008/09

- Profile `vote-health-supplementary-2008-09-category-totals/v1` is pinned to
  the captured seven-page Treasury PDF (SHA-256
  `4cb75bd49333e616f1693b478be3f8e98e8a986aed0485993311febe3fb534cf`). It
  emits six edition-specific totals from pages 2–6, preserving the three
  printed `$000` columns, adjustment tokens, 18 field-lineage rows, and five
  partial-page dispositions.
- Persistent Silver manifest SHA-256 is
  `86e07787f7b49c26cc30aa410f9d17628bffa79e2ec28ae1d51771d8bbe5de9a`. Two
  integrated recovery builds match it byte-for-byte; the recovery confirms
  unchanged Bronze objects.
- Focused profile, source-operation, and recovery tests passed (527 passed,
  10 skipped). `./scripts/validate.sh` passed: 7,622 passed, 10 skipped,
  97.56% coverage against the 80% floor, 56 schemas/46 representative
  documents, 9/9 differential parity, and all mutation, security, and
  supply-chain gates passed on the final rerun. An earlier xdist run hit a
  transient Hypothesis slow-generation health check in an unrelated test; the
  isolated test and full rerun passed.
- The source census records Treasury's CC BY 4.0 notice; normalized-fact
  rights remain `not_evaluated`. Other source rows, cross-edition comparison,
  publication, and overall track completion are not asserted.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2009/10

- Profile `vote-health-supplementary-2009-10-category-totals/v1` is pinned to
  the captured seven-page Treasury PDF (SHA-256
  `c6ed655b1dbca81b0fc54ef62547b71d5f984c6556cfdc77b6299c1bcc870a0e`). It
  emits six edition-specific totals from pages 2–6, retaining the three
  printed `$000` columns, parenthesized adjustment tokens, and 18 field-lineage
  rows.
- Persistent Silver manifest SHA-256 is
  `ef5c1180f43173878c6c6b9ce82ed02e59ca5253031c987e4a6f0a682d86d795`. The
  integrated recovery receipt records two Bronze rebuilds, repeat stability,
  digest parity with persistent Silver, and unchanged Bronze objects.
- Focused profile, source-operation, and recovery tests passed (526 passed,
  10 skipped). `./scripts/validate.sh` passed with 7,615 tests, 10 skipped,
  97.57% coverage against the 80% floor, 56 schemas/46 representative
  documents, 9/9 differential parity, and mutation, security, and supply-chain
  gates passed.
- Treasury's CC BY 4.0 notice is recorded in the source census; normalized-fact
  rights remain `not_evaluated`. Other source rows/pages, cross-edition
  comparison, publication, and track completion are not asserted.

## 2026-10-06 — Vote Health Supplementary Estimates category totals 2014/15

- Profile `vote-health-supplementary-2014-15-category-totals/v1` is pinned to
  the captured 38-page Treasury PDF (SHA-256
  `99e90dfddd8fc7b6d2bb545148d95f8f3c4c3cbf77760b91103130304176780e`). It
  emits seven named totals from pages 2–6, retaining the three printed `$000`
  columns, parenthesized adjustments, and 21 field-lineage rows.
- Persistent Silver manifest SHA-256 is
  `cb61d26cf178638ef96ec345512f5d3cdf96b25ca99f4dba91f78e7ac99f3310`. The
  integrated recovery built the profile twice from Bronze, matched the
  persistent output digests, and confirmed Bronze objects unchanged.
- Focused checks passed 520 tests with 10 skips; module coverage is 91.67%
  against the 80% floor. `./scripts/validate.sh` passed on this documented tree:
  7,573 tests passed, 10 skipped, 97.66% overall coverage, 56 schemas and 46
  representative documents, 9/9 differential parity checks, and mutation,
  security and supply-chain gates passed.
- The census records Treasury's CC BY 4.0 notice, while normalized-fact rights
  remain `not_evaluated`. Other PDF rows/pages, cross-edition comparison,
  publication and track completion are not asserted. See the machine evidence
  and clean-room recovery receipt linked from `index.md`.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 2006/07

- Profile `vote-health-supplementary-2006-07-overview-totals/v1` is pinned to
  the captured 24-page Treasury PDF (SHA-256
  `f319471bd62ca7302a9984c95fc28036cf7aa68113e9cd9733e6c6b5ac587b43`). It
  emits seven page-3 appropriation rows with six source columns, `$000` units,
  42 field-lineage rows, and one partial-page disposition. Raw dash and `N/A`
  cells remain in lineage; typed numeric values are null.
- Persistent Silver manifest SHA-256 is
  `75398989b383000601e6acd42e0ae88dadb42cdf21533bf39d8901359364e23e`. Two
  integrated clean-room builds match its fact, lineage, and disposition
  digests; Bronze remained unchanged. The wider recovery remains
  `partial_with_blockers`.
- Focused profile, source-operation, and recovery tests passed (530 passed,
  10 skipped). `./scripts/validate.sh` passed with 7,637 passed, 10 skipped,
  97.51% coverage against the 80% floor, 56 schemas/46 representative
  documents, 9/9 differential parity, and all mutation, security, and
  supply-chain gates passed.
- Treasury's CC BY 4.0 notice is recorded; normalized-fact rights remain
  `not_evaluated`. The profile does not normalize the separate Crown Revenue
  table or establish cross-edition comparability, publication, or track
  completion.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 2005/06

- Profile `vote-health-supplementary-2005-06-overview-totals/v1` is pinned to
  the captured 17-page Treasury PDF (SHA-256
  `9907280937726b80a2f623f3879f9bc69814e02a1702a3cb0b2fb39d2d7d7074`). It
  emits seven page-3 appropriation overview rows with six separate source
  columns, `$000` units, 42 field-lineage rows and one partial-page disposition.
  Raw dash and `N/A` tokens remain in lineage; numeric nulls do not replace
  those source tokens.
- Persistent Silver manifest SHA-256 is
  `236008de1ca9747c177cc86347d3050023539b53d8fbc78557d4c4b3fae232dd`. The
  integrated Bronze recovery confirms two repeat-identical builds, matching
  persistent Silver digests, and unchanged Bronze. `./scripts/validate.sh`
  passed with 7,646 tests, 10 skipped, 97.48% coverage against the 80% floor,
  56 schemas/46 representative documents, 9/9 differential parity, and all
  configured mutation, security, and supply-chain gates passed.
- Treasury's CC BY 4.0 notice is recorded; normalized-fact rights remain
  `not_evaluated`. The separate Crown Revenue and Receipts table and other PDF
  pages remain outside this slice. No cross-edition comparability, publication
  or track completion is asserted.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 2004/05

- The pinned profile extracts the nine page-3 appropriation summary rows and
  retains five `$000` columns, including the separately labelled Main Estimates
  baseline. It emits 45 field-lineage rows and one partial-page disposition.
- Persistent Silver manifest SHA-256 is
  `5979de6bb60983d98cbc39be8a596ea5eef4f4414b021ea080e447695a3416a9`;
  payload digests and Bronze identity are in the linked machine evidence.
  Integrated recovery rebuilt twice from Bronze, matched the Silver payload
  digests and confirmed Bronze immutability. The overall receipt remains
  `partial_with_blockers` for other sources and products.
- Focused profile, source-operation, and recovery tests passed (530 passed,
  10 skipped). `./scripts/validate.sh` passed on the final implementation:
  7,651 passed, 10 skipped, 97.46% coverage against the 80% floor, 56 schemas
  and 46 representative documents, 9/9 differential parity, and all mutation,
  security, and supply-chain gates passed.
- The census records Treasury's CC BY 4.0 notice; normalized-fact rights remain
  `not_evaluated`. Detailed Part B1 rows, other pages and cross-edition claims
  are excluded. See the machine evidence and recovery receipt linked from
  `index.md`.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 2001/02

- The pinned profile extracts the nine page-2 appropriation summary rows and
  retains five `$000` columns, including the separately labelled Main Estimates
  baseline. It emits 45 field-lineage rows and one partial-page disposition.
- Persistent Silver manifest SHA-256 is
  `c1150393b8fce05ecbf18cd3a608adbf8630f1573e8753abef1387833e0a769a`;
  payload digests and Bronze identity are in the linked machine evidence.
  Integrated recovery rebuilt twice from Bronze, matched the Silver payload
  digests and confirmed Bronze immutability. The overall receipt remains
  `partial_with_blockers` for other sources and products.
- Focused profile, source-operation, and recovery tests passed (532 passed,
  10 skipped). `./scripts/validate.sh` passed on the final implementation:
  7,657 passed, 10 skipped, 97.44% coverage against the 80% floor, 56 schemas
  and 46 representative documents, 9/9 differential parity, and all mutation,
  security, and supply-chain gates passed.
- The census records Treasury's CC BY 4.0 notice; normalized-fact rights remain
  `not_evaluated`. Detailed Part B1 rows, other pages and cross-edition claims
  are excluded. See the machine evidence and recovery receipt linked from
  `index.md`.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 2000/01

- The pinned profile extracts the nine page-2 appropriation overview rows and
  preserves five `$000` columns, including the separate Main Estimates baseline.
  It emits 45 field-lineage rows and one partial-page disposition.
- Persistent Silver manifest SHA-256 is
  `adf18895ac9141dc93e5a0e86b9f53e771282b74c8a21f437bf07c6bbed6b15f`; output
  digests and source identity are recorded in the machine receipt.
- The source census records Treasury's CC BY 4.0 notice. Rights for normalized
  facts remain `not_evaluated`; detailed Part B1 rows, other pages and cross-
  edition claims are excluded. No publication is performed.
- `./scripts/validate.sh` passed on the final tree: 7,663 tests passed, 10
  skipped, 97.42% coverage against the 80% floor, 56 schemas/46 representative
  documents, differential parity 9/9, and all mutation, security, and supply-
  chain gates passed. Conductor validation passed with 93 tracks and no errors.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 2002/03

- The pinned profile extracts nine page-2 appropriation overview rows and
  preserves five `$000` columns, including the separate Main Estimates baseline.
  It emits 45 field-lineage rows and one partial-page disposition.
- Persistent Silver manifest SHA-256 is
  `1fddf962d3b65ba2d0b850c63bcf29a51b71ca217b04b8774f025bff84a390de`; the
  integrated clean-room receipt confirms two identical Bronze rebuilds, matching
  payload digests, and unchanged Bronze. The overall recovery remains
  `partial_with_blockers` for other track items.
- The source census records Treasury's CC BY 4.0 notice. Rights for normalized
  facts remain `not_evaluated`; detailed Part B1 rows, other pages and cross-
  edition claims are excluded. No publication is performed.
- `./scripts/validate.sh` passed on the final tree: 7,679 tests passed, 10
  skipped, 97.40% coverage against the 80% floor, 56 schemas/46 representative
  documents, differential parity 9/9, and all mutation, security, and supply-
  chain gates passed. Conductor validation passed with 93 tracks and no errors.

## 2026-10-07 — Vote Health Supplementary Estimates overview totals 1999/2000

- The edition-pinned profile extracts nine page-3 summary rows from the captured
  11-page PDF, preserving five printed `$000` columns, the separate Main
  Estimates baseline, 45 lineage records, and one partial-page disposition.
- Persistent Silver manifest SHA-256 is
  `90b01a953007932a3f59d577e1260ce6b9b7a6fcf53f017a4e728cde4437fef9`. The
  integrated clean-room receipt confirms repeat-identical payloads, a match to
  persistent Silver, and unchanged Bronze. Wider recovery remains
  `partial_with_blockers`.
- Treasury's CC BY 4.0 notice is recorded; rights for normalized facts remain
  `not_evaluated`. Page 4 onward, other source pages, and cross-edition
  comparisons are excluded; publication was not performed.
- `./scripts/validate.sh` passed: 7,673 tests passed, 10 skipped, 97.38%
  coverage against the 80% floor, 56 schemas/46 representative documents,
  parity 9/9, and all mutation, security, and supply-chain gates passed.
  Conductor validation reported 93 tracks and no errors. The harness used an
  external-SSD `TMPDIR` after local temporary storage was exhausted.

## 2026-10-07 — Fiscal Gold cross-product query matrix

- The named DuckDB read-only query contract now has a two-period matrix across
  nominal, GDP-share, per-capita, and household-CPI benchmark products. It
  verifies shared numerator IDs/values, exact source identity, GDP denominator
  IDs, population status, and quarter-level CPI lineage while preserving the
  missing-population status for FY2024.
- A requested `real` table remains rejected by the allowlisted query contract.
  The admitted CPI product is a household purchasing-power benchmark, not an
  approved health-spending deflator; source base, GST treatment, and period
  comparability do not authorize a real-spending view.
- Focused validation: `tests/domains/health_appropriations/test_fiscal_analytical_operations.py`
  passed (11 tests). The wider golden matrix across Crown, Budget, revisions,
  classifications, portfolio and CPB products remains open.

## Analytical context reconciliation — 2026-10-16

The current register distinguishes quarterly discovery leads, captured annual
population data and three implemented Fiscal analytical policies. Their exact
policy constants and receipt source pins match; the three retained outputs,
three Bronze originals, Treasury period observation and combined Gold manifest
passed fixity readback. No original capture or clean-room rebuild is claimed.

The current census now pins the revised register, and the recovery harness
pins that census. Two source-health builds from the retained capture manifest,
Bronze CAS and layout baseline were byte-identical. Compared semantically with
the previous current report, only its context-census input digest changed;
source facts, counts, rights and qualification states are unchanged.
`source-measure-review-20261016.json` records the current bounded policies and
evidence closure; the dated 2026-10-06 review and all dated recovery receipts
remain unchanged. The five focused census/register/review/recovery suites
passed 122 tests. Required full revalidation passed: 7,675 tests passed, 10 skipped; 97.38% coverage against the 80% floor; 56 schemas/46 representative documents; parity 9/9; all mutation, hygiene, security and supply-chain gates passed, including strict 113-component SBOM validation. Conductor reports 93 tracks and no errors. Hosted validation remains a separate gate.

## Canonical Gold named queries — 2026-10-17

The eight-product reader, CLI and read-only MCP endpoint pass 131 focused and
neighboring integration checks, relevant lint/format, focused typing and
Conductor validation (93 tracks, no errors). Two native source-bound Gold builds
have identical digests; exact direct-Arrow readback, actual CLI/MCP parity,
repeat-query identity and no-write checks pass for every product. Historical
and Budget are explicitly truncated at 200 rows. Native assurance exposed and
resolved host-dependent timestamp formatting by restoring the validated input
Arrow schema, retaining the external-access prohibition. See
[query evidence](./canonical-gold-queries-20261017.md) for pins, counts, retained
logs and limits.

The required `./scripts/validate.sh` passed on implementation commit
`ff91c196c3fd9c81d3cbec186a7ca64d259100cf`: 7,693 tests passed, 10 skipped;
97.39% coverage against the 80% floor; 56 schemas/46 representative documents;
parity 9/9; all mutation, hygiene, security and supply-chain gates passed,
including the 113-component SBOM. Conductor reports 93 tracks and no errors.
The external durable `validation.log` and `validation.exit` record exit 0.
The follow-up commit records this evidence only; hosted checks must qualify
the final PR head before merge.
No source/rights/publication or whole-track completion is claimed.

## Canonical Gold metadata — 2026-10-17

The new bounded canonical profile projects full schemas and literal period
inventories for all eight fact products through the existing metadata system.
92 focused checks pass; typing/lint/format, 59 schemas/49 documents and Conductor
93/no errors pass. Final native v4 projection covers 13 recordsets / 1,184 rows,
including 800 canonical rows, with exact independent schema/token readback,
offline graph parsing, byte-identical rebuilds and installed CLI/MCP parity.
Pre-change/current Fiscal/Budget metadata payloads are byte-identical. Legacy
schema identifiers/bytes remain unchanged; canonical metadata uses new v4/v2
schemas. See [native evidence](./canonical-gold-metadata-20261017.md) for source
pins, final receipt and preserved pre-review evidence. Local and hosted
delivery remain separate gates; rights/publication/federation and final
track completion are not promoted.

Required `./scripts/validate.sh` passed on implementation
`b2fde77e67555913f5a32369f9253ed1260c210e`: 7,698 tests passed, 10 skipped;
97.43% coverage against the 80% floor; 59 schemas/49 representative documents;
parity 9/9; all mutation, hygiene, security and supply-chain gates passed,
including the 113-component SBOM. Conductor reports 93 tracks and no errors.
Session 9819 and the durable `validation.exit` record exit 0. The subsequent
commit records evidence/task status only; hosted checks must qualify the final
PR head before protected merge.

## Fresh canonical recovery wiring — 2026-10-17

The new input builder consumes only five pinned originals and locked exact
observation definitions, producing separate raw/canonical input trees for both
Gold builds. Twenty focused recovery checks and relevant lint/typing pass.
Downstream contracts exercise all eight queries and 13-recordset composite
metadata. Preflight context/provenance differences and exact historical replay
are recorded in [the slice evidence](./canonical-recovery-inputs-20261017.md).
Native full integration and required whole-repository/hosted validation remain
pending; no whole-track or rights/publication completion is claimed.

Native recovery now exits 0 on implementation `a8b8fcea74a8889c90fb68ddabf0012a68489f49`. The bounded [native receipt projection](./canonical-recovery-validation-20261017.json) retains definitions, source/output pins, query counts and metadata reconstruction. Forty-seven input-tree files and 53 Gold files repeat; composite metadata covers 13 recordsets/1,184 rows and nine repeat-identical files. All eight bounded query results match typed facts, with truncation recorded, and no Bronze mutations occur. The actual completion receipts also validate against the corrected JSONL-aware schema; no production code changed after native assurance. Required full/hosted validation remains pending.

Full local `./scripts/validate.sh` passed on clean
`7946b24392d1053b76d3ef77cbc49263a08b3f23` with exit 0 (durable
`validation-2.log`/`validation-2.exit` outside Git): 7,708 passed, ten skipped,
97.44% coverage against the 80% floor, 60 schemas/50 representative documents,
parity and all mutation/hygiene/audit/licence/secrets/SBOM gates. SBOM has 113
components; external CDX validation was explicitly skipped. The bounded fresh
canonical-input recovery task is now complete locally; broader Phase 9 remains
in progress. This result bookkeeping changes only track documentation/evidence;
protected exact-head hosted validation and merge/prune remain pending.

## PR #691 ordered-query verification completed locally — 2026-10-17

Corrected native verification on clean `49becbc7b05982412834293dd6fcd7f912a19b48`
passed (exit 0; targeted receipt SHA256
`08c8cc1657489cbceb0ab4387f7c81eede29b37cfdfc7f109c1777435a67f2e5`). Both
fresh input inventories (47 files each), Gold inventories (53 files each) and
645 returned query-row digests match the original full native output pins. The
new independent typed-column ASC NULLS LAST oracle proves each exact ordered
slice, including truncation, counts and duplicate multiplicity. Fresh paired
BEFU/HYEFU/Pharmac/MoH inputs were rebuilt alongside the five original-source
pairs; source receipt schemas pass and Bronze is unchanged. Full actual outputs
are retained outside Git. The original full native receipt remains unchanged;
its metadata evidence is not relabelled as a second metadata run.

Repeated full `./scripts/validate.sh` passed on that same clean code head:
7,712 passed, ten skipped, 97.44% coverage against the 80% floor, 60 schemas/50
representative documents, parity, all mutation/hygiene/audit/licence/secrets/SBOM
gates. SBOM has 113 components; external CDX validation was explicitly skipped.
Durable `ordered-native-1.*` and `validation-3.*` logs/exit statuses remain in
`/Volumes/PortableSSD/tmp/canonical-recovery-inputs-20261017/`. The subsequent
bookkeeping commit changes only track evidence/documents. Local review correction
is verified; corrected exact-head hosted checks, thread resolution and protected
merge/prune remain pending. Whole-track recovery/source/rights/standards gates
remain open. See `canonical-recovery-ordered-validation-20261017.json`.

## 2002 BEFU/DEFU census extension — 2026-10-17

The [source observation](./source-census-2002-befu-defu-20261017.json) adds five
official discovery locators, taking the historical register to 76. The
[new current review](./source-measure-review-20261017.json) preserves earlier
dated receipts and records a separate DEFU Core Crown expense definition.
Browser href and page-rights readback resolved the forecast locator; the
annex/glossary extent discrepancy remains fail-closed pending native evidence.
All 41 focused census/review tests and relevant static checks pass. Capture,
resource rights, native layouts, analytical joins, whole-edition completion and
full/hosted validation are not claimed by this focused evidence.

## 2002 census local assurance — 2026-10-17

The required `./scripts/validate.sh` passed on clean
`3f57c983b7689b741ae0952ed9d16a0bbb9511b9`: 7,713 passed, ten skipped,
97.44% coverage against the agreed 80% floor; 60 schemas/50 representative
documents, parity and all mutation/hygiene/audit/licence/secrets/SBOM gates.
The SBOM contains 113 components; external CDX validation was explicitly
skipped, so no independent external standards-validator pass is claimed.
Durable logs and exit 0 are retained in
`/Volumes/PortableSSD/tmp/health-census-defu-2002-20261017/validation-1.*`.
Direct value comparison also verifies all 71 earlier resource rows and all
nine earlier reviewed series unchanged. Current strict source-review validation
binds all 33 evidence files, ten series and 76 discovery locators without
rights or analytical admission. The following commit changes only unpinned
track evidence/status; source observations and review evidence hashes remain
unchanged. Local slice work is complete; protected exact-head delivery remains
pending, and whole-source/Health completion is not claimed.

## BEFU 1998 census — 2026-10-17

The [bounded observation](./source-census-befu-1998-20261017.json) records ten
official PDF links, separate source scopes/status labels, reader-layout gaps
and the qualified withdrawal notice. The
[new current review](./source-measure-review-20261017-1998.json) binds 12
source-separated series and 86 historical discovery locators, preserving
all earlier resource rows and reviewed series. Forty-two focused tests pass.
Native byte/layout verification, resource rights, ISO currency, cross-basis
joins, whole-edition closure and full/hosted validation remain open.

## BEFU 1998 local assurance — 2026-10-17

The required `./scripts/validate.sh` passed on clean
`81eae29c2de632e6affb9ded72d780fb27a6b812`: 7,714 passed, ten skipped,
97.44% coverage against the 80% floor; 60 schemas/50 representative documents,
parity and all mutation/hygiene/audit/licence/secrets/SBOM gates. SBOM has 113
components; external CDX validation was explicitly skipped. Durable log and
exit 0 are retained under
`/Volumes/PortableSSD/tmp/health-census-befu-1998-20261017/validation-1.*`.
Current source-review validation binds 35 repository evidence files, 12
source-separated descriptors and 86 discovery locators. All 76 earlier
resource objects and ten earlier reviewed series compare unchanged. The
following bookkeeping commit changes only unpinned track evidence/status;
source observations and their evidence hashes are unchanged. Local slice work
is complete; exact-head hosted validation and protected delivery remain pending.
Whole-edition/history, native-layout/fixity, rights and cross-basis qualification
gates remain open; this does not close the Health track.

## BEFU 1999 census — 2026-10-17

The [source observation](./source-census-befu-1999-20261017.json) records seven
exact official links and distinct year-end publication dispositions. The
[current review](./source-measure-review-20261017-1999.json) binds 13 descriptors
and 93 historical discovery locators; earlier 86 resources/twelve descriptors
are unchanged. Two new contracts failed before the data/review existed (0.50s);
43 focused inventory/review checks now pass (4.09s). Ruff and whitespace checks
pass. Full local assurance and protected exact-head delivery remain pending.


## BEFU 1999 local assurance — 2026-10-17

The required `./scripts/validate.sh` passed on clean
`bb803cafa53df9d00a6656c168a644728dd11c0b`: 7,715 passed, ten skipped,
97.44% coverage against the 80% floor; 60 schemas/50 representative documents,
9/9 differential parity and all mutation/hygiene/audit/licence/secrets/SBOM
gates. SBOM has 113 components; external CDX validation was explicitly skipped.
Durable log and exit 0 are retained under
`/Volumes/PortableSSD/tmp/health-census-befu-1999-20261017/validation-2.*`.

The first two-worker full run had one existing Gold discovery CLI subprocess
exceed its 30-second timeout after emitting its success receipt (7,714 other
tests passed). The unchanged isolated contract passed in 12.21s, with a 5.49s
test call. A guarded one-worker full rerun then passed all 7,715 tests in
488.21s. Timeout and quality gates were not relaxed; the underlying cause was
not established. The initial failure and isolated logs remain beside the full
rerun evidence. No CLI or product implementation was changed.

Current review binds 37 evidence files, thirteen source descriptors and 93
historical discovery locators. All 86 earlier resources, twelve descriptors,
the captured-source census and prior dated review are unchanged. Corrected the
stale Phase 4 sentence to agree with its existing source-backed retain-both
receipt; this grants no replacements or publication approval. This bookkeeping
commit changes only unpinned track evidence/status. Exact-head hosted checks
and protected delivery remain pending; the whole Health track is incomplete.

## Remaining year-level locator census — 2026-10-17

The [primary-source observation](./source-census-locator-gaps-20261017.json)
adds 38 locators across six editions, giving 131 total and at least one for
all 30 scoped years. All editions remain pending complete source-family
coverage; four related links await content-scope review. Existing captured
records/bytes and prior 93 resource objects are unchanged. The separate
[component-index observation](./health-component-index-discovery-20261017.json)
records exact publisher table/dimension identities and method boundaries,
not a deflator policy or numeric admission.

The [new dated review](./source-measure-review-20261017-locator-gaps.json)
binds 19 source descriptors and 41 evidence files, preserving twelve unaffected
prior descriptors and correcting Vote Health coverage wording against the
existing register. Older dated review bytes remain unchanged. Four selected census contracts began red (1.45s). An older
negative fixture assumed a nonempty missing-year list; it now injects a known
located year as a false gap, preserving the coverage-consistency rejection.
Ruff's statement-count finding was resolved by extracting the historical
coverage assertions into a helper. Latest focused run: 45 passed in 1.39s,
with lint/format/whitespace checks passing. A prior default-TMPDIR cleanup
warning did not recur with the dedicated external temporary root. Logs are
retained under `/Volumes/PortableSSD/tmp/health-census-locator-gaps-20261017/`.
Full local assurance and protected delivery remain pending.


## Current-review coverage consistency correction — 2026-10-17

A further read-only assessment found a stale Vote Health narrative inherited
from the older review: 58 PDFs and ten missing Estimates years, while the
structured aggregate register and validator prove 59 PDFs and nine missing
years. The latter excludes 2008, already present in that register. Added a
contract tying narrative counts to the structured evidence; it failed as
expected before correction (0.63s, `red-coverage-description.log`).

Cancelled only this slice's verified queued guard request PID 8669 before its
harness started, preserving the queue/cancellation receipt and leaving the
other live validation holder untouched. Corrected the new dated review to
59 PDFs / nine missing years, retaining all 93 prior resource objects, all source
values/rights/captures, twelve unaffected descriptors and every older dated
review. This is current inventory reconciliation, not a historical value
replacement. The original thirteen-descriptor preservation check described
the preceding implementation state; it is not claimed for the corrected Vote
Health description. No native captures or broader source-family closure were
added. Later per-edition capture receipts need separate reconciliation and do
not retroactively change the aggregate snapshot's current counts.


## Remaining locator census local assurance — 2026-10-17

The required `./scripts/validate.sh` passed on clean
`7e780458e1d5c49160e85afd5a5d520fc55681b3`: 7,717 passed, ten skipped,
23 warnings, 97.44% coverage against the 80% floor; 60 schemas/50 representative
documents, 9/9 parity and every configured mutation/hygiene/audit/licence/secrets/
SBOM gate. Test execution took 530.03s with one worker. SBOM has 113 components;
external CDX validation was explicitly skipped. Durable log and exit 0 are
retained under
`/Volumes/PortableSSD/tmp/health-census-locator-gaps-20261017/validation-2.*`.
The earlier guard request was cancelled while still queued for the documented
coverage-wording correction; no harness was started on its superseded head.

Conductor's independent exact-head review confirms all 41 evidence hashes,
all 93 prior resource objects unchanged and twelve unaffected prior descriptors
unchanged. The sole earlier descriptor changed is Vote Health inventory
wording/status, reconciled to the existing 59-PDF aggregate register and nine
missing Estimates years. Earlier dated reviews and captured-census bytes remain
unchanged. The new review records 131 locators/19 source descriptors while all
30 editions remain pending full source-family coverage and source-specific
rights/fixity/layout/analytical qualification.

The following bookkeeping commit changes only four unpinned track notes/status.
Source observations, review evidence hashes, tests and product code are unchanged.
Local slice assurance is complete; exact-head hosted checks and protected PR
merge/pruning remain pending. This does not close the Health track.

## Reviewed overview common adapters (2026-10-17)

- [Native parity receipt](reviewed-overview-common-adapters-20261017.json): fourteen profiles, 209 facts, repeated dispatch and unchanged originals.
- [Scope and qualification](reviewed-overview-common-adapters-20261017.md): thirteen new common registrations; operational adoption and whole-phase assurance remain open.


## 17 October 2026 — retained capture cohort reconciliation

[Inventory and scope](./capture-inventory-20261017.md),
[deterministic metadata projection](./capture-inventory-20261017.json),
[build pins](./capture-inventory-build-20261017.json), and
[independent native CAS receipt](./capture-inventory-fixity-20261017.json).
152 URL identities, 84 recorded captures; all 84 captured URL/version CAS
identities freshly verified (46,245,283 bytes). No WARC replay, rights or
whole-corpus completion claim. Frozen-tree full assurance and PR delivery pending.


## 17 October 2026 — distinct 2019/20 Supplementary Addition

[Source census/layout and scope](./supplementary-addition-2019-20-census-20261017.md),
[layout observations](./supplementary-addition-2019-20-census-layout-20261017.json),
[native request/CAS/WARC proof](./supplementary-addition-2019-20-capture-verification-20261017.json),
[new bounded inventory](./capture-inventory-20261017-addition.json), and
[repeat-build/input/proof-set accounting](./capture-inventory-build-20261017-addition.json).
153 URLs /85 recorded captures; all 152 prior resource rows remain exactly
unchanged. No amount normalization, new rights approval or whole-corpus closure.
Full exact-tree validation and PR delivery pending.


## 17 October 2026 — PR #698 delivery and operational overview integration

PR #698 merged through the normal protected path at
`901f7ae60bb3b6d81182cc09a4534782073a6f4a` after all applicable checks
passed on `f41fb82139fb29f91e170803fc627c5e20f9d103` (Windows17m57s).
Fetched remote main contains both head and merge; no unique commits or dirty
changes remained. Local/remote topic and stale tracking ref pruned; primary
worktree retained. External receipt:
`/Volumes/PortableSSD/tmp/health-supplementary-addition-census-20261017/merged-and-pruned.json`.
Operational bridge task is now in progress; Phase3 remains incomplete.


Operational native proof completed0 on clean276a8225 under the actual shared
guard:14 profiles,209 facts,42 reference Parquet files per repeat, two identical
new manifest sets and70 observed common dispatches with direct normalization
forbidden. All original/reference files were independently SHA-checked and
remained unchanged. See [scoped proof](./overview-operational-dispatch-20261017.md)
and [run inventory with retained manifest pins](./overview-operational-dispatch-20261017.json).
Focused545 passed/10 skipped, Ruff and typing passed. Full final-tree harness
is pending. No general recovery-profile or phase-completion claim.


PR #699 historical full assurance on cleanfcd1c6dd completed0:7,767 passed,
10 skipped,23 warnings,308.42s,97.39% coverage;62 schema validations/52documents,
parity9/9, all configured mutation/hygiene/audit/licence/secrets/SBOM gates,
113components; external CDX explicitly skipped. Review correction2e9cd674 then
passed546 focused/10 skips and repeated native14-profile209-fact42-Parquet
parity/pinned-readback with all14 manifest pins unchanged.
See [review-fix proof](./overview-operational-dispatch-review-fix-20261017.json).
Full final-tree assurance, hosted checks, thread resolution and merge pending.


## 17 October 2026 — PR #699 delivery

The operational overview bridge and symlink-parent review correction were
merged normally in PR #699 as071cfef55d96c810edf0c56ee4b1eef9bb3cad65 at
02:47:31Z. Exact headbadc3a6f541a16f5b145acd1dc9c3652bc9338be passed full
local assurance (7,768 tests/10 skips/23 warnings,281.24s,97.38%,62 schema
validations/52documents,9/9 parity,configured mutation/hygiene/supply-chain
gates and113-component SBOM; externalCDX explicitly skipped) and every
applicable hosted check. Windows17m34s,macOS8m16s,Ubuntu7m17s; CodeQL,lint
and patch coverage passed. The actual review thread was resolved after
red/green/native/full/current-hosted proof. Fetched main contains head and
merge, with no unique commits or dirty changes. Topic/local/tracking refs
pruned after proof; primary worktree retained. External receipt:
`/Volumes/PortableSSD/tmp/health-overview-operational-dispatch-20261017/merged-and-pruned.json`.

Phase4issue #210 stays open: completed donor-functional parity is not
M07/AC03 coverage of all detected workbook areas. Metadata-only reconciliation
found three exact retained stage receipts and nine missing historical receipt
locators; old temporary12-stage roots are absent. Two forecast partial mappings
and a bounded30-coordinate historical ledger mapping add traceability only,
without output verification, whole-sheet assertions, repairs or publication.
Conductor independently reviewed their bounded meaning. The158 globally
unresolved structural units are not a count of unimplemented extractions.
The next implementation is the two reviewed forecast common adapters; census
residuals and wider source/operational/phase gates remain explicit.


Forecast native verification completed0 under the shared guard at clean
cb48363b:four unchanged legacy/versioned API profiles,40 native facts,16 files
per repeat, including byte-identical original manifests; two common successors,
20 facts and120 lineage entries with exact non-normalized cell/sheet losses.
Direct filesystem normalization was forbidden during common extraction.
Original observation tokens are pinned by legacyPLAN/source census, preserving
identity spellings. All originals/references remain unchanged. Independent
Conductor read-only review verified source-code hashes and all eight regenerated
manifest pins without replaying sources. See
[proof](./forecast-common-adapters-20261017.json). Full final-tree harness and
PR/hosted assurance remain pending; no phase or operational-adoption closure.


## Forecast implementation evidence rebinding — 2026-10-17

The first exact-head full harness at fc332cfa stopped with 7780 passed,
2 failed, 10 skipped (97.33% coverage): the current context census still pinned
the previous forecast implementation. Failure evidence was retained before edits.
Only that implementation evidence hash is refreshed; every series, selector,
qualification and rights claim is unchanged. The exact previous census is retained
as `context-census-pre-forecast-common-20261017.json` (579e63a757cae410a26e0f371ae8cb79bf31e10e30c46ccb652789b160199708).
Historical recovery explicitly reads this snapshot with unchanged product/input
pins; this is historical replay evidence, not current implementation validation.
The original dated source-measure review remains unchanged; its successor
`source-measure-review-20261017-forecast-binding.json` refreshes only the census
pin. Current source-health builder defaults remain current. Tests which preserve
recorded report receipts explicitly use the historical input; a context refresh regression verifies the current context pin is emitted while
independently source-bound capture/layout evidence stays valid. A proposed
context-invalidation assertion failed (127 passed, 1 failed); inspection showed
that resource evidence correctly binds only the source census, so that assertion
was corrected without changing the builder. No verifier is
weakened and no source/product is recaptured or silently replaced. See
[rebinding receipt](./forecast-evidence-rebinding-20261017.json).
Focused checks and the full exact-tree rerun are required before PR creation.


## Forecast common adapter local assurance complete — 2026-10-17

Full `./scripts/validate.sh` completed0 at clean frozen
521681914f2504eaa2f131fbb223aefe5975c511: 7783 passed, 10 skipped,
23 warnings in345.64s, 97.38% coverage (unchanged80% floor); typing0,
62 schemas/52 representative documents, differential parity9/9, all mutation,
hygiene, audit, licence, secret and SBOM gates passed (113 components).
External CDX validation remains skipped by existing configuration. The exact
[tested-head/log receipt](./forecast-common-adapters-validation-20261017.json)
distinguishes the local tested tree from this documentation-only closeout.
The current review link now selects the successor implementation binding;
historical review and census remain preserved. No production code, tests,
runtime, schemas or pinned validation inputs change after the full run.
Affected Conductor/hygiene/whitespace checks qualify this closeout; required
hosted checks must qualify the final PR head before protected merge/prune.
The four-API native proof is unchanged; Conductor independently reviewed the
rebinding and source-specific report compatibility. Operational adoption and
all broader source/donor/rights/phase gates remain open.


## Forecast operation adoption started — 2026-10-17

PR #700 merged normally at03:47:56Z, merge58362d4d6bb9eb5a6ad54a83cd4a6c95d9150aba,
headbf0b8d5f697d01fd1f1cc2bc645f15005ffee381. All required/applicable checks
passed, including Windows20m46; no unresolved review threads. Fetched main
contains both commits, no unique changes remained, and clean local/remote/tracking
topic refs were pruned; primary checkout retained. Windows ran7763tests/30skips,
Ubuntu/macOS7767/26; native local parity and full7783/10 remain separately scoped.
The next approved bounded Phase3/8 task adopts the two actual common forecast
outputs in operations. Existing formula rejection/partial-package behavior is an
explicit compatibility contract. No broader phase, rights or donor closure.


## Forecast operation bridge implementation checkpoint — 2026-10-17

New bridge consumes common dispatch facts/lineage, verifies all shared fields
and loss rows against auxiliary metadata parsed from the same immutable Bronze
snapshot, then emits unchanged three Parquet tables plus a versioned operation
manifest. Public compact receipts and rejected-cell partial-package behavior
remain unchanged. Readback requires an independent manifest hash and trusted
source/profile/context; verifies exact metadata types/values via canonical JSON,
rejects duplicate keys and unexpected files, regenerates table pins, checks every
bounded output snapshot and final manifest stability. Symlink ancestors are
refused before output, and interrupted directories cannot be overwritten.
Initial red collection check and old-manifest comparison failures are retained.
A real False-versus-zero tamper case exposed dictionary equality accepting
changed types; canonical JSON comparison fixes it without weakening validation.
Focused forecast/operation suites:604 passed/10 skipped in11.29s; Ruff clean,
basedpyright0 errors/warnings. All three previously qualified native parser,
adapter and registry source files remain unchanged. Native proof, full harness,
review resolution and hosted delivery remain pending; see
[checkpoint](./forecast-operational-dispatch-20261017.json).


## Forecast operational native verification — 2026-10-17

At frozen clean6a15374d2c2bbcdf1a3d42044459d2d983a5f45b, the shared kernel
validation guard ran two actual retained successor sources through source
operations and independent pinned readback, with the direct filesystem normalizer
forbidden. Both preflights wrote nothing; two writes/readbacks per profile
produced20facts/120lineage rows and8files per repeat. Every generated Parquet
hash matches the independent retained native manifest; all new operation
manifests and tables are byte-identical across repeats. Original observation
spellings are bound to the retained source census. Source bytes/stat and all
native reference files remain unchanged. No capture, currency/rights change,
historical repair or phase-completion claim. See
[native proof](./forecast-operational-dispatch-native-20261017.json).
Required full repository assurance and hosted delivery remain pending.


## Forecast operation full local assurance — 2026-10-17

Full `./scripts/validate.sh` completed0 at frozen clean
fafe203816793fc1ea7567081556f608c04b1f1b:7800passed/10skipped/23warnings
in454.49s,97.39% coverage against unchanged80% floor; typing0,
62schemas/52documents,9/9parity, all mutation/hygiene/audit/licence/secret/SBOM
gates passed (113components). External CDX validation remains intentionally
skipped by existing configuration. See the exact
[tested-head receipt](./forecast-operational-dispatch-validation-20261017.json).
The prior full run is retained as failed:7795passed/5 subprocess30s timeouts.
All16 affected module/Gold diagnostic cases passed serially in62.40s; the
fresh full2 passed without code/test/runtime/deadline changes. This proves
non-reproduction, not a host-cause conclusion. Unrelated CPU contention was
independently observed. No FOI implementation changes or relaxed assertions.
Conductor independently checked native verifier/code hashes and all four new
manifest pins without source replay; no blocking finding. This closeout changes
only result documentation/index pointers, not source, tests, schemas or pinned
inputs. Affected documentation checks follow; required hosted checks must
qualify the final PR head before normal merge and clean topic pruning. No broader
phase, donor-area, currency/rights or source-census completion is claimed.


## PR #701 generated-output size finding — correction in progress

Actual thread PRRT_kwDOTo2MOM6tdDD8 identifies fixed8MiB/16MiB readback caps
rejecting native-accepted sources after completed writes. A real208357-byte
synthetic workbook,80034 inventoried cells/80002 preserved-only/10 normalized,
zero rejected, produces a10929247-byte manifest and all4files but compact failure.
The red package/source/native references are retained; an initial import-only
setup failure is separately recorded and is not defect evidence. A fast
source-derived-size assertion also fails on the original code.
Expected hashes and exact lengths are now regenerated from source-derived
Parquet bytes and the native writer's canonical UTF-8 manifest before creating
the output directory. Readback uses those bounds, never candidate stats or
manifest declarations. The independent verifier still requires a retained
external pin and checks its syntax before source parsing; duplicate-key, exact
metadata/type/file-set/hash and final reread controls remain. Producer consistency
uses its source-derived expected pin, distinct from external verification.
Partial package/default-preflight/native API semantics remain unchanged.
Focused610passed/10skipped; typing0 and Ruff clean. Appended/truncated output,
malformed pin, forged metadata and exact bound regressions pass; compact tamper
JSON ensures type/selection tests reach semantics rather than size rejection.
Conductor reviewed the fix without finding a blocking defect. Large-source green,
new native/full/hosted qualification and actual review-thread resolution remain
pending; prior full/CI green results do not qualify this material fix.
See [review-fix evidence](./forecast-operation-size-review-fix-20261017.json).


## PR #701 output-size fix native qualification — 2026-10-17

Combined guarded verification completed0 at frozen clean
2446e13475adb9b436330994d50a443e76c0c30d. The exact retained208357-byte synthetic
source now passes no-write default preflight, explicit write and independently
pinned verification. All80025 common losses are preserved; the10929247-byte
manifest retains its originalb54fb7556e74d12bb55f53f834fb18a991c72b5719811198abc78c6a14ae4357
hash. All4corrected package bytes match the earlier failed package, all3Parquets
match the native reference, and source/red/native evidence remains unchanged.
This is a synthetic contract regression, not official data admission.
Both retained official successor profiles also pass two complete repeat builds
and independently pinned readback with direct filesystem normalization forbidden:
20facts/120lineage rows/8files per repeat. Every generated file hash, including
both new manifests, matches the pre-fix native proof exactly. No original or
source/reference bytes changed. Conductor independently verified the large-case
file hashes and no-write preflight; code review found no blocking defect.
See [review-fix native proof](./forecast-operation-size-fix-native-20261017.json).
A new full exact-tree harness and final-head hosted checks remain required;
actual PR review thread is intentionally unresolved until these qualify the fix.


## PR #701 size-fix full local assurance — 2026-10-17

Fresh `./scripts/validate.sh` completed with exit0 at frozen clean
5f6bf873907ce977f3c6d71aa1fa1b79f5adb4d8: 7,806 tests passed, 10 skipped,
23 warnings in374.46s;97.39% coverage against unchanged80% floor. Typing0,
62 schemas/52 representative documents, parity9/9 and all mutation, hygiene,
audit, licence, secret and SBOM gates passed (113 components). Existing external
CDX validation remains skipped. The material size fix is qualified by this run,
not the earlier pre-fix green tree. Exact head/log/runtime pins are retained in
[final local receipt](./forecast-operation-size-fix-validation-20261017.json).
Only result notes and index pointers follow the tested head; affected checks
qualify this closeout. Required final-head hosted checks, actual review-thread
resolution and normal protected merge/prune remain pending. Native/large-case
proof and all original sources/output identities remain unchanged. No broader
track gate or source/rights/denominator claim is closed.


## Forecast delivery and context operation preparation — 2026-10-17

PR #701 merged normally at05:16:46Z as3fe73c7636a335f5587f767cd8ae249deb534adf.
Final headf2883fcf passed all applicable checks; Windows18m50. The actual size
finding was resolved after checks, no other review threads remained, and fetched
main contains both head/merge with identical treef55038e71d29f1dd41fc2ab81ca32caba4d45737.
Zero unique changes and clean status preceded local/remote/tracking topic pruning;
primary checkout retained. See [delivery receipt](./forecast-operational-dispatch-delivery-20261017.json).
The next five-profile context slice is registered. Read-only preparation verified
five Bronze source hashes plus four surviving native manifests/12table hashes.
June GDP temporary derivative is gone; independently attested historical four-file
pins and current Bronze exist. No source parsing/rebuild/acquisition occurred in
that preparation. CPI vintage aliases and population lineage representation need
explicit source-faithful projection; Conductor guidance requested before coding
those boundaries. Other families and contract preparation continue independently.


## Context operation CPI vintage contract — 2026-10-17

The retained CPI native manifest edb62f4b... binds source f474a6a3... and literal
`Stats-NZ-CPI-2026-Q2`; existing common registration supported only `2026-Q2`.
A fixture regression reproduced preserved-only fallback for the retained label.
The factory now exposes an explicit1.1.0 recorded-label adapter while preserving
legacy1.0.0 behavior. Source context and unresolved mapping vintage retain the
caller's exact supported literal; no parse-short-then-rewrite conversion occurs.
Unrelated vintages remain refused and the legacy class does not implicitly
accept the new label. Native CPI APIs and schemas remain unchanged.
Focused CPI/adapter/dispatch contracts:80 passed in3.24s; targeted typing0 and
Ruff clean. This is fixture boundary qualification only; actual native-source
repeat proof, five-profile operation routing, full harness and hosted delivery
remain pending. See [CPI boundary receipt](./context-operation-cpi-vintage-20261017.json).
Conductor guidance also retains full population common records, all three lineage
fields/status/rules and dimensions/links in the operation manifest, with an
explicit native compatibility projection rather than silent parity replacement.
For GDP June, retain the legacy common parser token and actual June fact/native
transformation separately; vintage/61-quarter controls establish source scope,
not the parser label. No source capture or semantic/rights approval is inferred.


## Five-profile context operational dispatch — 2026-10-17

The five reviewed context profiles now consume actual common records and field
lineage, retaining every original record, lineage, loss, unresolved dimension
and link in a versioned operation manifest. Population's legacy two-field/raw-year
projection is explicit; full three-field common status/rules remain in evidence.
GDP June retains both actual June transformation and legacy common parser token.
QES preflight and public compact receipts remain compatible. Native APIs and
canonical-reader pins are unchanged. Historical June recovery uses the unchanged
native API and independently recorded four-file pins, never a replacement common
manifest. Exact observation timestamp literals are retained when registering
adapters: equivalent timestamp spelling must not silently change observation IDs.

Focused operations/recovery/context-adapter checks:577 passed/10 skipped in49.82s.
Initial timestamp mismatch and two old manifest-equality contracts were diagnosed
without changing source values; native three-table fixture parity passes. Tests
cover full evidence retention, independent readback, tampering, interruption,
symlink ancestors, source/vintage/observation bindings and repeat stability.
Actual retained-source/native recovery proof, full harness and hosted delivery
are pending. No broad track gate, rights, denominator, currency or join is closed.
See [implementation checkpoint](./context-operational-dispatch-20261017.json).


## Context dispatch native and full qualification — 2026-10-17

The frozen clean tree a798e1282774e88a505cc7114b507324e03f7e1f passed actual
retained-source qualification for all five profiles: 615 common records, 6,171
common lineage rows, 25 real dispatch calls and two complete repeat builds. All
15 native Parquet files per repeat are byte-identical to independently pinned
references; source and reference bytes remain unchanged. Full common losses,
unresolved dimensions and links are retained. Direct filesystem normalization
is forbidden during common-operation qualification. The missing June GDP native
reference matches all four historical file pins, and the entire outer recovery
report (including canonical products) equals the independently pinned October 2
receipt. Conductor independently rehashed all 40 generated files.

`./scripts/validate.sh` passed with exit 0 at that same exact head: 7,834 tests
passed, 10 skipped, 23 warnings in 429.93 seconds; 97.40% coverage against the
unchanged 80% floor. Typing 0, schemas 62/documents 52, parity 9/9 and every
mutation, hygiene, audit, licence, secret and SBOM gate passed (113 components).
Existing external CDX validation remains skipped. Only result documentation and
evidence follow the tested tree; affected checks and final-head hosted checks
remain required before normal protected merge and clean topic pruning. This
does not close downstream common-package canonical/Gold adoption or broader
source, rights, denominator, currency, mapping and track gates.
See [native proof](./context-operational-dispatch-native-20261017.json) and
[full validation](./context-operational-dispatch-validation-20261017.json).


## Context operations delivered; canonical integration active — 2026-10-17

PR #702 merged normally as 6a13aab0f81fa990dfecf5da8fbc33fc8cea25c6. Final
head cf7ee53f passed all applicable checks: Ubuntu 6m49s, macOS 11m46s,
Windows 19m28s, analyze/lint/CodeQL and patch coverage. No review threads
remained. Fetched main contains both head and merge; checked and merged tree
0113827cdb800aceaec3019853f5df034fb917b5 is identical. Zero unique changes and
clean status preceded local/remote/tracking topic pruning; primary retained.
See [delivery receipt](./context-operational-dispatch-delivery-20261017.json).

The next integration consumes independently pinned operation packages through
their source-regenerated verifier and reuses existing source-specific canonical
transformations. Historical fixed-cohort native APIs, manifest pins and outputs
remain unchanged. Qualify all five canonical fact/lineage projections first,
then their source-separated Gold consumption; the combined plan item remains
in progress until both are qualified and delivered. Full common evidence stays
closed by the input operation manifest pin, including status/rules/dimensions
and links not expressible in the existing canonical row schemas. No rights,
currency, denominator or join decision is inferred.


## Operation-bound canonical context and QES lineage finding — 2026-10-17

A read-only consumer now verifies the actual independent operation pin and exact
fixed official source identity before using regenerated typed tables and existing
source-specific canonical transformations. Historical filesystem readers and
fixed native manifest pins remain unchanged. Complete common evidence is bound
by its original manifest pin and schema/rows digest; it is not discarded because
canonical schemas express only a subset of source fields.

Full v2 lineage admission exposed a real historical QES defect: the old reader
supplies only six mapping fields to a complete schema, leaving required metadata
null. Its tests validated earnings but only checked lineage schema shape. The
legacy table also cannot serialize to Parquet. Preserve that representation and
its exact schema/rows digest, then explicitly complete the NEW path's lineage
metadata from uniquely resolved verified target facts, with a distinct completion
transformation. All 90 original mapping tuples remain unchanged; no wage values,
unknown qualifications, historical outputs, schemas or gates are replaced.
Conductor confirmed this source-backed approach. Other four profiles retain full
canonical fact/lineage parity; QES retains fact parity plus exact mapping tuples
and now passes complete v2 validation.

Focused contracts: 57 passed in 10.40 seconds; targeted typing 0 and Ruff clean.
Missing-module, full-lineage-validation and invalid-legacy-Parquet failures were
retained as bounded evidence. Native five-profile proof against pre-refactor
committed code, repeat/readback qualification, full harness and hosted delivery
remain pending. Gold operation-package consumption remains open in the combined
plan item. See [checkpoint](./context-operation-canonical-20261017.json).


## Canonical consumer native and full qualification — 2026-10-17

The frozen clean tree 3c9cadf7a3fa2111b9c44885ba3dd21753355439 passed native
qualification against pre-refactor Git 6a13aab0 code: all five official operation
profiles, 615 canonical facts, 4,190 valid canonical lineage rows, ten actual
verified reads and two identical repeats. Every fact Parquet matches the old
projectors; all four other full lineage Parquets match too. QES retains all 90
mapping tuples and the invalid legacy schema/rows digest, while its completed
v2 lineage validates with unique IDs and fully resolved targets. All source and
input operation-package bytes remain unchanged. Filesystem normalizers and
historical readers are forbidden inside the new route. Conductor independently
checked all 30 generated files, four code pins and generated QES v2 admission.

`./scripts/validate.sh` passed with exit 0 at the same exact head: 7,847 tests
passed, 10 skipped, 23 warnings in 314.23 seconds; 97.41% coverage against the
unchanged 80% floor. Typing 0, schemas 62/documents 52, parity 9/9 and all
mutation, hygiene, audit, licence, secret and SBOM gates passed (113 components).
Existing external CDX validation remains skipped. Only result documentation and
evidence follow the tested tree; final-head affected/hosted checks remain before
normal protected merge and topic pruning. Gold operation-package adoption and
broader track gates remain open.

The population canonical count is 110: 108 period/amount/label links plus two
publisher-status links. This corrects an old plan count; the pre-refactor and new
outputs match exactly. The historical QES JSON replay remains a legacy mapping
receipt, not proof of complete v2 lineage admission; the new path qualifies that
missing contract without rewriting the historical output.
See [native proof](./context-operation-canonical-native-20261017.json) and
[full validation](./context-operation-canonical-validation-20261017.json).


## Canonical consumer delivered; operation Gold adoption active — 2026-10-17

PR #703 merged normally as 8410aaa7374f12df732e8683f371dc80375c32e8. Final
head 37ebb7d7 passed all applicable checks: Ubuntu 9m50s, macOS 8m40s,
Windows 17m38s, analyze/lint/CodeQL and patch coverage. No review threads remained.
Fetched main contains head and merge, with identical checked/merged tree
f37ebf16d04856557c3be0952522321b24d4f3d0. Zero unique changes and clean status
preceded local/remote/tracking topic pruning; primary retained.
See [delivery receipt](./context-operation-canonical-delivery-20261017.json).

The combined integration item remains active for source-separated Gold. Reuse
canonical mappings plus existing coverage/quality/report/plot projections and
original native Gold APIs. The new route must verify all five independent input
operation pins, consume admitted canonical facts and actual source statuses,
retain canonical/direct/common lineage closure, and verify saved products against
source-regenerated expected content. Add typed local CLI and read-only query
contracts for this new route, with no default writes, no repairs of partial output
and no external publication/capture mutation. Rebuild/repeat and tamper evidence
remain required before full assurance and focused delivery.


## Operation Context Gold implementation and input-reader fixes — 2026-10-17

The new Gold path consumes all five independently pinned operation packages
through admitted canonical bundles, preserving common evidence alongside typed
facts/direct lineage. It saves canonical products plus existing context tables,
quality report and deterministic plots, with a distinct operation-Gold manifest.
Readback regenerates expected metadata/products from trusted source inputs and
requires independent Gold and input pins. Source statuses come from original
common records; GDP series identity composes the same row's literal prefix and
reference. Native Gold outputs/readers remain unchanged. Typed CLI build/verify/
query and three read-only MCP tools use a closed bounded five-input specification;
MCP exposes no write flag and queries cap returned rows.

Real draft regressions were retained before correction: both directory readers
scanned beyond an unexpected entry; bounded membership now stops after one extra.
Conductor found that a FIFO input specification could block before byte caps; a
bounded subprocess reproduced the timeout at 10 seconds. Shared regular snapshot
transport now uses nonblocking open where supported, fstat regular-file admission,
capped reads and finally-close. Existing verified snapshots still hash exactly
the bytes returned. The public FIFO test now passes, independently confirmed by
Conductor; affected config/regular snapshot checks pass 27 tests. Prior integrated
checks passed 49 tests before final FIFO/dispatch/output-schema changes; the final
coherent focused run remains pending. Typing and Ruff are clean. Native actual-
source repeat/CLI/MCP/recovery proof, full harness and hosted delivery remain
pending; no broad track gate or rights/currency/denominator/join is closed.
See [implementation checkpoint](./operation-context-gold-20261017.json).


## Operation Context Gold native proof and full-gate corrections — 2026-10-17

At frozen e9f4297f, coherent focused checks passed 98 tests in58.57s. Two
empty-derivative Bronze → operation → canonical → Gold replays each generated
20 files with identical hashes. All five input operation inventories match the
independent earlier receipt; canonical facts/lineage match the retained canonical
proof. The615 observations map to615 unique canonical facts, with4190 validated
lineage rows,585 eligible context-only observations and30 exclusions (including
two publisher-provisional population rows). Four actual CLI invocations passed
in10.8–11.4s under the unchanged30s bound; read-only MCP preflight/verify/query
passed both runs. Source and operation inputs remained unchanged. Conductor
independently audited saved files, schemas, links and logs without replay and
found no actionable native-proof issue. See
[native proof](./operation-context-gold-native-20261017.json).

The full harness at the same head failed:7865 passed,2 failed,10 skipped,
23 warnings,432.40s; coverage97.38% against80%. Formatting/lint/typing passed;
later harness gates did not run after test failure. Preserve
[initial failure evidence](./operation-context-gold-initial-validation-20261017.json).
The new MCP input/output schemas omitted the repository-required2020-12 dialect
marker; both now declare it. The existing Budget directory-pin failure test
injected a global fstat error and now hit the new source descriptor check first.
Its injection now targets an actual directory descriptor using saved real_fstat;
it still proves exactly that failed descriptor closes once, while input errors
retain input-stage semantics. No production error relabeling or safety removal.
Corrective MCP/Budget focused checks passed33 tests in6.60s; Ruff check/format
passed. Full clean-head rerun and hosted delivery remain required before merge.
Native output logic was unchanged by these corrections; the native proof remains
bound to its original exact commit. No broader track completion is claimed.


## Operation Context Gold qualified locally — 2026-10-17

The corrected clean frozen7143a86a full harness completed with exit0. Tests:
7867 passed,10 skipped,23 warnings in390.34s; coverage97.40% against unchanged
80% floor. Formatting/lint/typing0,62 schemas/52 representative documents,9/9
parity with zero divergences, all mutation/hygiene gates, CAS347.99MB/s,
dependency vulnerability/licence/secret checks and SBOM113 components passed.
The existing CDX validation skip remains explicit. The failed initial receipt is
retained independently. The project runtime is Python3.14.6/uvCLI0.13.1, with
unchanged lock/backend/CI pins, rather than the system interpreter used for an
earlier observer. See [full validation](./operation-context-gold-validation-20261017.json).

Conductor independently audited the native proof and the two exact corrections;
no blocking finding remained. Only documentation/evidence follows the tested
code tree. Final affected documentation checks and hosted checks are separate
required gates before normal protected merge and clean topic pruning. The five
context common-operation canonical/Gold integration has local implementation,
615fact/4190lineage native parity and20file repeated recovery evidence; broader
source, donor-area, rights, metadata, scheduling and final track gates stay open.


## PR #704 reserved-output race correction — 2026-10-17

Review thread PRRT_kwDOTo2MOM6teibQ identified a real write redirection defect.
Two executable races replaced the reserved output path with an input symlink
before the first create or between creates; the old writer added19/18 files to
that input. Both red failures and their exact logs are retained externally.
The corrected writer reserves and pins the output directory, uses POSIX relative
O_EXCL/O_NOFOLLOW creates, and holds all native Windows ancestor/leaf handles
with read sharing only, reparse rejection and128bit file-ID checks through final
readback. No unlocked Windows fallback. ExitStack closes in reverse order on
success/interruption; failed pin and fdopen cleanup are covered. Original value,
manifest and readback semantics are unchanged in design; actual-byte parity must
be requalified before delivery. Native Windows replacement/cleanup contracts are
present but cannot be claimed from macOS.

Affected Gold/output checks passed15 with2 Windows-only skips in144.86s; final
helper checks after test cleanup passed4 with2 skips in0.29s. Ruff and typing
passed. The prior full gate remains valid only for its original7143 tree; the
material correction requires fresh native/full/hosted assurance before review
resolution or merge. Preserve the original native/full receipts and current
non-terminal hosted runs; no merge, pruning, protection change or source repair.
See [correction checkpoint](./operation-context-gold-output-correction-20261017.json).


## PR #704 pinned-output native parity and platform narrowing — 2026-10-17

Frozen6ef90a1a completed two fresh Bronze→operation→canonical→Gold rebuilds.
All20 output files repeat byte-for-byte and match independently retained pre-
correction pins. All615 observations/4190 lineage links retain their controls;
585 eligible context-only/30 excluded, originals and input packages unchanged.
Four actual CLI calls passed in12.1–14.9s under unchanged30s; read-only MCP
preflight/verify/query passed both. See
[output-correction native proof](./operation-context-gold-output-native-20261017.json).

An additional explicit Windows platform type check exposed POSIX O_NOFOLLOW
availability in a branch conditioned only on descriptor state. No runtime
fallback or flag weakening: branch now tests os.name, requires the corresponding
None/native descriptor state, and keeps existing writes unchanged for both valid
public reservation cases. Windows platform typing is now0errors; affected
race/closure checks6passed/2Windows-only skips/9deselected in14.27s, Ruffpassed.
The native run finished before this type-only equivalent branch clarification;
its exact head remains recorded. Conductor stopped the following full3 stage
before tests for that known defect; exit143 and cancellation receipt retained,
never represented as passed. The final frozen tree still needs its own full
local harness and actual Windows native/hosted qualification before review
resolution/merge/pruning. No broad track gate is closed.


## PR #704 native Windows access-mask qualification correction — 2026-10-17

Exact4a3cad55 hosted Ubuntu and macOS full assurance passed. Windows failed two
native sharing tests: leaf/ancestor renames were not denied by attribute-only
handles (7847passed/36skipped/2failed,648.09s). Preserve job117352281624/run
39017372061 bounded evidence and log fixity in the correction checkpoint. This
is a demonstrated Windows defect, not a hosted runner stall. Microsoft MS-FSA
corroborates why attribute-only access does not participate in sharing checks.

After Conductor stopped only the superseded local4 descendants and released
freeze, add FILE_LIST_DIRECTORY to Windows handle desired access (0x80→0x81).
Keep restrictive sharing, complete ancestor locks, reparse rejection,128bit IDs,
finally-close and all native replacement/cleanup assertions. Add an early
Windows-only CI invocation of the existing small output-pinning test module;
full required platform assurance still follows on success. No new framework,
permission grant, threshold reduction, Windows feature drop or timeout change.
The sole production delta is inside the Windows-only function; native2/POSIX
output code and bytes are unchanged, so no redundant Mac native/full replay is
claimed or scheduled. Local4 exit143/partial logs are retained, never marked
passed. Local full-before-PR7143 and exact4a3 hosted Mac/Ubuntu remain historical
scoped evidence. Final corrected head requires actual native Windows proof and
all required hosted checks before resolving review/merging/pruning.


## Operation Context Gold delivered; metadata bridge active — 2026-10-17

PR #704 merged normally as3545f270e9d9829893baa859cb2a2892706aadd1 after all
applicable checks passed onab156c16625d87305ec4207bce613ee60d260ec8. Final full
Ubuntu/macOS:7857passed/28skipped each; Windows:7849passed/36skipped. Native
Windows preflight3passed/3platform skips; schemas62/documents52, parity9/9,
mutation/security/supply-chain gates, analyze/lint/CodeQL/patch coverage passed.
The reproduced output-race review was resolved after qualification. Coverage
97.20–97.26% against unchanged80%; SBOM platform counts114/113/114. Historical
local passes, Windows failure and superseded cancellations retain exact scope.

Fetched main contains checked head and merge; checked/merged tree is identical
6af6f4ace1f21c6b3411e688750a4812096023e7. Zero unique topic changes and clean
status preceded local/remote/tracking topic pruning. Primary worktree retained.
See [delivery receipt](./operation-context-gold-delivery-20261017.json).
The five-profile canonical/Gold integration and its output-race fix are complete;
no broader phase/track gate is closed.

Next is the existing Platinum/recovery bridge. The current projector supports
only Budget/Fiscal/canonical-Gold inputs, not operation-context Gold. A read-only
probe of13 independently pinned new tables found a real descriptor contract gap:
nullable publisher statuses cannot be sorted with strings. Add an explicit new
profile, retain null counts distinctly, label facts/lineage/coverage/quality
honestly, and reuse existing metadata projections rather than duplicate them.
The new route must verify Gold and five independent operation pins against
trusted Bronze before projecting expected products; keep paths private and
rights/publication/unsupported federation claims unchanged. Qualified CPI-base
candidate captures collected outside the frozen tree remain for a separate
source-census slice; the admitted Gold base metadata is unchanged.


## Operation-context metadata projection started — 2026-10-17

Following the PR704 delivery/design checkpoint, two new public contracts failed
because the operation-context metadata input did not exist (2failed/7.68s).
A typed input now carries Gold/operation pins and Bronze scope. The Gold reader
returns source-regenerated manifest/product bytes only after saved-package
readback; verify/query wrappers preserve their public results. The existing
metadata projector reuses its renderers for a newv5 profile, describes13 tables,
retains null publisher status separately, labels lineage/facts/summary kinds,
keeps paths private and reports source re-verification per profile honestly.
Initial contracts passed2/10.37s; subsequent typed dispatch refactor and Ruff/
typing are clean (0errors). A final coherent test run remains pending after the
rest of this slice; do not treat initial green as complete assurance.

Export/readback, versioned schemas, source-locator drill-through, historical
v3/v4 byte parity and two full Bronze-driven metadata recovery repeats remain
before focused/full/hosted delivery. The authorized Conductor coordinator retains
broad/native local launch ownership in this coordination batch. The durable
workflow records frozen head/tree/runtime/command/log/terminal-marker handoff
and independent focused/static/hosted ownership; no new approval or framework.
See [in-progress checkpoint](./operation-context-metadata-20261017.json).


## Operation-context metadata focused qualification — 2026-10-17

The v5 bridge now implements all eight existing metadata projections plus the
manifest, exclusive output reservation, source-regenerated expected-byte readback,
exact source-locator/hash pointers and three versioned schemas. The schema-first
contract failed for the absent v5 schema before implementation; the final coherent
focused suite passed27 tests (4 existing RDF deprecation warnings,94.19s), Ruff
check/format passed, basedpyright reported0 errors, and schema validation passed
65 schemas/55 representative documents. Tests cover all13 table descriptors,
nullable statuses, independent operation pins, repeated9-file builds, dry-run,
overlap/no-overwrite and forged rights with a rehashed candidate marker.

Self-review retains old v3/v4 projection branches, versions and marker construction;
actual native byte parity remains unproven until replay. New v5 cards keep all
recordset rows contiguous; per-profile Bronze verification claims remain distinct.
The offline native proof compares retained legacy packages against the Git3545f270
renderer, then twice rebuilds Bronze→operation→canonical→Gold→metadata, validating
schemas, literal manifest references and RDF graphs with file/network loading
denied. Independent prior operation/canonical/Gold pins are not refreshed from
new outputs. Runtime remains uv0.13.1/Python3.14.6 with unchanged lock/backend.

Native/full runs are prepared, not launched or passed. The Conductor coordinator
retains launch ownership; this topic is frozen for a combined native-then-full
handoff. No PR, broader phase closure, source admission, rights reassessment,
federation link, publication or new metadata CLI/MCP claim is made. The broader
track remains in progress. See the updated checkpoint for exact log/script hashes.


## Native proof assertion correction — 2026-10-17

Conductor-owned assurance1 terminated with native exit1; the full harness did
not start. On frozen02174648, retained v3/v4 Git-reference byte parity passed.
The source-reference pointer checks passed, then the external proof incorrectly
expected five total HTTPS locators. The actual verified Gold manifest contains
five input projection and five plot-report locators, and the metadata correctly
retains all ten field references. Preserve the first run/log and correct only
the external proof: require ten total, two exact five-member groups, and both
locator sets equal the independently pinned operation binding locators. No
production values, source references, tests or gates are changed. Attempt2 uses
a fresh clean-room output and new logs/markers; native/full remain pending.


## Native qualified; bounded full-harness recovery — 2026-10-17

Both clean-room Bronze→operation→canonical→Gold→metadata repeats passed on
e1e01c0b. All36 metadata files,40 Gold files and40 operation files were independently
read back; two metadata forms are byte-identical across reversed input order.
Operation-only metadata describes13 tables; mixed metadata describes26 across
four profiles. Offline RDF checks verify exact dataset/collection/member sets
with file/network loading denied. Historical v3/v4canonical/v4composite payloads
and marker pins match the Git3545f270 renderer. Native receipt is retained in
[operation-context-metadata-native-20261017.json](./operation-context-metadata-native-20261017.json)
(SHA1f70250e5d34caf438f8aecedad516d5083448d6e797d27882c6989b7eed5b71).

The required ./scripts/validate.sh ran on this exact code tree:7876passed,
12skipped,23warnings/555.04s;97.29% coverage against unchanged80%; schemas65/
documents55; parity9/9; mutation, hygiene, CAS throughput271.36MB/s, dependency
audit and licences passed. It stopped at the secret scan (exit1), before SBOM.
The sole unadjudicated entropy candidate was a redundant concatenation of the
public PR704 review-thread identifier and resolution status in the delivery
receipt, not an authentication secret. Normalize review_resolution to status
only; retain the exact identifier in its separate existing review_thread field.
Original receipt bytes remain at Gita37476ec and external retained evidence;
original SHA867f4a7fa48031519cbae817e8b736cd1946cb50a7d663868cbbb76f4de44dee.
No scanner, exclusion, adjudication or production-code change is made.

Conductor recommends resuming unchanged secrets/SBOM plus affected document
validation, preserving explicit partial-run scope rather than replaying the
unchanged7876 tests/native proof. Remaining gates and hosted checks are pending;
there is no successful whole-run claim yet. Broad/native launch ownership remains
with the authorized coordinator. No PR or phase/track completion is claimed.


Secret-scan recovery passed with the unchanged scanner and exclusions; no
candidate remains. The actual full2 report and secret-adjudication evidence are
retained externally. Affected Conductor-state and hygiene checks also pass.
Only track evidence documents differ from e1e01c0b; production/test/schema/tool
bytes remain unchanged. Final frozen continuation will reconcile document gates
and SBOM; full2/native2 claims retain their original head and terminal scope.


## PR705 metadata delivery and next census slice — 2026-10-17

PR #705 merged normally at0a534f13aa6481888c467088b6117318e3d77178 after final
3f86e6fe passed all required hosted gates, CodeQL and patch coverage; review
threads were clear. Ubuntu/macOS each7860passed/28skipped; Windows7852passed/
36skipped plus native preflight3passed/3skipped. All65 schemas/55 documents,
parity9/9, security/mutation/supply-chain gates passed. Fetched origin/main
contains the checked head and merge with identical tree7bada49c and0 unique
changes. Clean local/remote/tracking topic refs pruned; primary/originals retained.
See [delivery receipt](./operation-context-metadata-delivery-20261017.json).
This completes the bounded metadata bridge, not Phase7 or the overall track.

Continue with CPI source-evidence census reconciliation on the next topic. The
existing census already qualifies the June2017 base and the fiscal CPI benchmark
has an approved exact-pair averaging policy; reuse both. Newly retained external
captures verify current/versioned metadata edition159 and the same base clause,
plus the exact release→CSV link and official copyright policy. A separate raw-CSV
period census finds all449 quarter labels,422 numeric values and27 publisher NA
slots; no numeric continuity, rights or analytical admission follows. Preserve
one differing spatial metadata identifier in both raw snapshots. Offline evidence
contracts and census reconciliation are next; no new broad/native run launched.
The authorized Conductor coordinator retains broad/native launch ownership.


## CPI transport boundary resolved without historical rewrite — 2026-10-17

The retained original CPI WARC matches inventory pin46c14f15 but lacks request/
final URL digests. The unchanged modern verifier correctly rejects it as
resume_warc_binding_invalid, caused by resume_warc_binding_mismatch. Preserve
that legacy observation; do not manufacture capture-time headers or repair its
bytes. A separately observed bounded capture of the exact official CSV succeeded:
bodySHAf474a6a3 is byte-identical to the retained2917074-byte original, while new
WARC0fa0c571 passes modern response binding. The old August observation and new
October observation remain separate. The original and old WARC are unchanged.

This supplies the missing modern transport evidence for the next offline CPI
source-evidence contract. Metadata/current/versioned, release and copyright
captures remain outside Git; checkpoint records exact URLs, observed times and
body/WARC pins. Reuse the existing census base qualification and household fiscal
benchmark; no new benchmark, source projection rewrite, rights promotion or
publication follows. Implementation/tests, current census reconciliation and
repeat/full/hosted assurance remain pending. See
[census evidence checkpoint](./cpi-source-evidence-20261017.json).


## Offline CPI source-evidence contract implemented — 2026-10-17

The initial contract failed collection because the module was absent. The new
read-only API verifies a closed seven-capture profile with independent body/WARC
pins and exact byte limits before parsing. It reuses the existing WARC contract
through an additive immutable-byte entry; the Path entry retains its behavior.
Request/final URL digests, status, media type, framing, lengths and body digests
remain mandatory. No HTTP client or acquisition is used by the inspector.

Contracts retain selector/units/layout, metadata edition and the explicit SDK
flag, both differing identifier snapshots, exact release-to-CSV and metadata
references, and the qualified reference clause with its later-index exception.
Quarter labels are checked separately from27 publisher NA slots; the existing
CPI parser supplies every source row and value classification without rewriting
native products. Copyright output is an observed URI/field digest, not rights
admission. The existing fiscal CPI policy is referenced without another benchmark.

Real-page inspection found unrelated non-JSON/scalar/list widget values; a new
fixture reproduced rejection before unique PageBlocks selection was corrected.
A missing-field/null regression also failed before presence-aware, type-sensitive
metadata comparison was fixed. Final focused suite81passed/9.30s includes the
existing strict WARC and census contracts and immutable-byte entry behavior;
Ruff/format pass and basedpyright reports0 errors. Keep these bounded failures
and exact log hashes in the checkpoint; no coverage chasing or policy weakening.

Actual-source native proof is prepared, not run: two fresh seven-body/seven-WARC
input trees, socket/DNS disabled, independent capture/period pins, unchanged
original and legacy capture, identical report bytes. The authorized Conductor
coordinator owns launch. Census reconciliation will use its verified output,
then a final coherent tree will go through full/hosted delivery. No PR or wider
phase/track completion is claimed.


## CPI actual-source proof and census reconciliation — 2026-10-17

The Conductor-owned native run on38bc5158 terminated0. Two fresh14-file input
trees produced identical source-evidence report0716432e with socket/DNS access
disabled. Independent implementer and coordinator reads verified all28 source
files and both report copies. Raw22701-row CSV inventory retains449 selected
quarter labels,422 numeric values and27 publisher NA; exact2017.06 anchor at
physical row22666 is1000. Source identities, units, qualifiers, layout and
metadata differences are retained with exact body/transport/field digests.

Reconcile the current context census to that actual report and code pins. Keep
all other context rows byte-equivalent; CPI source observations, base qualification,
rights, unqualified analytical state and native manifest pin remain unchanged.
The prior complete census bytes3f0f1522 are retained separately. Clarify the
existing exact fiscal benchmark versus unqualified general annual aggregation,
without a new benchmark. Source-health v1's coarse state is not silently upgraded
from a free-text assertion; its future adoption remains Phase6 work.

All14 verified source bodies/WARCs and the full native proof/recipe/reference
are retained in a permanent bounded Health archive CAS/evidence directory using
the existing store. Source staging/original files are unchanged; this is local
preservation, not another acquisition or external collection/publication action.
The compact native receipt binds the full external proof and inventories; the
standalone report and preservation receipt carry all expected source pins.
Focused source/WARC/census checks82passed/12.77s. Final static and full/hosted
assurance remain pending; no PR or broader phase/track closure is claimed.
The coordinator retains full launch ownership and will serialize after any
actual live external broad profile is terminal.


Final pre-harness static checks pass: Ruff format/lint, typing0, schemas65/
documents55, Conductor0 errors and hygiene. The code qualified by native38bc5158
is unchanged; subsequent work adds census data, historical preservation and a
reconciliation regression. Freeze this coherent tree for the coordinator-owned
required full harness. No independent broad/native run, new acquisition or
external publication/collection action is launched.


## Full-harness historical review recovery — 2026-10-17

Conductor-owned full1 on65622850 terminated1 at tests:7883passed,2failed,
12skipped,23warnings/550.20s; coverage97.29% against unchanged80%. Both failures
in test_source_measure_review raised invalid source-measure evidence because
its prior forecast-binding review still pinned old census3f0f1522 at the mutable
current context-census.json path. Preserve the full log52ba023a and original
report. The validator correctly rejected drift; no production check is weakened.

A successor review changes that evidence locator to the retained historical
snapshot with the SAME digest and cites the immutable original review. All19
series, source-family counts, assessment time, scope and rights stay unchanged.
Current CPI census af8cf8eb remains intact; no old value or evidence hash is
silently substituted. The active index/test reference selects this explicit
historical binding, preventing later current-census edits from breaking the
frozen assessment again. See
[rebinding receipt](./cpi-source-review-rebinding-20261017.json).

Recovery tests initially found an assertion mismatch in the new regression:
validate_review returns normalized optional fields, so raw JSON is not its
comparison contract. Compare validated output to its own pre-mutation baseline;
retain a separate raw old/new assessment equality assertion. Then changing the
bound historical snapshot must still fail. All68 source-measure/census checks
pass/1.97s, including the original two failures and the new drift contract.
Source/native production code and runtime are unchanged. Resume affected static
and all unrun post-test stages on a frozen head under the coordinator, rather
than replaying unchanged7883 tests/native proof. Full1 remains explicitly a
failed partial run; no whole-pass or hosted/PR claim is made yet.


### 2026-10-17 — PR706 delivery and CPI source-health slice

PR706 passed all seven named gates on730e12e8 and merged normally at4cf8d808.
Fetched main contains checked head/merge with identical734e2f60 tree and zero
unique changes; clean topic refs pruned, primary/originals retained. See
`cpi-source-evidence-delivery-20261017.json`. Next bounded task is explicit v2
CPI label-grid evidence adoption using the existing producer, renderer and tool.
Conductor reviewed independent pin/census binding and non-admission invariants.
No external mutations or new rights decisions are involved.


### 2026-10-17 — CPI source-health focused checkpoint

Optional typed evidence reuses the closed CPI inspector and existing report/
renderer/tool. Independent digest and exact census/source/vintage binding
precede v2 adoption; v1 remains the default. Paired CLI roots and distinct output
paths protect historical reports; existing different content is refused.
69 focused checks pass in2.53s, including counterfeit/source URL/observation and
census-byte failures. Ruff/format/type/Conductor checks pass;66schemas and
56documents validate. Initial collection and cached-alias test failures are
retained in the external health-cpi-source-health-20261017 evidence folder.
Native two-run proof and full harness are prepared for the coordinator, not yet
claimed. No acquisition, rights decision, join or external mutation occurred.


### 2026-10-17 — source-health native1 input-selection correction

Coordinator session10894 terminated1; full was not launched. Native first-run
v2 generation and exact replay passed, but a protected non-JSON destination was
implicitly selected as prior input and raised JSONDecodeError before the intended
refusal. No output was overwritten. Preserve native1 log and partial artifacts;
see `cpi-source-health-native-failure-20261017.json`. V2 now independently selects
the retained baseline when no explicit prior report is supplied; v1 defaults
are unchanged.70 focused checks pass in7.66s, including a sentinel refusal
regression. The preliminary unit-regression command observed the fixed code and
passed; native1 is the failing evidence. Fresh native2/full remain pending.


### 2026-10-17 — CPI source-health delivery and metadata operations

PR707 passed all seven named gates on27e79f3c and merged normally at28e48f52.
Fetched main contains checked head/merge with identical13f421b4 tree and zero
unique changes; clean topic refs pruned. Native1 failure, native2PASS and exact
full2PASS remain separately scoped; see cpi-source-health-delivery-20261017.json.
Next bounded reviewed task exposes existing v5 metadata through CLI/read-only
MCP, refs213/214/215. Live issue214 is open for Phase8.

A bounded GDP currency discovery inspected the official June2026 release and
linked quarterlies411, concepts4 and June-update metadata; it did not find an
explicit currency binding for SNEQ/SG03AB01GE00S900. This does not establish
absence of all publisher evidence. Conductor independently could not supply a
verified new locator. Keep literal dollar/million/price context and ISOcurrency
separate, with currency-dependent joins unqualified. Admissible next evidence
is exact publisher series/export currency+multiplier+release metadata, or
publisher clarification bound to that exact series/vintage. No contact/send,
ADE403 retry or broad search loop is implied. Preserve the existing historical
source-measure assessment and continue independent operations work. Discovery
bodies/hashes remain in the external health-gdp-currency-discovery-20261017
folder; these were read-only observations, not WARC-qualified admission.


### 2026-10-17 — metadata operations focused qualification

The thin operation_metadata adapter reads the existing typed five-profile spec
and retains independent Gold/metadata pins. Two CLI routes use qualified v5
export/readback; MCP adds one closed read-only verifier. No projector/normalizer
or v3/v4 contract changed. Dry-run verifies actual source products; write uses
existing overlap/exclusive-output guards and post-write source regeneration.

Initial3missing-command failures40.63s preserved; initial3real contracts passed
72.18s. Expanded spec/pin/overlap/repeated-write/forged-manifest/read-only tests
and related legacy/MCP suite pass76tests/2RDFLibwarnings387.07s. The longer
focused run remained live, was inspected, and completed without restart.
Ruff/format/type and Conductor checks pass. Native actual-source comparison and
full harness await the coordinator's frozen launch, with original Gold and
metadata baseline reuse; no unnecessary chain/RDF replay. See the dated
operation-metadata-operations checkpoint and implementation guide.


### 2026-10-18 — metadata operations full assurance recovery

Native CLI/MCP proof passed on frozen e876eaf3, with independent63-file readback
and all9metadata outputs identical to the pinned PR705 baseline. Full1 terminated
124 at the900-second test-stage cap after98percent/one unidentified F; no final
traceback or coverage result was available. Cached selection56PASS/14deselected
did not reproduce/identify it. Preserve that incomplete scope.

Full2 changed only runtime scheduling/verbosity to4bounded workers, retaining
the900-second cap and assertions.7901PASS/12skip/23warnings657.25s at97.28percent
coverage against80; schemas66/56docs, parity9/9, mutation/hygiene/CAS/audit/licences
passed. It stopped at a new false-positive completion-status label before SBOM.
The sole new finding hashes to literal passed, not a credential. Normalize only
the redundant receipt label to post_test_gates; preserve the result, logSHA,
original receipt in Git/external evidence, and every detector rule/baseline.
No production/test/tool/runtime input changes are involved. The coordinator will
run only the affected scan and previously unrun SBOM after focused structure/
reference checks. No PR is opened before that required recovery succeeds.


### 2026-10-18 — metadata operations delivered; component-index qualification

PR708 merged normally as31ba7ee6 after all seven named hosted checks passed on
f0291547, with no review threads and active strict branch protection unchanged.
Fetched main contains checked/merge commits, identical cbaeb167 tree and zero
unique changes. Primary checkout retained clean; topic refs pruned. The external
local-assurance-reconciled-3 receipt preserves full1 timeout/unidentified F,
full2 test success/scan stop, and terminal0 affected scan/SBOM continuation.
No unchanged native/full replay was needed. See the dated delivery receipt;
prior pending checkpoint statements remain historical rather than silently
rewritten.

Next source-census task preserves publisher exports rather than constructing
series identifiers. BrowserOS generated the exact LCI025AA TQX for code3 All
Salary and Wage Rates / LCI025AC Health Care and Social Assistance, central
Government sector. TQX has selections only, not numeric observations. Native
CSV export was found in the actual response's download-frame URL after UI
selection yielded no downloaded file. Original2719bytes SHA4a525c42 contains
135quarter labels1992Q4–2026Q2,66literal missing '..' through2009Q1 and69numeric
2009Q2–2026Q2. Status flags were requested; no final status is inferred from
unflagged observations. The CSV retains baseJune2009=1000, Index/Units and
updated05Aug2026 metadata. Coordinator-owned fresh unauthenticated GET capture
matched the body exactly; existing response binding verified actual3297byte
WARC1c6d9962. External query/capture receipts remain in
/Volumes/PortableSSD/tmp/health-component-index-export-20261018. Rights and
analytical admission are not performed; no browser credentials transferred.

PPI021AA full-period UI currently has empty publisher row/column layout lists;
ValidateInput returnsfalse. Preserve that diagnosis; do not fabricate hidden
layout fields or infer PPIQ identifiers. Conductor has been asked for a bounded
publisher-supported recovery. Continue independent source/rights qualification.

PPI layout recovery used the existing publisher direct-Go route from variable
selection, then Show status flags; no hidden field or client-authored query was
needed. Exact original3470byte CSV159708fc has129periods,9missing '..' through
1996Q2 and120numeric from1996Q3. Initial integer-only diagnostic miscounted the
native decimal tokens; finite Decimal inspection corrected only that count to
120, retaining all source bytes and lexical precision. DisplayDecimals0 does
not authorize rounding the export. PPI021AA/PPI021CC identifies Inputs ANZSIC06
NZSIOClevel3 health-and-social-assistance, not central-government-only or output
PPI. Exact query2a40ab6d and fresh sessionless response WARCfd3c66ae retained;
existing response binding passed. Five actual source captures plus two original
query files (12objects) independently rehashed/read back and preserved outside
Git in the permanent component-index-export-20261018 CAS. Three metadata captures
provide Infoshare ownership, LCIv66 and PPIv3 methodology; their semantic
qualification remains pending. No rights decision or analytical admission.
See component-index-source-checkpoint-20261018.json.


### 2026-10-18 — component source offline contract

The first focused invocation failed collection because the new module did not
exist (red-1.log retained). The bounded offline implementation now checks the
closed six-capture cohort using existing regular-snapshot/fixity/WARC response
binding plus two separately pinned native TQX configs. Defused XML rejects DTDs;
CSV checks exact table headers/footer, complete quarterly label grid, missing
positions, finite positive decimal literals and observed selectors/status option.
Readback retains title/base text, units, update literal, source footnote and
lexical period/value digest; no rounding or inferred FINAL/series code. General
LCIv66 and PPIv3 method observations remain limited by their version/vintage.
Publisher ownership/licence statements are observed, not automatically applied.
All14source/query/response objects including the reused CPI copyright capture
are preserved. Existing Silver/Gold and generic rights policy are unchanged.

Initial9contracts passed4.94s; capture/read-only refusals expanded to13passing
contracts1.41s. Final14component contracts plus7CPI regressions pass21checks2.61s.
Ruff/format and focused typing pass; initial lint findings retained and corrected
without changing detector rules or assertions. Actual-source offline replay,
full harness and hosted delivery remain pending under the existing coordinator.


### 2026-10-18 — native metadata representation correction

Actual-source replay1 on ced56bf0 exited1 at the owner-link check, before full
harness. The retained Infoshare page stores Content HTML inside data-value JSON,
with escaped URL slashes. Initial parser compared undecoded JSON text; this was
an implementation defect, not absent source evidence. Native-proof-1 and original
bytes remain retained; owner released patch freeze after bounded diagnosis.
Initial replay did not set native TMPDIR, but used explicit proof paths and no
temporary-directory calls. Do not claim a full or successful replay.

Decode only structured PageBlocks Content, parse its anchors and text, ignore
script/style text, then require the exact observed Infoshare link and ownership
statement. No raw-script/hidden-URL acceptance or weakened host check. Replace
the unrealistic fixture with actual-style escaped-slash JSON and add a wrong-host
refusal.22focused checks pass2.40s (15component/7CPI); Ruff/format/type pass. The
six fixed capture identities and original source/query bytes are unchanged.
A fresh uniquely named native-proof-2 and subsequent full harness remain pending
with the same launch owner. No unchanged recapture or source substitution.


### 2026-10-18 — component source qualification assurance

Corrected native2 and exact-head full harness pass on c3e87580/tree4d68e634.
Two network-denied14-object replays produce identical report bbd251a4; independent
CSV counts match LCI135/66/69 and PPI129/9/120 (represented/missing/numeric), and
all original bytes remain unchanged. Actual native1 failure and diagnosis remain
separate; no unchanged recapture or duplicate proof was used. Full harness exits0:
7916tests/12skips/23warnings322.55s,80percent floor retained,66schemas/56documents,
9/9parity/zero divergences, all mutation/hygiene/CAS/audit/licence/secret-scan/SBOM
stages pass. CAS335.30MB/s; SBOM113components. Exact log and native receipt pins
are in component-index-source-assurance-20261018.json. No source code, tests,
lock/backend, harness or workflow changes follow this qualified tree.

The deterministic report, actual native receipt, initial failed native receipt
and maintainer guide are now reviewable in the track. This is a qualified census
successor to the historical component-index discovery; historical observations
are retained rather than rewritten. Existing primary source/context census
profiles, Silver/Gold products and generic rights policy remain unchanged.
Rights eligibility, analytical weighting/join policy, broader source coverage and
track completion remain open. Result-only documentation checks and hosted PR
checks precede normal protected merge; the task stays in progress until delivery.


### 2026-10-18 — public method summary rendering correction

Docs-only affected scan on12d65559 exits1 after Conductor/schema success. Its
sole new candidate is the emitted PPI methodology summary at report line5,
classified Base64 High Entropy String. Root and coordinator independently match
the finding fingerprint to the descriptive label, not a credential. Full scan,
adjudication and failed docs-stage evidence remain external/permanent; original
canonical reportbbd251a4 remains unchanged in native2/Git/external history.

Conductor selected readable-prose producer output rather than a detector
exception. Change only the three methodology summary values; keep field/schema
names, underlying facts and every numeric/query/capture byte unchanged. This is
a changed-output validation: fresh focused checks and uniquely named actual-source
native3 precede a new original full harness on the corrected executable tree.
No scanner rule, exclusion, baseline, source substitution or legal/admission claim
changes. Earlier c3 fullPASS and native2PASS remain true only for their recorded
scopes; they do not qualify the changed producer's final output. Regeneration of
the tracked canonical report follows native3, before the new full harness, so the
failed old rendering is not silently edited or carried as a current result.


### 2026-10-18 — readable summaries actual-source regeneration

Native3 passes on4126170a: two network-denied14-object replays, same numeric/gap
counts and unchanged source bytes. Actual regenerated reportfccc3850 replaces
only the three methodology summary values; every other report field/value equals
the preserved previousbbd251a4 report. Current report/native/guide pointers now
refer to these generated bytes. Original native2/full1 successes, native1 failure
and docs-scan failure retain their exact historical scopes. No detector exception
or baseline/rule change was made. Full2 on this corrected producer and tracked
report remains pending; no PR is opened before it succeeds. See the dated scan
recovery record for the precise false-positive diagnosis and remedy.


### 2026-10-18 — corrected producer full assurance

Full2 on69afe04b/tree12528659 exits0 with7916tests/12skips/23warnings261.09s,
unchanged80percent coverage floor,66schemas/56documents,9/9parity/zero divergences,
all mutation/hygiene/audit/licence/secret-scan/SBOM gates passing. CAS404.66MB/s;
SBOM113components. The readable report clears the original false positive with
no scanner policy, exclusion, baseline or approval exception. Preserve full1,
failed docs scan, native1 and both prior/new canonical reports separately.

The final assurance receipt records the exact corrected executable tree and log
9aabb76c. Native3's source/report checks remain valid because no production,
test, runtime, capture or query bytes changed after native3; current report is
fccc3850. This closeout changes only result documentation. Affected documentation
checks and required exact-head hosted checks precede protected merge; no further
unchanged full/native replay is indicated. Broader track and rights/analytical
admission gates remain open.


### 2026-10-18 — hosted CodeQL exact-anchor comparison

PR709 opened after native3/full2/final-doc checks passed. Separate CodeQL
findings check failed with alert3 py/incomplete-url-substring-sanitization at
owner anchor membership; analysis job itself passed, and platform assurance was
still running. Existing runtime comparison was exact membership in list[str],
not substring matching. Preserve alert/check evidence outside Git. Add the
specific attacker-path case: an unqualified host whose path contains the exact
trusted URL is already rejected before the change (1PASS1.43s).

Make the same full-string equality explicit through any(link == expectedURL),
without relaxing the parsed-anchor/ownership requirement or suppressing the rule.
23focused checks pass1.17s after the change, plus Ruff/format/type. No source,
query or report contents change. Earlier native/full receipts retain their exact
heads; new exact-head CodeQL/platform assurance remains pending. Do not merge or
prune while any required check is non-terminal or this finding remains active.


### 2026-10-18 — component cohort delivered; Supplementary dispatch selected

PR709 merged normally as6b8c2ee0 after seven named gates succeeded on7ada6fec,
all review threads resolved and current CodeQL alerts empty. Fetched checked and
merge commits have identical8d5fcaf1 tree and zero unique changes. Topic refs
pruned; primary checkout and all original/failure evidence retained. Exact-head
full3/native4 receipts and reportfccc3850 are retained. The tracked current full
receipt represents its completion flag as a boolean; the original external
receipt and its SHA remain preserved, without changing a scanner rule/baseline.

Next Phase3 work adds common dispatch for already normalized2024/25 and2025/26
Supplementary summary profiles (5+6facts,30pages each). Existing overview and
forecast registrations already cover those independent sources; do not rebuild
them. Preserve source $000, capital-injection authorisation distinctions and
literal dashes/nulls. Extract native logic into a shared pure snapshot boundary
without altering existing standalone product bytes. Source profiles and existing
schemas stay closed; no new source capture, legal approval or analytical join.
Conductor remains the native/full launch owner; original source code references
are retained outside Git for actual old/new comparison.


### 2026-10-18 — Supplementary dispatch focused qualification

The initial import check failed because supplementary_summary_adapter did not
exist (red-1.log retained,0.54s). Each existing normalizer now exposes a pure
hash/edition/page-guarded extract_snapshot used by both its standalone writer and
common adapter; no separate parser/fact construction is introduced. Existing
schemas/IDs/token conversion/quality flags and standalone page-disposition output
are preserved. The common adapter additionally accounts for all30pages, keeping
the selected page partially normalized and the other29preserved-only. Registry
contexts are explicit, source locator/vintage-bound, sorted and duplicate-rejecting.

Initial focused25checks pass1.39s. Expanded normalizer/registry/overview selection
passes41checks1.60s; record and field-lineage equality against standalone Parquet,
repeat dispatch, source bytes, dash nulls/capital-injection flags, changed-source
fallback and invalid contexts are covered. Initial lint/type findings are
preserved; typed closed profile bindings and test context types fix them without
assertion suppression. Ruff/format/strict typing pass. Actual retained-source
old/new byte comparisons, repeat proof and the repository harness remain pending
with the existing Conductor launch owner. No source capture or rights/policy
change occurs.


### 2026-10-18 — Supplementary dispatch actual-source and full assurance

On clean ad36a7a7/tree69a6478e, native2 passes two network-denied replays
against both original CAS PDFs and pinned pre-change normalizers. All four
standalone product files per edition are byte-identical to the baseline; common
dispatch matches11facts and33field-lineage records, accounts for60pages and
preserves58unselected pages. Altered source bytes remain preserved-only; source
originals are unchanged. Repeat report ca84c64c040812f75a422235bda5a137a44f32b4c30fc16262af5be69b081709.

Native1 stopped at metadata-sensitive Arrow-versus-Parquet equality after the
2024/25 baseline files already matched. Bounded diagnosis established identical
values and only the Parquet list-child name item-to-element representation
change. Native2 explicitly compares values and then compares identical Parquet
representations with metadata sensitivity retained. Original failure, recipe,
log and partial products are preserved externally; production code is unchanged.

Original ./scripts/validate.sh passes on that exact frozen commit:7922tests,
12skips,23warnings,251.85s;97.23% coverage against80% floor;66schemas/56documents;
parity9/9 with zero divergences; all mutation, hygiene, performance and supply-chain
gates;113SBOM components. See supplementary-summary-dispatch-20261018.json for
full log and native recipe/report pins. This documentation integration follows
terminal release; affected document gates and hosted delivery remain pending.
Broader phase/rights/analytical and track completion claims remain open.


### 2026-10-18 — Donor SQLite common dispatch implementation

After PR710 merged and its clean topic refs were pruned, the next Phase3 slice
exposes the pinned donor SQLite source through explicit common dispatch. The
existing path reader delegates to the same capped-byte, fixity/schema/VM/row-
bounded query-only in-memory reader. Both standalone and dispatch projection
reuse the existing Silver record/lineage construction. No donor value, period,
currency label, historical disposition or rights rule is replaced. The registry
opts in with explicit observation context and preserves its default four profiles.

Initial missing-module red is retained. Focused25contracts passed; expanded run
had42passes and one test comparing fresh adapter object identity, corrected to
compare the registry identity/version/media contract. Final44checks pass2.13s,
including native fixture equality, repeats, changed-byte fallback, direct fixity,
size/row guards, registry opt-in and existing Silver/Gold/boundary contracts.
Lint/strict typing pass after import/type fixes. Actual312-row comparisons against
pinned pre-change reader and Silver code, native repeats and full harness remain
pending. See donor-sqlite-dispatch-20261018.json; no PR yet for this slice.


### 2026-10-18 — Donor SQLite native/full assurance and fixture follow-up

Native1 passes two network-denied runs on clean e36b6bea/tree428ea8fd: the
pinned49,152-byte donor source remains unchanged; both native files match the
independently pinned pre-change reader/normalizer bytes;312facts,1699lineage,
five tables and retained donor values agree. Repeat report9a105be2565efb4efb5d061a2fd16835415e41c8f7691ab626d30ac8acd28404.

Full original ./scripts/validate.sh passes on that exact frozen commit:
7926tests/12skips/25warnings257.26s,97.23% against80% floor,66schemas/56docs,
parity9/9 zero divergences, all mutation/hygiene/performance/supply-chain gates,
113SBOM components. Original25warnings remain preserved; extra database warnings
were traced to the reused test fixture transaction context, which did not close
its connection. Production read_snapshot already closes in finally.

After terminal release, the shared fixture gained closing outside its unchanged
transaction context, preserving commit/rollback before close. Its only direct
importer is the new adapter test. Both affected suites pass10tests6.99s without
warnings; lint/format/strict typing pass. No production/runtime/native input
changed after full assurance. Evidence closeout and hosted exact-head checks
remain separate gates; no additional native/full rerun is required for this
fixture-only correction. See donor-sqlite-dispatch-20261018.json.


### 2026-10-18 — Exact donor stage-receipt reconstruction

The older twelve-stage run directory was not retained. Bounded lookup found
no exact stage directory; Conductor identified the existing replay_eight.py
recipe and surviving donor893f387e/candidate9a33babd/Crown4bea6001 inputs. All
three live input hashes matched their historical pins before native execution.

On clean33ae9e4e/tree8fa7c33f, the guarded network-denied native1 reconstructs
two new permanent runs using the existing historical normalization context
2026-08-30T08:58:00+00:00. Both contain739facts/12stages/50files and pass the
existing verifier. ALL50 output-file hashes and ALL12 stage-manifest hashes
match the historical evidence exactly, including the previously unavailable
Budgetf051c4 receipt. All23donor objects plus the separate Crown source and
all pinned metadata are unchanged before/after. Proof SHA63a7fdd6eb5e99e9fcb1489f591860ccb85abd10b3e72f1958b22de69afd1f8f.

Current reconstructed files are retained permanently under evidence/
donor-area-recovery-20261018/native-1 in the external archive; they are not
mislabelled as the missing original directory or fresh source captures. See
donor-area-reconstruction-20261018.json for all exact recovered stage pins.
This removes the exact-receipt availability blocker. The remaining nine
stage-to-area bindings still require source/selection/lineage qualification,
with Crown kept source-separated if outside the donor inventory. Existing
three partial assertions and whole-worksheet remainders remain unchanged;
all152worksheet semantics, rights and broader track completion stay open.
No full/hosted delivery claim is made for this in-progress slice.


### 2026-10-18 — Remaining stage-to-area binding producer

The new stage_area_bindings producer reuses verify_eight and its per-profile
source/output/lineage contracts, then the existing bounded Parquet snapshot
reader. It binds selected fields to exact donor source hash/path/sheet IDs,
checks quoted/unquoted cell coordinates against the retained inventory bounds,
and emits partial bindings plus a nine-stage receipt catalog. Source records
may overlap between context sheets; record sets are explicitly non-additive.
Crown2025 is source-separated when absent from the donor inventory, never
matched to Fiscal2024 by a similar filename. No original workbook reparsing,
new source capture, value replacement, mapping/rights promotion or file write.

The pure projector is explicitly not a standalone source-admission boundary;
operational calls must use build_stage_area_bindings and its existing verifier.
The prior three partial assertions are retained separately and no global unit
state is resolved. New focused coordinate/identity/remainder/Crown contracts
initially fail missing-module collection, then113checks pass0.40s. The expanded
area/stage/orchestration selection passes229checks6.47s; Ruff/format/strict typing
pass after bounded lint corrections. Retained-output producer readback, full
harness and hosted delivery remain pending; no unchanged reconstruction rerun.


### 2026-10-18 — Native binding failure and narrow source-contract recovery

Bindings1 stopped before full validation at the coordinate contract. A bounded
pinned-output diagnostic identified exactly61unsupported references, all Crown
source_context cell@number_format properties; no ranges, composites or other
grammar were observed. Failure log/recipe/partial output and diagnostic remain
preserved. The projector now permits only the evidenced Crown/source_context
suffix, checks its underlying cell bounds and retains the full annotated
reference in context coordinates, never in amount coordinates. Unknown property,
wrong profile/field and bad bounds still fail closed.

Review also identified the missing explicit binding between supplied donor
inventory and the verified run PLAN. A bounded regular snapshot is JSON-decoded,
canonical encode_json hash checked against the existing verifier plan_sha256,
then legacy_plan.donor_manifest_sha256 must equal the supplied donor pin. The
legacy plan hash is canonical content, not raw newline-terminated file bytes.
Native retained inputs were already the same donor; this closes public-reader
cross-snapshot acceptance without changing any reconstructed product.

Focused source/property/plan-mismatch regression and existing area/verifier/
orchestration checks pass236tests5.16s after a test-import correction; initial
2failed/234passed evidence remains retained. Ruff/format/strict typing pass.
Revised bindings2 readback and required full harness remain pending on a new
frozen head; no workbook reconstruction is repeated or prior failure erased.


### 2026-10-18 — Nine-stage binding readback and full assurance

Revised bindings2 passes on clean44ce414b/tree dcf1c955. Both existing retained
reconstructions produce the same report312cd02dc17da9dd122eb43e7f763de1981a2e56d78dd23c5800a044d8a35eaf:
9stages covering613facts,12bindings (11partialdonor +1source-separatedCrown),
all61Crownformat context coordinates preserved outside amount coordinates,
all158global units still unresolved and previous3partial assertions unchanged.
All100reconstruction files remain byte-identical. This is bounded existing-
product readback through the existing verifier, not workbook re-extraction.
The bindings1 failure/diagnostic and partial directory remain preserved.

Original ./scripts/validate.sh passes on that exact frozen head:7939tests,
12skips,18warnings296.06s;66schemas/56documents;parity9/9 zero divergences;
all mutation/hygiene/security/supply-chain gates;113SBOMcomponents;
CAS399.66MB/s. The configured overall coverage floor remains80%. Terminal
session60707 returned0 and released the shared slot before this evidence-only
integration. See donor-stage-area-bindings-20261018.json for exact log/recipe/
report pins and separately scoped reconstruction evidence. Final documentation
and exact-head hosted checks remain pending; no whole-worksheet/rights/Gold or
track completion claim is made.


### 2026-10-18 — Seven literal profiles through five physical source bundles

After delivered/pruned PR712, the next Phase3 increment closes common-dispatch
coverage for the existing seven literal admissions. Five exact physical source
identities compose shared-file BEFUchart/residual and HYEFUallowance/residual
profiles, rather than registering ambiguous competing handlers. Every reviewed
sibling is included. The existing source path guards remain; pure capped/hash-
verified byte admission shares their unchanged parsers. Native persistence and
common extraction share the same literal projection and Crown capture-context
binding; no second fact/lineage parser or new source acquisition is introduced.

Known byte identity pins reviewed layout for the fast selector; extraction
still executes the native guarded admission. Unknown bytes preserve-only and a
sibling admission failure returns no partial packet. Typed native facts retain
all original JSON/source tokens. Common field lineage preserves raw_value_json
on both sides with literal_source_json_preserved/v1, not a new conversion.

Review identified the need to retain area exception lists and record IDs, not
only the generic loss triple. This adapter's source_coordinate uses the narrow
literal-area-json/v1 prefix plus canonical JSON of the complete native area row
and its logical profile. State and reason remain native; every original field
can be decoded directly, with no global protocol/schema or old output change.
The focused test compares complete reconstructed rows, including exceptions,
record associations, source identity and profile, not a reduced projection.

Initial missing-module red is retained; five physical bundle fixtures plus
inventory checks pass6tests1.45s. Expanded shared admission/packaging/registry/
workbook/verifier/orchestration checks pass257tests8.18s. Native admission89 and
package16checks pass independently. Ruff/format/strict typing pass after bounded
style/type corrections; earlier logs remain. Native qualification now passes two independent runs:329facts/5543lineage/
606complete area dispositions, five physical sources/seven profiles and all28
standalone files per run identical to historical pins. All50reference files and
source bytes remain unchanged. Report SHA256 is recorded in the checkpoint.

The first replay reproduced all28files, then file-denial instrumentation blocked
PyArrow's first UTC/platform dependency initialization. Preserve that failure.
The second recipe warms verified Arrow UTC conversion before denying Python
file APIs during common dispatch; network denial remains throughout. This is
warmed-dispatch assurance, not an operating-system sandbox claim. No producer
change or dependency installation was needed.

The original full harness passed on0c378f4e/treebfd0ae9e:7951tests,12skips,
18warnings,505.09s and97.20%coverage against the unchanged80%floor. All66schemas,
56representative documents,9/9parity and mutation/hygiene/security/supply-chain
gates passed; CAS232.13MB/s. Hosted checks, normal merge and pruning remain
pending. Rights, currency, periods and global mappings are unchanged.


### 2026-10-18 — Fiscal2024 historical common dispatch

The closed source769f2e7d now shares byte extraction with the original historical
path writer. Preserve native XML numeric lexemes, typed facts, field lineage,
all cell disposition fields and six excluded-sheet reasons; no new semantic or
rights claims. Three new contract checks plus existing affected suites pass308
checks15.53s. The exact106fact/1143lineage/1503cell/six-sheet native replay and
required full harness are pending. The prepared proof compares all four old
native hashes and two report builds, and tests unambiguous coexistence with the
five literal bundles. See historical-common-dispatch-20261018.json.


### 2026-10-18 — Native historical proof and census code binding

Both native replays passed:106facts,1143lineage rows,1503complete cell
dispositions, six excluded sheets and1509losses; all four products match old
pins and original source/reference bytes are unchanged. The reports have equal
SHA256 b14b274911e2623cfbb2eb4228c279a775cf6b0f46581841a7dd7101da6be520.
Warmed dispatch denied Python file APIs; network was denied throughout.

Full1 stopped at tests with7952passed/2failed/12skipped/18warnings271.03s,
97.14%coverage. Later full-harness gates did not run. Both failures were the
census's old historical.py code-evidence hash. Preserve original census bytes
in context-census-pre-historical-dispatch-20261018.json and refresh only that
reviewed code hash after native parity. Every series/source/qualification/rights/
join field and every other evidence pin is unchanged. Existing affected census
and adapter checks now pass28tests6.84s. Full2 remains pending; no native repeat.


### 2026-10-18 — Historical full2 qualification

Original full2 passed all32stages on780f3040/tree46064578 after the one-pin
census repair:7954tests/12skips/18warnings283.60s,97.19%coverage against the
unchanged80%floor. All66schemas/56documents,9/9parity, mutation, hygiene,
audit/licences/secrets and113component SBOM gates passed; CAS157.57MB/s.
The full log and terminal receipt hashes are pinned in the existing checkpoint.
Native1 remains valid because producer/tests/runtime are unchanged; no native
repeat. Original failed full1 and census binding remain retained. Hosted checks,
normal merge and pruning are pending; no rights or analytical admission change.


## Budget 2024 revenue qualification — 2026-10-18

The [qualification receipt](./budget-2024-revenue-qualification-20261018.json)
binds the actual retained source, two identical four-file builds, common-dispatch
parity and all 32 original full-harness stages to head 64d40613/tree 754e4eb6.
It records 66 facts, 1,056 lineage entries, all 1,004 source rows and zero rejects;
8,034 tests passed with 14 skipped. The source remains unchanged and the root
owner verified actual exit 0 and lease release. Full log SHA-256:
`10b3a06c1d7ef958922e8d865c730cf90779d4655d09e43add61010ef37bf5a8`.
Only track receipts/documentation follow that qualification. Exact-head hosted
checks and protected delivery remain pending. ISO currency, period starts,
rights adjudication, Gold joins and publication are separately bounded.


Corrected source-entry qualification passes on89fdb3c9/tree8eb3dbbf: actual
CLI/MCP read-only preflight parity and explicit CLI writing reproduce the
prior four native files exactly. Corrected original ./scripts/validate.sh
passes all32 stages:8038tests/14skipped/18warnings in429.01s,97.18%coverage
(unchanged80%floor),66schemas/56docs,parity9/9,allmutations/hygiene/audit/
licences/secrets/SBOM113 pass. Full log SHA
d587161040e4414e2dc2d6e73167d161328b757dd13942ffac3c5e62aff3951b.
Entry summary SHA09dfcfd899f191553b4ddf21fa2c380b6da4387e47f907ade364f4dcc7a4676d.
Both actual source/full exit markers are0; source-owned processes ended and
nonblocking kernel acquisition/release plus clean head/tree/all pins verify
release. Earlier proofs remain retained. Post-qualification changes are track
receipts/docs only. Fresh exact-head hosted checks and protected delivery follow.


### 2026-10-18 — Budget2024 expenditure profile, local focused gate

The source-bound profile preserves all17 source columns, explicit parent/category/
group/periodicity qualifiers and original numeric tokens. Literal $000 retains
unknown ISO currency and no period start. It does not aggregate or map source
classifications. Existing CLI/MCP source-operation registration and closed schema
include the profile; legacy expenditure dispatch refuses this2024 edition so it
cannot emit the legacy NZD schema. Other vintages remain unchanged.

647broader tests pass/10skip; final9profile cases pass after caller-Decimal
isolation. Ruff, strict types,66schemas/56docs and93Conductor tracks pass.
Actual source and original full qualification remain pending root-owned launch.
See budget-2024-expenditure-profile-20261018.json.


### Budget2024 expenditure native qualification and local timing evidence

[Qualification](./budget-2024-expenditure-profile-20261018.json) retains
actual-source CLI/MCP/repeat/common-dispatch proof:244facts,6100lineage,
all6645rows and zero rejects; source bytes unchanged. Three original local
full attempts remain explicitly failed(timing/hostcapacity), with logs and
terminal/kernel-release receipts retained privately. Focused/static gates and
source contracts pass. Existing exact-head hosted fullchecker remains pending;
no local fullpass, broader semantic admission or publication is asserted.


### 2026-10-18 — Budget 2024 delivered; Budget 2023 release reconciled

PR 718 is merged after all seven checks and all 32 stages on each hosted
platform. The delivery receipt retains exact heads, trees, log hashes and
post-merge cleanup checks; local failed runs remain failures. The next 2023
release observation identifies the two existing locators, period labels and
declared page licence. Four inventory surfaces and 360 first WARC headers
have no exact matches; that bounded check establishes neither global absence
nor alias equivalence. Source bodies, native units and item notices are pending.


[Budget 2023 capture](./budget-2023-capture-20261018.json) records two privately
preserved originals, independently verified CAS/WARC bindings and receipt
hashes. The failed module-import attempt is retained and had no source-side
operation. Capture2 is terminal 0 with a released kernel lease. Native layout,
units and item-level rights remain pending; no numerical or publication claim
is made from transport success.


Budget2023 native inspection is recorded in `budget-2023-native-inspection-20261018.json`. Revenue source profile implementation has focused581-pass/10-skip evidence; actual-source repeat qualification and full assurance are not yet claimed. Expenditure normalization and wider phase gates remain open.


See `budget-2023-revenue-native-20261018.json`: native repeat/dispatcher and actual CLI/MCP qualification passed on f865f698. All four file hashes match across both direct builds and CLI output. Full assurance and protected delivery remain pending.


`budget-2023-revenue-assurance-20261018.json` records the original32-stage local pass on3d55f173. The full log and independent terminal/fixity proof are retained privately. Hosted exact-head checks and protected merge are not yet claimed.


`budget-2023-expenditure-profile-20261018.json` bounds the next profile and records red/green focused checks. Native qualification, unchanged2024package bytes and the original full harness are pending. PR719 delivery is recorded separately in `budget-2023-revenue-delivery-20261018.json`.


`budget-2023-expenditure-native-20261018.json` records actual-source277facts/7,479lineage with6,696-row accounting, complete repeat/CLI/MCP/dispatcher parity, and unchanged2024four-file bytes. Frozen inputs and actual terminal exit independently verified. Full assurance and protected delivery remain open.


`budget-2023-expenditure-assurance-20261018.json` records the original local harness timeout at900s/97%, with7,826observed pass entries and no observed assertion failure. The suite was incomplete; this is not a full local pass. Native and2024byte proofs are unchanged. Full hosted assurance and seven exact-head required checks are mandatory before protected delivery.


`readable-pdf-layout-diagnostic-20261018.json` records three default-readable exclusions and an indirect-Font metadata defect, exact retained-source identities, diagnostic summary pins and focused red/green evidence. Native cohort and prior-descriptor parity remain pending; no new fiscal facts or rights/publication claims.

- Full retained PDF qualification: `readable-pdf-layout-qualification-20261018.json`; 59/59 recorded, 56 prior rows unchanged, two byte-identical builds and unchanged Bronze. New report `source-pdf-layout-baseline-20261018.json`; old report retained. Full/hosted delivery pending.

- PDF full local assurance passed all32stages: `readable-pdf-layout-assurance-20261018.json`. Source-health adoption passed after a retained stale-context comparison: `readable-pdf-source-health-qualification-20261018.json`; new paired v2 report `source-health-report-20261018-pdf-layouts.json`/`.md`. Protected delivery pending.

- Protected delivery and cleanup: `readable-pdf-layout-delivery-20261018.json`; PR721 merged2fa3183b, all7checks/all32stages on3platforms, equal checked/merge tree, zero unique changes, topic refs absent and primary retained. Broader track incomplete.

- Budget2022 preliminary census: `source-census-budget-2022-20261018.json`; registered pair, six-inventory zero-hit and360-header zero-candidate reconciliation. Native bytes/units/rights remain pending.

- Budget2022 capture: `budget-2022-capture-20261018.json`; two HTTP200 originals independently verified, one release-page HTTP403 retained. Partial attempt exited2; this is not a whole capture pass. Native source inspection remains eligible; rights/page transport held.

- Budget2022 native observation: `budget-2022-native-inspection-20261018.json`;17/8headers,6568/1015occupied rows, source-preserving definitions and exact inspected-report hashes. No facts/rights admission;2022profile implementation and qualification pending.

- Budget2022 implementation prerequisites: `budget-2022-profile-implementation-20261018.json`; exact native definition equality, six new contracts and corrected540-case affected assurance. Actual-source/full/hosted qualification pending; zero facts admitted at this checkpoint.

- Actual Budget 2022 qualifications: `budget-2022-native-qualification-20261018.json`; expenditure307/8289 and revenue64/1024 facts/lineage, complete6568/1015row accounting, repeats and CLI/MCP/common parity, plus unchanged prior2024expenditure/2023revenue packages. Full/hosted/protected gates pending.

- Original local full attempt: `budget-2022-assurance-20261018.json`;900s test-stage cap at99%, all6newcases observed passed, no observed failures, no final coverage/suite/all32pass claim. Native proofs/source/code unchanged; all32clean-hosted qualification and protected delivery required.


PR722 delivered: all7exact-head checks/all32hosted stages per platform; merge95f9f638 verified fetched main/head ancestry/equal merge tree/zero unique commits and patches/clean. Topic local/remote/tracking absent; one primary/CAS/runtime/proofs retained. See budget-2022-delivery-20261018.json. Local full2 remains124 with2observed failures, not a pass. Serial/instrumented probes and140unchanged affected-module tests distinguish startup sensitivity from proven FIFO rejection; earlier timeout location unproven. Conductor advice requested, no approval claimed. Next bounded Phase8 task isolates input-spec inspection from plot/product startup without widening limits or changing product bytes.


Reader native qualification: first10s child-startup timeout is retained.
Instrumented attempt2 reads the retained5-input spec in2.14s without plotting,
then both native Gold builds match all20independent prior files and source-
regenerated readback returns615observations/585eligible/30excluded. All248
frozen code/runtime/input pins remain unchanged after terminal execution.
Actual full-source CLI preflight then times out at its original30s probe cap
with no output; registered MCP probe was not reached. Do not claim complete
CLI/MCP or a startup SLA. See context-reader-startup-native-20261018.json.
Original full harness and protected delivery of the reader-only slice remain
pending; broader Phase8 stays incomplete. Conductor design advice requested.


Reader original full attempt: eac7a9ab/tree65ea021d ran the unchanged
./scripts/validate.sh with supported2workers and original900s per-stage cap.
Five fast stages pass; test stage exits124at86%,6991observed PASSED and
0observed FAILED entries. No final suite, coverage or all32local pass claim.
All292frozen code/runtime/input/output pins remain unchanged and the kernel
lease is free after terminal execution. See context-reader-startup-assurance-
20261018.json. Proceed with focusedPR under the existing run-before-PR contract;
require exact-head original all32stages on3clean hosted platforms, all7checks
and resolved review before normal protected merge/prune. Actual full-source
CLI30s timing and unrun MCP remain separate open Phase8 evidence, not complete.


PR723 P2 provenance correction: restore the Budget2022 qualification,
implementation and dated census snapshots byte-for-byte to merged95f9f638,
and retain the reader implementation checkpoint at producer5f0a94df.
Transitions/current status live in separate versioned projections and the
new delivery/native/assurance receipts. This supersedes earlier in-place
status-reconciliation wording; no historical checkpoint is rewritten to
claim later merge. See budget-2022-state-20261019-v1.json and
context-reader-startup-state-20261019-v1.json. Code/source/product bytes and
previous qualification results unchanged; original local timeout preserved.


Recovered standalone operational replay3 at b2212f7c/treeb0881b67:
original console preflight completes12.13s within its unchanged30s bound;
all19 predicted products match the independent retained package. Initialized
stdio MCP initialize/list/read-only call completes, call10.11s within30s,
615records across5inputs and19outputs; neither output directory is created.
After PortableSSD reconnection all frozen code/input/source pins match, runtime
versions match and kernel lease is free. Recipes, logs, raw responses and both
diagnostics are copied with hash readback. Prior native1/2timeouts and original
local full124 remain immutable; no unconditional startup SLA. See
context-reader-startup-replay-20261019-v1.json and current-state v2. Hosted
b221 Ubuntu passed; macOS test stage hit original900s cap at96% with no final
summary; Windows was non-terminal at observation. Protected delivery remains
blocked until exact-head required assurance succeeds. Broader Phase8 and track
completion remain open; no rights/currency/joins/publication admission.


PR723 delivered normally at ae4f870c after seven exact-head successes on
625a8b8e and all32 original stages on Ubuntu/macOS/Windows. Source-focused
41-test/API product and standalone CLI/MCP evidence remains separate from the
retained local full124 and earlier hosted macOS timeout. Review resolved; no
open CodeQL alert. Fresh fetch proves checked-head ancestry, equal9e17847b
merge tree, zero unique commits/patches and clean main. Topic local/remote/
tracking refs pruned; sole primary, runtime, CAS and private proofs retained.
See context-reader-startup-delivery-20261019.json and current-state v3.

Next bounded Phase3 slice: shared expenditure registry and legacy normalizer
currently route only2022 to its pinned edition profile; generic adapter refuses
2023/2024 despite both qualified source profiles. Extend the existing2023/2024
contracts for shared-registry fact parity and legacy four-file equality; route
existing profiles without changing source bindings or semantics. Reuse retained
native sources/packages; root remains sole broad/native launch owner, unchanged
900s original harness and80%floor. No external collection/publication mutation.


Edition-routing red reproduces two empty fact outputs for reviewed2023/2024.
Shared registry and legacy normalizer now select their existing edition-specific
registrations/normalizers; other editions retain generic fallback. Existing
2023/2024 cases require shared-dispatch fact equality and legacy entire-package
byte equality. All72focused contracts pass33.24s; no test count added. Ruff and
focused Pyright pass after import wrapping only. No profile/parser/source/hash/
locator/vintage/rights/currency/period/coverage/cap/protection changes. Retained
native four-file equality and original full harness/protected delivery remain
pending. See budget-edition-routing-implementation-20261019.json.


Edition routing native qualification at82a7ea33/tree8a87f078 passes:2023
277facts/7479lineage/all6696rows and2024 244facts/6100lineage/all6645rows,
zero rejected. Shared dispatch facts/lineage/losses match exact profiles;
two legacy packages per edition match all4independent prior files (16matches).
Originals and frozen pins remain unchanged, terminal0 and kernel lease free.
See budget-edition-routing-native-20261019.json.

Original full1 at same head passed8067tests/14skip/18warnings/97.13% before
interruption after tests; missing terminal marker/remaining26stages means no
full pass. Durable full2 finishes124 at original900s test cap,91%,7409observed
passes and2unchanged legislation-property failures; no final tracebacks or
coverage summary. Both extended Budget cases passed in broad run. Exact two
failed contracts pass focused replay10.25s with original seed2032132534 and
2workers/no-cov; no deadline/assertion changes. Broad cause remains unproven,
coverage instrumentation differs, original failure retained. Conductor advisory
requested; root retains source/native launch ownership. No blind third full
rerun. Require all7exact-head checks and original all32stages on3clean hosted
platforms plus resolved reviews before normal merge/prune. See
budget-edition-routing-assurance-20261019.json. Broader phase/track and all
rights/currency/analytical joins/publication claims remain open/unchanged.


PR725 delivered normally at edeaab6d after seven exact-head successes on
a4c14ec0 and original all32stages on Ubuntu/macOS/Windows. Native shared/
legacy paths reproduce existing2023/2024 facts and16prior file hashes.
Prior interrupted/local124 failures and no-cov replay limitations remain
immutable; no local full pass or proven timing cause asserted. Fresh fetched
ancestry/equal94e746f9tree/zero unique commits/patches/clean-main proofs pass;
topic local/remote/tracking refs pruned, sole primary/CAS/runtime/proofs kept.
See budget-edition-routing-delivery-20261019.json and derived state v1.

Next bounded Phase1 cohort: reconcile all40 registered annualBudget2007–2026
expenditure/revenue resources against existing preservation and qualification
receipts before any further capture. Private crosswalk found10resources with
later JSON references and6with directly referenced matching CAS objects; these
are candidate evidence, not inferred capture/admission or exhaustive aliases.
Resolve retained receipts/WARC bindings and native periods/units/rights gaps;
capture only eligible missing originals through existing preservation core.
Keep each edition and all failure/unknown dispositions separate. Preserve dated
historical/producer checkpoints, no duplicate VoteHealth preflight, no rights,
currency, denominator, fiscal alignment, analytical or publication inference.
Root retains sole archive broad/native launch ownership and original900s/80%
assurance contract. Broader phase/track gates remain open.


AnnualBudget retained reconciliation at29724225/treec78befbf: all479JSON
metadata files and366single-frame WARC headers in four permanent health roots
scanned without exclusions. Exactly6registered URLs have retained candidates:
2022/2023/2024 expenditure/revenue. Actual receipt/fixity, CAS SHA256/BLAKE3/
size and full source-request/response WARC bindings all verify, terminal0 and
kernel lease free. No original recaptured or rights/numeric claim promoted.
34registered URLs remain without exact matches in this scoped inventory;
this is not global absence or source unavailability. Older/newer locators stay
separate pending evidence. See budget-census-retained-20261019-v1.json.

Concrete next capture blocker: current resumed health-capture CLI assigns
host-wide rights eligibility and excludes legacy Excel transport MIME. The
registered cohort has26.xls URL hints, not yet native-byte format findings.
Add an explicit preservation-only mode retaining unknown item rights across
capture/resume/orphan recovery, bind the mode to the capture context, and allow
legacy Excel transport only in that lane. Preserve legacy default behavior,
host allowlist, WARC full-request/source/body binding, resource limits and no
publication/numerical admission. Enforce the existing65MiB WARC recovery read
bound before allocation. Verify only these real contracts and reuse existing
capture/recovery suites; no new coverage target or deadline changes.


Preservation-only red contracts reproduce unselected legacy transport and an
unbounded recovery read. New --preservation-only keeps rights not_evaluated
with null licence/evidence/attribution through capture, failure, resume and
unique orphan recovery. Its versioned policy binds checkpoint identity;
required_rights_policy in a new request prevents omission of the intended mode.
Legacy defaults and contexts remain compatible. Only this lane adds opaque
legacy-Excel transport MIME; actual response media stays recorded, no native
format/rights/numerical/publication admission. Recovery enforces the existing
65MiB limit on regular bytes before allocation and keeps source/response binding.
CLI partial capture now reports partial while retaining its existing nonzero exit.
Two new real contracts;61focused capture/recovery checks pass12.55s and the
added inventory bridge/policy assertion passes separately. Ruff/typing pass;
no dependency, stage-cap, deadline or coverage-floor changes. Actual34-source
preservation, integrated original assurance and protected delivery still pending.

Final refactored preservation-only implementation:61focused capture/recovery
contracts pass11.37s, Ruff format/lint pass and strict typing0errors/0warnings.
See preservation-only-validation-20261019-v1.json. Native capture/full harness
and protected delivery remain pending; original producer checkpoints preserved.


Frozen5f0e27ce/treea4c26478 preservation-only CLI selects34missing exact
registered URLs:18captured,16HTTP404 (terminal_status), actualexit2/partial.
No blind retry. Six retained captures reused, so40-resource cohort has24
recorded captured URLs. All18new CAS SHA256/BLAKE3/size and complete WARC
request/response/body bindings verify. Ten bodies have OLE container signatures
only, pending a qualified legacy reader; eight XLSX native workbook inventories
match repeated builds. Formula-cache freshness, periods/units/definitions and
rights/admission remain unqualified. Existing capture inventory projection
repeats equally,40resources/24recordedcaptured/allrightsnotassessed. Native
verification terminal0; capture/verification owner PIDs/PGIDs absent, independent
kernel lease free and all frozen pins unchanged. Recipes, frozen requests,
markers, logs, layouts, inventory and fixity archived outsideGit with hash
readback. See budget-preservation-qualification-20261019-v1.json. Full original
harness and protected delivery remain pending; cohort/phase/track incomplete.


Original ./scripts/validate.sh at41f2c92d/tree35c69da6: lock,Conductor,
format,lint,types pass. Test stage reaches98% with7979observed
passes/0failures before original900s limit, actualexit124; no final
pytest/coverage summary and no all32localpass claim. Both new preservation
contracts and both previous unrelated failure nodes pass in this broad run.
Underlying timing/capacity cause unproven; no blind repeat or gate changes.
OwnerPID/PGID absent, independent kernel lease free, all1787frozenpins
unchanged at completion. Full log/config/runtime/marker/postflight archived
and hash-readback verified. Exact-head all32 hosted3platform assurance and
all required checks still required before protected merge. See
budget-preservation-assurance-20261019-v1.json. Native capture/verification
producer checkpoints remain immutable and broad phase/track gates remain open.


PR726 head99acb185 hosted Ubuntu tests8053passed/30skipped/18warnings335.08s;
31stage headers reached, then secrets gate rejects one Base64 entropy candidate.
Local reproduction confirms the qualification receipt proof_root directory,
not a credential. Preserve the exact producer receipt (SHA256173090c1575b6ec5
...f4db1654), scanner output and failed hosted log. One new red contract fails
as expected4.23s. Add only an exact document SHA256 plus known candidate
fingerprint/type adjudication through the existing reviewed-document helper.
Thirty supply-chain contracts pass13.64s; changed document bytes, another
candidate/type or wrong line still reject. Full local secret scan then passes
with0unresolved candidates; Ruff and strict typing pass. No file/path-pattern
exemption, plugin removal, security threshold change or producer rewrite.
Capture/CAS/WARC/native implementation and originals remain unchanged. Original
local full900s timeout at41f2c92d predates this scanner-only correction; no claim
that the new correction passed a local full run. Requalify all32 hosted stages
on all3platforms at the new final head before normal protected merge/prune.
See budget-provenance-secret-adjudication-20261019-v1.json.


PR726 merged normally2026-10-19T13:39:19Z atb3fe8f49, checked2b0ff5ea/
treed8b4e373. All7expected checks succeed; all32stage headers and full tests
verified in each exact-head hosted log: Ubuntu8054/30skip542.84s, macOS8054/
30skip795.74s, Windows8048/36skip509.09s. Original local124/98% and first
hosted secret false-positive failures remain immutable. Exact provenance
adjudication qualified without producer rewrites, plugin/path exclusions or
threshold changes. Fetch/ancestry/equal merge-tree/0uniquecommits/0patches/
clean proof precedes pruning; topiclocal/remote/tracking absent and soleprimary
checkout/runtime/CAS/privateproofs retained. See separate delivery/state receipts.
Broader40-URL cohort remains24captured/16terminal404; native periods/units/
rights and ten OLE layouts remain unqualified. No whole phase/track completion.
Next bounded slice: four cached official page identities and nine linked
candidates, including the2012 departmental-statements workbook absent from
registered40. Reconcile retained exact-request evidence first, preserve old
404 observations, no inferred aliases or numerical/rights approval. Root keeps
sole native/broad launcher ownership, existing900s/80% contract unchanged.


Locator slice1 at29728a07/treed3f83510: all13requested candidates attempted;
nine linked workbooks captured/verified, four publication pagesHTTP403,
actualcaptureexit2. All9CAS SHA256/BLAKE3/size and complete WARC request/
response/body bindings pass. Bodies have OLE signatures only, not BIFF/layout/
period/units validation. Rights remain unknown and no numerical admission.
Original40URLcensus/16HTTP404 observations remain unchanged. Existing inventory
projection repeats equally:53distinctURLs/33recordedcaptured; this is URL
observation coverage, not approval of aliases, versions or source completeness.
Nativeverificationexit0; ownerPID/PGID absent, independentkernel lease free,
all1236frozenpins stable. Recipes, request/manifest, WARC/CAS, logs/markers,
inventory and fixity retained outsideGit with hashreadback. See separate
budget-locator-qualification-20261019-v1.json. Full harness/protected delivery
remain pending; broader source/rights/legacy and track gates stay open.


First13locator cohort is qualified for archive fixity and repeat inventory,
with four page403s and native legacy/rights/definition gaps explicit. Continue
the same source-census topic through a separate19candidate cohort: six pages,
eight remaining intended expenditure/revenue locators and five additional
FFS files (2008–2011/2013; 2014page lists onlytwo workbooks). Exact links were
read from cached official pages, not invented by year/filename patterns.
Keep the first13request/checkpoints unchanged; reconcile all retained evidence
before new capture. Cached2008/2010period wording conflicts remain attributed
and unqualified, and no publication date, numerical scope, alias or rights is
inferred. No new production code, dependencies or tests are needed for this
data-only cohort; original full harness and protected delivery remain required.


Second19candidate cohort at3c4f889b/tree41411771:13workbooks captured,
sixpublicationpagesHTTP403, captureexit2. Verificationexit0; all46aggregate
workbook-candidate CAS SHA256/BLAKE3/size and complete WARC request/response
bindings independently rechecked across the six reused originals,18previous
captures and22new locator captures. Each of40intended Budget2007–2026
edition/role slots has an archived candidate;16use exact publisher-linked
locator-correction candidates. Original40URLs/16HTTP404s are not overwritten,
and no numeric/version alias is approved. Six additional departmental-statements
candidates are preserved outside the original40. Aggregate72distinctURLs/
46recordedcaptured inventory repeats equally;32OLE/14ZIP signatures, legacy
layout/period/units/definitions/rights still pending. All10publicationpages
returned403; cache observations remain separate and no blind retry occurred.
OwnerPID/PGID absent, independentkernelleasefree, all1240frozenpins stable;
recipes/frozeninputs/markers/logs/manifests/WARCs/CAS and repeat outputs archived
with hashreadback. See new v2qualification and separate40slot/16correction/
46asset projections; v1and earlier producer checkpoints remain unchanged.
No production code/dependency/test change in this data-only topic. Original
./scripts/validate.sh and protected hosted delivery remain pending. Broad source
census, native legacy/rights, other phase and final track gates stay open.


Fast-first secret gate at26b48985 finds one Base64 entropy candidate: the
immutable v2qualification boolean metadata key (line3), not a credential.
Its known candidate hash is verified against the literal field name and true
value; full document reviewed/pinned. Preserve both original producer snapshots.
Extend the existing exact Health document/candidate table, retaining detector
type, complete document SHA256 and matching line-content checks. No generic
JSON-key/path exclusion or scanner/threshold change. Extend the existing negative
contract by one parameter case: red1fail/1pass5.26s; final31focused checks
pass4.31s, Ruff/format/typing pass. Initial2ISC004 test tuple concatenation
findings were fixed with parentheses before final replay. No new test function,
runtime dependency or capture/CAS/WARC behaviour. Full secret scan and original
harness remain pending. See separate20261020adjudication receipt; earlier
native/source producer bytes and unresolved rights/definition claims stay intact.


The second fast scan classifies a new historical receipt pending-status value
as a keyword candidate. Its candidate hash equals the documented pending token,
not a credential; preserve that exact receipt. Extend the existing exact
metadata table with this one document SHA256/candidate/detector tuple. Each
entry now pins its own detector type; no generic status/key/path exclusion.
Existing guard expanded by one profile: red1fail/2pass0.97s;32focused checks
pass3.63s and Ruff/format/typing pass. Wrong type/candidate/line or edited
bytes still reject. No new test function, runtime dependency, capture behaviour,
coverage target or time limit changes. Further receipts use structured gate
states while historical producer fields stay immutable. New full scan/harness
pending; no full-pass or source-rights/definition/track completion claim.


Original ./scripts/validate.sh at4ebcd917/tree53b0aaba passes all32stages,
actualexit0:8072tests passed/14skipped/18warnings542.19s; schemas/parity/
mutations/audit/licences/scanner/strictSBOM113components all pass. Same original
900s/80%/2worker contract, Python3.14.6/uv0.13.1; no Hypothesis deadline or
healthcheck changes. OwnerPID/PGID absent, independentkernelleasefree, all1806
frozenpins unchanged at completion. Full log, runtime/config, marker, native
output pins and supply-chain receipts archived with hashreadback. Earlier
metadata-candidate failures remain separate evidence; immutable producer
snapshots preserved. See budget-locator-assurance-20261020-v1.json. Exact
final-head hosted assurance and protected delivery remain pending. Native
archive candidates do not establish BIFF/layout/period/units/rights, numeric
alias approval or source/phase/track completion.


### PR727 protected delivery

See budget-locator-delivery-20261020-v1.json. Exact-head CI39271172686 passed
all32 stages: Ubuntu8056/30skip558.22s, macOS8056/30skip869.85s,
Windows8050/36skip504.08s;18warnings each. Seven checks green, active strict
protections, resolved reviews, no open CodeQL alerts. All46CAS/WARC hashes
rechecked. Merge cdbc3652 has the checked tree; ancestry/zero-unique/clean
proof preceded pruning only the topic refs. Local original full remains its
separate4ebcd917 producer with8072passes. Native page403 and original404
records remain distinct from successful verification. Track is incomplete.

Legacy reader native qualification: see legacy-inspection-qualification-20261020-v1.json.32preserved candidates/210worksheet observations,64schema-validated CLI outputs with repeat equality, native exit0 and unchanged source/runtime/evidence pins.5x12 heads are bounded observations, not full-sheet normalization or period/unit/rights admission. Date-mode source-record presence, formula origin/cache freshness and documented unsupported structure remain unqualified.

Original local full assurance: legacy-inspection-assurance-20261020-v1.json records9d687f04/tree2a2c1bf6, all32stages,8090pass/14skip/18warnings597.09s, actualexit0, strictSBOM114components. All3840source/runtime/native/CAS pins stable; actual owner/group absent and independent kernel lease free. This local result does not establish hosted delivery or period/unit/rights admission.

Original79dc7ec0 hosted all32stages/8checks pass after completion-reporting delay; logs/run/check/Date observations retained separately. Synthetic empty-title counterexample demonstrates a declared-schema violation, so that head is not delivered. Focused correction63pass5.03s plus Ruff/format/typing; corrected native parity and full assurance pending. No cancellation or rerun was performed for the prior completion delay.

See legacy-inspection-schema-correction-20261020-v1.json: empty-title rejection is verified by63focused checks, unchanged32positive outputs against both baseline repeats and fresh original full32stage assurance at83b53390 (8091pass/14skip/18warnings581.1s). Actual native/full exits0; all frozen pins stable, owners absent and validation lease independently free. No coverage, timeout, protection, rights or numerical-admission changes.

Budget2021 source-native qualification: budget-2021-native-qualification-20261020.json records exact original bindings,2017–2022 periods, native counts/lineage/repeat hashes, actual30s CLI/MCP checks and six prior-edition package comparisons. Failed timeouts remain explicit. This is source-native Silver only; rights/currency/period-start/canonical/Gold/track completion remain unqualified. Original local harness and PR delivery are still required.

Original Budget2021 local assurance: budget-2021-original-assurance-20261020.json pins the executed head/tree, all32 stages, test summary, immutable log digest, full input fixity and terminal process/lease checks. Native source contracts are unchanged. Hosted protected delivery and broader final track review remain pending.

Budget2021 source-native qualification: budget-2021-native-qualification-20261020-v2.json records exact original bindings,2017–2022 periods, native counts/lineage/repeat hashes, actual30s CLI/MCP checks and six prior-edition package comparisons. Failed timeouts remain explicit. This is source-native Silver only; rights/currency/period-start/canonical/Gold/track completion remain unqualified. Original local harness and PR delivery are still required.

Original Budget2021 local assurance: budget-2021-original-assurance-20261020-v2.json pins the executed head/tree, all32 stages, test summary, immutable log digest, full input fixity and terminal process/lease checks. Native source contracts are unchanged. Hosted protected delivery and broader final track review remain pending.

Budget2020 native qualification: budget-2020-native-qualification-20261020.json records authentic-source counts, exact field lineage, every source row, four-file repeats/operations/common parity, actual30s CLI/MCP preflights and32 prior output hashes. Rights/currency/start-date/joins/canonical admission remain held; original full validation and protected delivery are pending.

Budget 2020 original local assurance: budget-2020-original-assurance-20261020.json pins the original 32-stage run, exact producer/tree, test summary, log digest, all frozen inputs and independent terminal/lease readback. No numeric/source/rights/coverage/deadline admission changes; hosted delivery and broader track gates remain pending.

### 2026-10-20 — Legacy Budget definition census

source-census-budget-legacy-20261020.json reconciles all 32 retained BIFF8 Explanation sheets and complete raw headers. Native cohorts reuse earlier observations and add the 2019 pair, 21 remaining definition sheets, final 2010 revenue tail and nine pending-unit headers. All have repeat equality, actual exit zero, unchanged frozen pins, absent owners/groups and an independently free lease. Source/CAS/WARC identity and 121 reconciliation inputs were verified. Direct amount-scale evidence exists for 23 sources; nine unit gaps and the 2014 revenue B10 edition conflict remain explicit. No numeric/formula/currency/start-date/rights/join admission or new source/publication mutation. Full validation and protected delivery are pending.

Original legacy census assurance: source-census-budget-legacy-assurance-20261020.json records the frozen producer/tree, original 32 stages, test summary/log digest and all evidence pins with actual terminal/process/lease readback. No numeric or rights admission. Hosted delivery and broader track gates remain pending.

Budget2019 BIFF8 native qualification: [machine receipt](./budget-2019-biff8-native-qualification-20261020.json), [scope and operational boundary](./budget-2019-biff8-silver.md). Two originals;319/63 facts;complete6288/1020 row accounting;1595/189 source-bound witnesses;repeat/operation/native parity;actual CLI/MCP twice under30s;40 prior modern file hashes unchanged. Producercc93f485;summary9af48e97e63b2bbb2186e9c51b2911c0a6b190d80ef5cc8ac42f254e35934564;actual exit0,9749pins stable,owner/group absent andlease free. Original full and protected delivery pending.

[Budget2019 BIFF8 original full assurance](./budget-2019-biff8-original-assurance-20261020.json): interrupted full1 preserved without a pass claim; fresh full2 passed all32 stages after exact-input recovery verification and normal remote checkpoint. Runtime/fixity/process/lease and original supply-chain receipts retained. Protected delivery remains pending.


2026-10-20 BIFF8 canonical/Gold native2: producer00faaa1d,319/63facts,9495field links and1784numeric witnesses. Both canonical packages retain native1 hashes; all11Gold files repeat exactly, both named queries verified. Manifest1,401,950bytes under unchanged4MiB cap. All4834frozen pins unchanged and launch lease independently free. See biff8-canonical-gold-native-20261020.json; full assurance and hosted delivery pending.

Native3: requalified the closed v3 producer after the original full1 registry finding. Both original-source canonical packages and combined Gold retain all previous output hashes; complete row and witness evidence remains unchanged. See biff8-canonical-gold-native-20261020-v2.json. Fresh original full2 pending.


Original full3 on2a36724d terminated124 at the unchanged900s test-stage cap: 5822observed PASSED,1observed FAILED (checkpoint property contract; no final trace before cap),71percent, no final suite/coverage summary and no all32local pass. Five fast stages passed. All4884pins stable, all captured owner/nested groups absent and kernel lease independently free. Preserve original full1 failures and aborted full2launch; no old log was overwritten. Under AGENTS.md run-before-PR contract, proceed to focused PR with incomplete local assurance explicit; require original all32stages on exact final head across Ubuntu/macOS/Windows, all required checks and resolved findings before normal protected merge/prune. This does not complete whole-track final assurance or change any threshold/deadline.

### BIFF8-inclusive recovery qualification — 2026-10-20

[Native receipt](biff8-recovery-native-20261020.json) records producer32a2da51,
two fresh seven-source builds (65files), complete Gold repeats (60files), all10
exact query readbacks (908bounded rows from1182facts), and composite metadata
(3packages/15recordsets/1566rows). All1241input records are accounted for.
The sorted legacy companion retains7063links; full BIFF8 lineage/witnesses remain.
All47 default-v1 source output hashes and48 prior Gold Parquet/plots match prior
qualification. Final postflight verifies4848pins, owner/group absence and free
lease. [Review](biff8-recovery-review-20261020.md) records bounds and remaining
whole-track gates. Original validation and protected PR delivery follow; native
qualification is not a rights, publication, standards or full-track claim.

### Budget2018 source-native BIFF8 qualification — 2026-10-21

[Native receipt](budget-2018-biff8-native-qualification-20261021.json) records
two unchanged-source builds of the2018 pair:382facts,9482field links,7178row
dispositions and1782numeric witnesses. All standalone/source-operation output
hashes repeat; complete native carriers match. Actual CLI/MCP preflights pass
within30s twice each per source/run. Existing2019 source packages retain all10
file hashes. Original/full/hosted delivery remains pending;2018 canonical,Gold
and recovery integration is not claimed. Rights/currency/start-date/aggregation
and cross-source holds, older unit/edition gaps and donor decisions remain.
