# Self-Review

## 2026-10-03 — Query-free redirected orphan recovery

The runner adopts a redirected orphan only when the original source URL hash
matches the selected census row and the WARC's single query-free HTTPS target
matches the stored full final-URL digest. `verify_response_binding` then checks
the WARC digest, one-record framing, response metadata and body fixity before
the CAS object is promoted. Query-bearing or fragment-bearing targets cannot
match the privacy-preserving target URI and remain untouched for fresh capture.
The focused regression proves recovery preserves the orphan bytes and avoids a
second request; the 34-test checkpoint suite, Ruff, basedpyright and full
repository validation pass. No rights, publication, source completeness or
power-loss claim is made. The initial hosted assurance run found stale hashes
because the source census and source-measure review pin the append-only
evidence ledger; their dependent pins were refreshed. That exposed the further
source-census digest pin in the recovery-assurance tool, which was updated too.
All three evidence-binding suites now pass (62 tests); full validation is being
repeated on the corrected pins. The next full run caught a secret-keyword false
positive in a new evidence field name; the status field was renamed, dependent
hashes and the recovery pin were refreshed, and the same 62 tests pass. No
credential value was present. No actionable issue remains in the recovery
logic.

The final full validation passed on the corrected evidence-linked head (7,286
passed, 10 skipped, 98.14% coverage against the 80% floor), including the
secret scan and SBOM gates.

## 2026-09-07 — Phase 2.1 bounded review

The changed length guard rejects incomplete identity-encoded bodies before
promotion and preserves the distinction between compressed wire length and
decoded body size. Expected length is bound to each HTTP attempt. Red tests,
boundary tests and three killed source mutants exercise both guard outcomes.
CAS/WARC hash and actual body linkage, partial disconnect, fsync/storage/time
failures and retained tombstone originals are verified with synthetic bytes.
No eligibility decision was added. Existing tests are mapped rather than
duplicated; runner resume/WARC gaps are explicitly characterization, not
positive acceptance. All focused tests, lint, format and types pass; critical
whole-module 100% and integrated checkpoints are not claimed. No additional
in-scope fix remains in this bounded change. See `bronze-ingestion-contracts.md`.

## PR #401 parser setup clarification — 2026-09-05 UTC

The reported external warm-up context was actually an empty inline context,
not a demonstrated SSRF path. Replaced the warm-up parse with explicit parser
plugin loading anyway, making every parse occur inside the external-I/O guard.
All 47 metadata tests and focused lint/format/types passed afterward. The
initial full harness passed on `fc672e0b`; exact clarified-head full/hosted
validation is still pending. No production behavior or rights state changed.

## Offline RDF interpretation review — 2026-09-05 UTC

The prior JSON-shape checks did not independently expand predicates, check RDF
object kinds or exercise the typed literal mapping. Added a development-only
RDFLib lane rather than a bespoke partial JSON-LD parser. DCAT fixtures require
exact triple counts, separate recordset/distribution nodes, registered media-type
resources, non-negative integer byte sizes and binary SHA256 values matching
retained fixture bytes. PROV fixtures require every entity and exact directed
derivation pair. External HTTP and file contexts fail under the parser's scoped
I/O guard; the guard is not represented as an operating-system sandbox.

Forty-seven combined tests and targeted static checks pass. Source-only runtime
helpers remain unchanged, and no RDF store/index/service or publication authority
is introduced. The pinned parser's internal ConjunctiveGraph deprecation warnings
remain visible. Supply-chain gates passed; full/hosted gates are pending. No full DCAT
application-profile, rights or track acceptance is claimed.

## DCAT media type and interoperable fixity — 2026-09-05 UTC

Primary-source review verified Parquet's IANA registration and DCAT's preference
for `dcat:mediaType` when a registered type exists. The draft used only a text
format label, and its exact payload digests were available only through the
companion inventory. Three red tests reproduced the missing standardized media
type/checksum graph entries before correction. The graph now carries the IANA
IRI and typed SPDX SHA256 payload checksum; tests calculate the expected digest
from actual fixture bytes, independently of the returned verification metadata.

All 23 focused tests pass in 22.85 seconds with 100% line/branch coverage;
Ruff and formatting pass. Cold mutation, typing and retained replay are being
repeated for this graph revision. The live full run on `c481b42d` was kept in a
separate unchanged worktree and cannot validate this later correction. No
rights, availability, full RDF processor or publication claim is added.

Corrected typing passes with zero errors/warnings/notes. Cold mutation killed
10/10 mutants with no survivors, errors, timeouts, pardons or cache hits in
146.26 seconds. Retained replay again produced six dataset/distribution pairs
and verified all 20 inputs unchanged. The new graph hash is recorded in the
run log; its verification-inventory hash is unchanged. The bounded correction
has no further focused finding; full/hosted assurance remains outstanding.

## Verified DCAT implementation review — 2026-09-05 UTC

Reviewed M-14/AC-14 mapping against DCAT3 Distribution and byte-size semantics.
Recordsets and package versions are distinct datasets; their local Parquet
representations have separate identities. Identity derives from validated
product metadata, while exact source/package/payload pins and physical schemas
remain in the accompanying verified inventory. No made-up publisher, location,
licence, date or full conformance claim is emitted. The graph uses only inline
namespace declarations and the existing read-only verifier, without a new
dependency or changes to the general Gold exporter.

Negative review cases ensure a new marker/payload hash cannot excuse changed
canonical values, schema metadata or rights claims. All 23 focused tests and
targeted static checks pass. Mutation, full assurance and hosted delivery remain
pending; the plan task and whole metadata phase remain in progress. The stale
standards route now distinguishes the already implemented assertion-only PROV
helper from this verified-snapshot DCAT work.

Follow-up validation killed all 10 cold mutants and passed a read-only replay
on the two independently pinned retained historical packages. The replay
returned six separate recordsets and unchanged input hashes in both input
orders. Full/hosted assurance still remains outstanding; there is no source
rights promotion or permanent metadata-output retention in this replay.

## Validation fixture isolation — 2026-09-05 UTC

The local two-worker run on `68c952de` failed two existing property deadlines
(4,743 passed, two failed). Both properties recreate invariant source fixtures
inside the timed body. The correction constructs those fixtures once, outside
nested generated examples. It keeps archive unpack/reorder/root checks timed,
preserves all union assertions and strategies, and gives each algebra example
fresh records and checkpoint state. No deadline or production behavior changed.
The 162-test register/parent-state/merge selection passes; Conductor validates
92 tracks and targeted typing, Ruff and formatting pass. The first formatting
check found a long nested decorator; formatting corrected it. Full local and
hosted validation of the correction remain pending. Neither historical coverage
nor operational/rights/publication acceptance is promoted by this test fix.

## Historical register stable-identity correction — 2026-09-05 UTC

M-02 review found that the new rows had locators but lacked explicit stable
source IDs. Added namespace-qualified URL-digest IDs for all 15 observations.
The regression failed on missing `source_id`, then passed with uniqueness and
derivation checks. These are not payload hashes; every byte count, fixity and
rights gate remains unchanged. Corrected wording to distinguish web-reader
observation from local payload retention. Ruff and formatting pass. The change
was isolated from the live full-validation tree; integration and assurance
remain pending before the review task can be marked complete.

## Historical source register — 2026-09-05 UTC

Reviewed all six locators against their official linked edition pages and the
30-year denominator against Treasury's historical index. No workbook digest,
byte count, licence approval, capture or completeness state is inferred from
a filename, page label, printed size, or web-reader error. All editions remain
pending full enumeration, including 2024's separate forecast-file discovery.
Existing donor objects, census observations and published candidates are
unchanged. The executable register test guards these boundaries; full local
and hosted assurance remain pending. No phase or track closeout is claimed.

## Health domain registration reconciliation — 2026-09-04 UTC

The immutable Arrow registry exposes the dedicated `health_appropriations`
domain and all eight versioned recordset shapes without modifying any other
domain contract. The combined Arrow/JSON schema suites pass 85 tests, so the
separate domain-registration task is evidence-complete. The broader fixture
task remains open: these contracts are explicitly structural-only and do not
yet prove cross-row stable-ID uniqueness, period compatibility, null-reason
consistency, or lineage closure.

## Preservation acceptance reconciliation — 2026-09-04 UTC

- Reconciled five stale plan boxes against retained evidence without promoting
  rights, semantic, publication, or historical-coverage claims. The workbook
  fixture umbrella is supported by completed member-level, formula, hidden
  content, macro, external-link, unsupported-part, and bounded-scan contracts.
- The source census contains 141 unique records with exactly one disposition:
  73 captured resources and 68 reason-coded out-of-scope records. The
  independent preservation audit rehashed all 73 CAS objects and their 73 WARC
  payloads with no missing or mismatched object.
- The retained checkpoint also records donor reconstruction, controlled
  interruption/resume and restriction paths, focused/property/mutation checks,
  and an exit-zero full harness. These marks describe the observed bounded
  source set only; new editions, rights decisions, and publication remain open.
- The earlier `health-survey-assessment.md` already completed the plan's
  non-blocking evaluation task: it records the analytical question, temporal
  and geography boundaries, rights observations, and the still-unmet export
  and dictionary gate. Marking that evaluation complete does not authorize or
  claim survey acquisition or integration.

## Optional graph/vector evaluation — 2026-09-04 UTC

The decision is consistent with C-01/C-02 and W-07. Existing repository search
code demonstrates a generic deterministic projection, but the health track has
no measured health-specific retrieval use case and no pinned external model,
quality threshold, or drift receipt. Deferral avoids making optional derived
state authoritative and introduces no dependency, payload, publication, or
rights change. Reopening requires a scoped query set and reproducibility
contract; no code finding is created by this evaluation.

## Phase 1 disposition reconciliation — 2026-09-04 UTC

The existing final census and donor structural evidence satisfy the bounded
accounting task: 141 unique source records have one explicit terminal
disposition and no unresolved/retryable state; all donor binaries and modeled
data areas have inventory evidence. The review preserves the documented scope
gap: this does not assert all historical annual Budget/forecast editions were
  enumerated or that every captured source is rights-cleared for republication.

## Bronze tracked-byte boundary — 2026-09-04 UTC

The hash comparison covers every tracked regular file, not only extension-based
candidates. None matches the 73 captured source-object hashes and none exceeds
10 MiB. This supports the repository storage boundary without claiming that
external CAS/WARC custody, rights eligibility, or publication is complete.

## Forecast explicit preflight — 2026-08-31 UTC

Independent source/test review found no actionable issue. The explicit dry
path has source-validation-only scope, never Arrow/package-writer execution,
and retains rejected/partial status. Strict booleans prevent truthy write-mode
ambiguity. All four prior written packages are byte-identical against a
pre-change baseline. Combined 92 tests/100% critical coverage and 66/66 cold
unfiltered mutants pass. Native and hosted delivery remain pending; see
[forecast-preflight.md](forecast-preflight.md). No originals were changed.

## Quarterly GDP literal profile — 2026-08-31

- Source identity, actual-versus-adjusted and expenditure-versus-income
  selection are exact; quarterly observations are not annual denominators.
- Parent found locale-sensitive month expectations and missing literal token,
  scaling, format-attribute and century-range lineage. All corrected; locale
  regression and complete 900-entry closure pass. Currency remains null.
- 45 focused tests/100% critical coverage and cold 37/37 mutation pass. Original
  source and both independently reconciled deterministic pilots are retained.
  Native passed at `41e7717`: 2,790 tests/97.07% overall and all gates.
  Hosted checks and rights approval remain distinct. Exclusive retained Silver
  package readback is identical; source-specific output is not canonical.

## Additive inventory planner — 2026-08-31 UTC

Independent read-only source/test review found no actionable correctness issue
within the explicit reviewed-pin, fixity-and-metadata contract. Exact original
and recorded-rights joins, all-four profile matching, full file-set agreement,
and casefold/parent collisions are tested. Fixed profiles are immutable. No
source, candidate, rights-state or external publication write occurs.

Metadata overhead and a future root manifest are explicitly unplanned; empty
replacement/deletion lists apply only to payload inventory. Arbitrary malformed
nested typed inputs may raise KeyError/TypeError rather than a stable ValueError;
they cannot produce a success inventory. A future CLI must add a redacted error
boundary. Semantic package validation and publication approval remain separate.

Critical coverage/mutation passed, but native assurance remains incomplete:
exit 124 at 300 seconds with two unidentified failure markers and no final
summary. Preserve that receipt and require exact-head hosted adjudication;
do not mark the whole track or publication gate complete.
## Pharmac published-budget profile — 2026-08-31

- Parent independently reviewed the strict table/physical-cell profile, fiscal
  definition and reform/caption boundaries. One finding: missing normalized
  lineage serialized as string `None`; corrected to true schema null after
  a red regression, preserving the original `-` token and missing status.
- Exact decimals receive zero-padding only; published changes and rounded
  percentages are not recomputed. Original HTML and the separate missing,
  padding, header and policy-context evidence remain preserved.
- Source mutation, network execution, rights promotion and publication are
  absent. The parser is a bounded reviewed-profile reader, not a browser or
  general HTML display-truth evaluator. Other page content remains in Bronze.
- Focused 69 tests, 100% critical coverage and cold unfiltered 93/93 mutation
  kills pass. No survivors/timeouts/errors/pardons/cache hits. Native harness
  passed at `677326a` (2,459 tests, 97.01% overall coverage); hosted delivery
  remains pending. Four archive-copy files match both retained pilots exactly.

## Plot context-style regression — 2026-08-31 UTC

- Confirmed a visual identity defect on valid same-context years 2000, 2001
  and 2003: line segments correctly broke at the gap, but used different
  colors/markers while legend deduplication retained only the final style.
- Canonical full context now determines the style; segment coordinates stay
  separate. An insertion-order regression guards dictionary canonicalization.
- Distinct full contexts with colliding abbreviated labels receive explicit
  context ordinals, not one merged legend entry. Tests cover shared SHA-256
  prefixes and a context field absent from the display label. Exact contexts
  remain in `CONTRACTS.json`; no abbreviation becomes an identity key.
- The pure plot contract, Gold verification, numeric values, line connections,
  output names and preservation rules are unchanged. Existing retained images
  are not regenerated or overwritten by this correction.
- All 23 focused renderer tests pass with 100% line/branch coverage (132
  statements, 30 branches). Full and mutation assurance remain separate.
- Native strict typing exposed test assertion types that needed explicit
  NumPy array comparison and `Line2D` narrowing; those corrections pass
  targeted typing and all three regressions. The corrected full run passed
  all pre-test gates but timed out at 300 seconds with one unidentified failure
  marker and no final test/coverage summary. Mutation remains 42 kills and
  25 timeouts, not 67 kills. No unresolved code finding is asserted resolved
  by these incomplete whole-repository/mutation results; hosted checks remain
  necessary. The track and this review-fix task remain in progress.
## Budget assurance recovery — 2026-08-31 UTC

- Hosted exact-head assurance is independently observed successful and merged;
  it does not retroactively pass the earlier local 300-second timeout.
- The interrupted mutation report is retained as 83 execution errors, not
  successes. Recovery changed the isolated checkout/environment, not source,
  tests, mutation selection or deadlines. All 110 cold mutants are now killed.
- The two bounded Budget successor/reader tasks are complete. CLI/MCP exposure,
  broader fiscal/contextual coverage and publication remain separate tasks.

## Budget successor consumer — 2026-08-31 UTC

- Independent review reproduced and fixed non-integer manifest count acceptance.
  Additional boundary tests cover duplicate facts, contradictory dispositions,
  cross-record column drift, exact zero and preserved unsupported empty output.
- Fixture schemas come from producer output and literal headers, not consumer
  constants. Fresh per-test copies preserve mutation-test independence.
- Final focused coverage is 100% line/branch; retained live readback passes.
  Native full assurance remains incomplete after the bounded timeout; mutation
  and hosted evidence remain pending. No unsupported completion claim is made.
- Fiscal-year interpretation, unselected workbook areas, rights evaluation and
  publication remain explicit boundaries. A valid package is not a licence grant.

## Donor failure conformance — 2026-08-31 UTC

- Post-integration native harness also exits zero at `62dc6e4`: 1,911 tests
  collected, 96.75% overall coverage, all repository gates and 111-component
  SBOM. Health-domain production coverage remains 100% line/branch.

- The three pinned originals were compiled without import/execution; hash
  checks precede and follow compilation. The processor fails before runtime.
  No claim that it produced the SQLite oracle is made. Structured observation
  records diagnostics only, not source contents or external credentials.
- A synthetic duplicate-if regression preserves an uncompilable processor in
  CAS while receiver orchestration succeeds without selecting it. The test
  stubs adapters; real adapter fixtures and retained live raw-run readback
  supply distinct evidence, not an exaggerated end-to-end test claim.
- Donor risks map to named existing tests for positional drift, explicit
  rejection, nonpositive amounts, missing periods, denominator gates, type
  mixing and preserved failures. No unnecessary new runtime API or dependency.
- 253 focused tests pass. Final native harness for `4454d75` passes 1,907 tests,
  96.48% coverage, eight SQLite warnings, 40 schemas/30 documents, 70 tracks,
  9/9 parity, all native mutation/supply-chain gates and 111-component SBOM.
- Only the donor-intended four-profile pipeline and characterization tasks
  close. Broader raw areas, source expansion, resumability and publication
  remain open; exact-head hosted delivery is still a separate gate.

## Source-derived plots — 2026-08-31 UTC

- Read-only Gold consumer verifies pinned snapshots, all eight files, typed
  schemas, bounded materialization, counts and exact input-ID closure. This
  verifies a previously reviewed package, not arbitrary semantic truth, rights
  or process isolation. Originals and prior derivatives are never overwritten.
- Reviewed all six plot contracts against selected Gold inputs. Explicit
  year/type filters, decimal strings, units, lineage IDs, period partitions and
  reason-coded omissions remain inspectable. Sparse recent series use bars;
  no donor pixel-parity or unverified denominator claim is made.
- Visual review found compressed year gaps, crowded ticks, faint hatches and
  unlabelled small breakdown values. Tests and V2 exports resolve these issues;
  V1 is preserved. Three independent V2 builds match all eight files.
- Review found dry-run omitted rendering resource limits. Two red tests
  reproduced this; a shared checker now fails before output creation. Retained
  plot bytes are unchanged. All 48 focused tests pass at 100% critical coverage.
- Current mutation evidence kills 44 reader, 26 contract and 58 renderer
  mutants without survivors/timeouts/pardons. Renderer uses the explicitly
  documented unit/protocol selection, not the two slow full-PNG integrations;
  those still pass in normal focused/full tests. No timeout was relaxed.
- Fresh fixity checks pass for all 23 donor objects and the pinned donor
  manifest. No original, Hugging Face publication or donor retirement changed.
- Final full harness passes 1,906 tests at 96.48% coverage and all remaining
  gates (111-component SBOM); exact-head hosted delivery remains separate.

## Verified Gold persistence — 2026-08-30 UTC

- Review follow-up: source fields named `input_profile` are rejected before
  output creation, preventing overrides of the derived profile annotation
  without discarding original source metadata. Four red regression cases
  cover both selected profiles and null/string collisions; no preserved source
  or existing package is rewritten. Final focused validation follows the fix.

- Both persistence paths now use one bounded snapshot/lineage reader. Canonical
  identities are checked before downstream joins. Shared fixture refactoring
  retains existing negative and limit-boundary tests.
- Typed schemas preserve decimal amounts and unavailable metrics, including
  empty breakdown tables. Input sidecars and selected lineage support exact
  reconstruction; forecast-profile exclusions are explicit in the manifest.
- Existing/input-overlapping outputs fail closed; new partial bytes are retained
  with redacted errors. Default CLI is dry-run. No destructive helper from the
  older donor-derived Gold implementation is used.
- Verified three identical live builds and unchanged compatibility output.
  Legacy comparison distinguishes exact Budget sums from tolerance-based
  binary historical values and reason-coded growth differences.
- 42 focused tests, 100% critical coverage and 79/79 unfiltered mutation kills.
  Full harness and hosted delivery are not inferred from these focused checks.

## Pure source-derived analytics — 2026-08-30 UTC

- Final isolated full harness exited zero for `0bf14b0`: 1,656 tests,
  96.09% coverage, all repository gates and 110-component SBOM; eight
  existing SQLite resource warnings remain recorded.

- Reviewed all comparisons as source/vintage-specific. Historical joins are
  keyed to source object/vintage/year, then checked for exact period-end
  equality and a positive GDP denominator; Health accounting basis is checked
  only for growth, not incorrectly imposed on GDP.
- Decimal arithmetic uses an independent context and exact input sidecars;
  output rounding is explicit. No float or donor SQLite input is used.
  Missing/broken comparisons remain null. Original period-start and quality
  limitations are retained, not cleared by successful calculations.
- Budget sums keep amount types and source labels separate, retain all input
  IDs and contributing departments/portfolios/flags, and include negative
  corrections. The breakdown filter is explicitly 2025 Estimated Actual.
- 79 focused tests pass across both modules with 100% critical line/branch
  coverage, including 30 generated growth cases; 104/104 unfiltered mutants
  killed with no pardons. Pure functions do not verify file hashes or implement
  persistence, CLI, plots, denominator acquisition, rights or publication.

## Persistent raw compatibility export — 2026-08-30 UTC

- Final isolated full harness exited zero for functional commit `e91d24b`:
  1,577 tests, 96.05% coverage, all repository gates and 110-component SBOM.
  Eight existing SQLite resource warnings remain distinct from test failures.

- Verified snapshots bind parsed bytes to the pinned raw-run manifests, with
  row/byte limits before Parquet materialization. Duplicate identities, source
  context mismatch, orphan/missing/duplicate amount lineage and non-text source
  coordinates fail before output creation. Existing and input-overlapping
  destinations fail closed. File values use SQL bindings; identifiers are fixed.
- SQLite connections close explicitly. Test review narrowed the simulated
  integrity failure to the module's SQLite reference, avoiding mutation of
  coverage's shared SQLite connector. The first failed mutation run is excluded;
  the corrected unfiltered run killed all 52 mutants with no pardons.
- Twenty-eight focused tests pass at 100% critical line/branch coverage,
  including 30 generated exact-amount cases. Lint/types and 35 schemas/25 sample
  documents pass. Full isolated harness and hosted delivery remain separate.
- Two live four-file exports match byte for byte. All five donor schemas and
  312 SQLite rows are retained; 29 original historical Health observations are
  added. Exact source decimals and all 4,918 lineage rows remain in sidecars.
- No claim of donor row-order parity, parser isolation, partial-export resume,
  public update, rights clearance or full assimilation is made.

## Raw compatibility projection — 2026-08-30

- Pure projection validates unit/measure/profile contracts, integer bounds,
  source identity and decoded text. Canonical amounts are never replaced by
  float values; a distinct compatibility value carries a representation flag.
- All source context is retained, including annotations, basis and dates.
  Callers still must verify the enclosing raw run and retain field lineage.
- Live projection preserves all 341 facts. Fifteen decimal-to-binary flags
  are explicitly distinguished from one source/donor value discrepancy.
- Twenty-seven tests cover all critical lines/branches. Unfiltered mutation
  run kills all 35; the earlier filtered run's 14 survivors are retained in
  the run log rather than treated as final evidence. No export file is claimed.

## Typed workbook inspection — 2026-08-30

- Final full harness exits zero; all 40 focused unfiltered mutants are killed,
  no pardons. Hosted inspector delivery remains separately gated.
- One capped, hash-verified snapshot feeds structural inventory and preview
  parsing. No filesystem output, formula evaluation or canonical fact claim.
- Added aggregate cell and UTF-8 value-byte boundaries, including equality
  cases and Unicode. Listing-only mode returns no cell previews.
- Corrected the nonfinite test fixture after learning `NaN` was already
  rejected by the parser; `1e309` reproduced permissive non-standard JSON.
  Strict encoding now rejects it. Array/data-table formula tests reproduced
  object-representation output; decoded fields now survive deterministically.
- Unknown objects are rejected. Existing parser/package/traversal limits are
  reused, with no claim of process isolation or unrestricted format support.
- Twenty-two focused tests achieve 100% critical line/branch coverage, with
  generated dimensions and original-byte invariants. Live Budget inspection
  matches eight sheets and a 34-cell selected head; source fixity is unchanged.

## Read-only raw verification — 2026-08-30

- Inspection has a separate entrypoint and cannot invoke rebuild, extraction
  or receipt-writing functions. Missing output and store paths remain absent.
- The caller's exact run-manifest pin is checked before and after all source,
  context and derivative checks. Tests cover late pin changes, symlinks,
  malformed private plans and redaction before the MCP error boundary.
- CLI and MCP share verified receipts; both live interfaces validated the
  retained original-workbook run. No new source observation or publication is
  claimed by readback.
- Extracted complete-run validation into a shared helper. Sixty-three
  focused/interface tests achieve 100% critical coverage; all 82 explicitly
  unfiltered mutations were killed without pardons.

## Raw archival orchestration — 2026-08-30

- The default CLI path only preflights; writes require `--no-dry-run`. All
  four source objects are reverified before either a new build or complete
  reuse. The run plan pins manifest identity, profile context and observation.
- Existing directories are never overwritten. Reuse requires exact plan,
  complete stage contexts, expected file sets and hashes. Corrupt, symlinked,
  partial and extra-file cases fail closed. Bronze output paths are prohibited.
- Review identified duplicate JSON keys and unexpected adapter exception
  handling. Red tests reproduced both; unique-key parsing and a narrowly
  annotated redacted failure boundary now reject them without source-message
  leakage. Failure receipts never imply completion or trigger publication.
- Forty-one focused tests retain 100% critical line/branch coverage, including
  20 generated corruption examples. Live independent builds match all 18
  files, and current-code complete reuse reverified sources and outputs.
- This increment does not claim partial-stage resume, scheduling, MCP raw-run
  projection, full workbook coverage, new Gold analytics or changed HF bytes.

## Historical original-source extraction — 2026-08-30

- Exact OOXML decimals avoid binary-float/display rounding; source lexemes,
  formats, annotated years, footnotes and period/basis labels remain traceable.
  Year-end lineage links both contributing source cells. Annual starts and
  cross-basis comparability are not invented.
- Split selection, period state, numeric validation, record creation and
  reconciliation into bounded helpers after the initial complexity finding.
  The standard-library lexical reader has a narrowly justified S314 annotation:
  a custom TreeBuilder rejects DTDs, tested with UTF-16 input. Prior workbook
  inventory/loading remains subject to its existing non-sandbox limitations.
- The first mutation run selected an unrelated test for one surviving return.
  Explicitly disabling coverage filtering killed all 70 extractor mutations.
  The final combined run killed 99/99, with no pardons. No survivor was waived.
- Review added donor numeric range/precision rejection before computing deltas;
  the new tests failed twice as expected before the correction. The comparison
  preserves both observations and never silently changes a donor value.
- Live extraction recovers every source year without filtering to the lossy
  donor table. Seventy-six historical oracle values match exactly, 29 annotated
  years are source-only, and the 1976 decimal difference remains explicit.
  Rebuilt artifacts and originals were independently hash-checked.
- Publication, remaining data areas, domain-wide operational integration and
  analytical compatibility are not claimed by this bounded extraction increment.

## BEFU/HYEFU extraction — 2026-08-30

- Source-specific selection uses unique literal labels, verified units and
  contiguous year/type ranges. Shifted-layout fixtures pass; duplicate labels,
  missing units, year gaps/duplicates, reversed Actual/Forecast ordering,
  formulas and unlabelled summary values fail closed.
- Forecast labels are retained from source cells, not inferred from dates.
  Bare years do not justify fiscal endpoints. Rights remain unresolved until
  linked to approved per-resource evidence; parsing cannot approve publication.
- Six fields per fact have explicit cell lineage, including the shared label
  and unit cells. Nonempty unselected cells and selected blanks have explicit
  dispositions. Other sheets remain inventoried and excluded from this narrow
  summary extraction, not deleted or declared fully normalized.
- Shared workbook integrity helpers remove duplicate validation/writing code.
  The Budget fixture's four output files remain byte-identical across the
  refactor. Output names are validated, files are exclusively created and
  hashes are streamed. The manifest uses portable UTF-8/LF and is written last;
  incomplete directories are not a resumability or atomic-transaction claim.
- Review found that a basename-only guard would accept Windows device stems.
  Five new red contracts reproduced the gap. Exact reserved stems are now
  rejected, while ordinary near-matches remain valid. A collision fixture
  confirms a file appearing after directory reservation is not overwritten.
- All selected literal values reconcile with both ten-row donor oracles.
  Each source independently rebuilds to identical bytes with 60 lineage rows;
  no source bytes or published artifacts changed. Larger workbook areas and
  historical/contextual series remain pending, not covered by this parity claim.

## Raw Budget extraction and donor characterization — 2026-08-30

- Added a separate original-workbook path, not a replacement for the donor
  SQLite oracle. All original columns and input-row dispositions are retained;
  named selection permits column reordering but rejects missing/duplicate or
  non-text headers. Repeated business rows retain distinct source-row identity.
- Extraction uses one hash-verified, size-capped snapshot and existing workbook
  package/scan checks. Extensionless CAS inputs are supported. Openpyxl parsing
  is still not a resource-isolated sandbox; the scan cap follows package load.
- Formula/error Health rows and missing/invalid source values are rejected with
  reason codes. Fixed-decimal conversion neither rounds nor drops nonpositive
  amounts. Source year labels are not silently assigned fiscal dates.
- New output directories prevent overwriting source or prior derivatives. A
  manifest is written last; partial directories remain incomplete and are not
  resumable. Consumers must verify manifest hashes, not directory existence.
- Static donor characterization does not execute import-time side effects or
  pretend the broken processor generated the checked-in SQLite database.
  Broader replacement analytics and complete format support remain pending.
- No dependency, raw payload in Git, source rewrite, changed HF publication or
  donor-retirement operation is introduced. Rights remain explicitly unresolved
  in these new facts until joined to approved resource-level rights evidence.
- Forty-nine focused tests passed with 100% extractor line/branch coverage;
  73/73 unfiltered mutation tests were killed. Ruff and basedpyright passed.

## Workbook part contracts and continuation — 2026-08-30

- Fixed the false macro-part marker for `notvbaProject.bin`; exact basename
  matching retains case-insensitive compatibility. The marker is explicitly
  not VBA validation, an active-content detector or a safety verdict.
- Synthetic external references and opaque embedded parts remain byte-exact;
  tests block socket connection paths and verify neither target URLs nor opaque
  contents appear in inventory output. Fixtures contain no executable macros.
- Focused format coverage is 100% line/branch with 37 passing tests and 31/31
  unfiltered generated mutations killed. Static checks passed after fixture
  style fixes. Invalid overlapping coverage runs were recorded and discarded.
- Added a milestone route rooted in the existing plan. It identifies raw-source
  extraction separately from donor-SQLite parity and preserves all external
  publication/rights/retirement gates. The document activates no scheduler.

## Current-state reconciliation — 2026-08-30

- Resolved contradictory current-state claims in the track entry page using
  canonical metadata and existing preservation/publication receipts. Historical
  observations remain unchanged and explicitly dated; no byte audit is implied
  by the fresh public metadata readback.
- Added an offline contract tying status, key counts, publication identity and
  issue linkage to metadata while retaining incomplete-work and retirement
  boundaries. No production code or dependencies changed.
- Reopened parent #205 after live readback showed closure despite pending Must
  work. The hosted issue now agrees with the active registry and metadata.
- Format-support implementation remains pending; this correction satisfies
  traceability, not extraction completeness. No new publication is authorized.

## Rich workbook census — 2026-08-30

- Previous count keys remain available. Additive structural details identify
  table/merged ranges, grouped hidden-column spans, hidden rows, scoped names,
  formula/comment coordinates and every original ZIP part name.
- Formula/comment coordinates use one bounded traversal. No formula execution,
  comment text/author export, network request or original rewrite is introduced.
- Unknown package parts are surfaced but not claimed as interpreted. Cached
  values, defined-name expression interpretation and broader source promotion
  remain separate pending contracts. Historical manifests are not rewritten.
- Synthetic rich/empty-sheet fixtures verify deterministic repeated results,
  original byte identity, chart/table preservation and non-disclosure of
  comment content. Existing unsafe-path/duplicate/scan-limit tests remain active.
- General/Python style and M-07/S-03 preservation boundaries were reviewed.
  No new dependency, publication or donor-retirement action is part of this slice.
- Final assurance passed: 1,239 tests at 95.59% overall coverage, 100%
  format-module line/branch coverage and 23/23 unfiltered mutants killed.
  The interrupted baseline and its native-Python SBOM retry are recorded
  separately from the successful final full-harness exit.

## Workbook safety prerequisite — 2026-08-30

- Replaced host-dependent path interpretation with explicit ZIP member rules;
  traversal, absolute/drive/backslash paths and ambiguous path segments fail
  identically across platforms. Duplicate exact member names fail before parsing.
- Added a cumulative 2,000,000-cell rectangular scan budget before `iter_rows`.
  Exact-boundary and multi-sheet fixtures prevent off-by-one and per-sheet
  bypasses. Twenty generated examples cover sparse extents and budget boundaries.
- Originals are never rewritten; both successful and rejected synthetic
  packages retain byte identity. This gate limits the inventory traversal,
  not all parser allocation: openpyxl loading still precedes this cell gate.
  Existing ZIP member/expanded-byte limits remain in force. This is not a
  complete sandbox, richer workbook census, or scheduled-operation completion.
- Focused format-module coverage is 100% line/branch; 22/22 generated mutants
  were killed. Ruff import-placement and raw-regex findings were corrected.
- Applicable local Python/general style and medallion requirements were
  reviewed; no new dependency, source payload, external publication or donor
  retirement was introduced. Broader Phase 1.3 tasks remain pending.

## Review fix — 2026-08-30

The batch-eligibility invariant inherited Hypothesis's 200 ms deadline and
flaked once under parallel worker startup despite replaying in 0.02 ms. The
test performs no bounded performance contract. Commit `b2bf7b7` disables only
that wall-clock deadline; generated examples, the eligibility assertion and
parallel execution remain intact. Focused pytest, Ruff and basedpyright pass.

## Operational status review — 2026-08-30

- The new surface is read-only and idempotent; it exposes no credentials,
  signed URLs, source payloads, mutation, publication or retirement authority.
- Missing state is distinct from partial state, and malformed or contract-
  invalid manifests fail closed rather than being treated as ready.
- The archive root is caller-configurable and no workstation path is embedded
  in source. Live validation found and resolved an ambiguous donor-manifest
  selection before commit.
- The bounded slice does not claim the broader Phase 8 capture, normalize,
  analyze, rebuild, scheduling, cancellation or retry contracts are complete.

## Initialization review — 2026-08-29

### Scope and requirements

- The specification covers the complete 23-file donor tree, not only its eight
  obvious source files or its working SQLite rows.
- The plan explicitly carries originals through Bronze and treats every later
  layer as a separately identified, reconstructable derivative.
- Donor functionality is represented by inspection, normalization, SQLite
  compatibility, four analysis families and all six plots. The donor compile
  defect is a test target, not silently accepted code.
- Direct official expansion includes longitudinal Vote Health/Budget,
  BEFU/HYEFU, fiscal series, Ministry Vote Health and Pharmac CPB sources.
  Indirect context is limited to official measures needed for defensible
  real/per-capita/share calculations; aggregate Health Survey linkage is
  conditional and microdata is excluded.

### Architecture and medallion integrity

- Bronze is authoritative for byte preservation, observations and rights;
  Silver has a dedicated binary-aware, multi-recordset domain and field/cell
  lineage; Gold owns analytics/compatibility outputs; Platinum owns metadata,
  federation and release candidates.
- Vintages, source labels, classifications, units, base periods and
  denominators are explicit. The design does not overwrite revisions or splice
  unlike series silently.
- CAS, WARC, manifests, multi-hash identity, heartbeats, reconstruction,
  schema fingerprints, data-quality reports and fail-closed promotion reuse or
  extend existing medallion features rather than creating a donor sidecar.
- Optional graph/vector outputs are rebuildable discovery projections and not
  preservation truth.

### Rights, security and external state

- The donor Apache-2.0 code licence is not misrepresented as source-data
  redistribution authority.
- New dependency adoption, resource rights, credentials, exact HF candidate
  approval, upload, remote verification, collection mutation, donor retirement
  and Zenodo release remain explicit gates.
- No raw payload, credential, signed URL, personal data or restricted content
  is introduced by the track scaffold.

### Corrections incorporated during planning

- Corrected the initial temptation to treat the donor SQLite database as
  canonical: it is now a preserved parity oracle and generated compatibility
  product.
- Corrected reliance on generic health/Treasury text normalizers: the plan now
  requires a dedicated workbook-aware health-appropriations domain.
- Corrected blanket publication metadata risk: Platinum licensing is
  per-resource and fail-closed.
- Added zero-loss coverage for workbook structures that may not be extractable
  initially, plus reason-coded exclusions.
- Added direct successor data and contextual denominator series, CPB, source
  health/drift, bitemporal vintages, federation, clean-room recovery and
  independently verified HF collection membership.
- Placed `openpyxl` and Matplotlib behind an explicit stack/dependency
  evaluation because bundled workbook tooling was unavailable during planning.
- Resolved one staged secret-scanner false positive caused by a validation
  receipt field name. The field was made less ambiguous and the scanner passed
  without an allowlist or suppression.

## Open findings and limitations

- Exact live source resource URLs, bytes, availability and rights are not yet
  frozen. Phase 1 owns the cutoff-bound census.
- Workbook sheet/table/range completeness has not yet been measured with an
  approved parser. No extraction-completeness claim is made.
- The proposed Hugging Face dataset configuration and rights-eligible payload
  cannot be fixed before schema, source census and rights work complete.
- A parent GitHub issue has not been created because track initialization did
  not mutate hosted issue state.
- Pre- and post-scaffold full validation passed locally. Hosted CI and every
  implementation/publication gate remain separate and pending.

No unresolved critical finding prevents creation of the planning track. These
open items are deliberate implementation or external-gate work and must not be
reported as complete.

## Phase 0 implementation review — 2026-08-29

- Pinned donor identity, inventory and archive digest were reproduced without
  drift; the archive contract explicitly excludes a path prefix.
- Landing-page HTTP 403 responses are recorded as client observations and are
  not misclassified as unavailable source resources.
- Hugging Face absence, collection membership, GitHub issue hierarchy and
  local validation are stated as distinct observations.
- No credential, signed URL, restricted payload or unsupported completion
  claim was found. No unresolved Phase 0 finding remains.

## Formula cache characterization review — 2026-08-30

- Commit `f73d678` adds presence/type observations without exporting contents,
  evaluating formulas or asserting cache freshness. Zero and false are not
  conflated with absent caches; absent and empty caches intentionally share a
  state. Both workbook views close on inventory completion or failure.
- The second view uses the existing approved parser and only looks up formula
  coordinates. Existing preflight/traversal limits remain; parser allocation
  itself is not newly bounded. Input is assumed to be immutable Bronze content.
- Thirty-two focused tests passed with 100% format-module line/branch coverage;
  all 30 unfiltered generated mutations were killed. Ruff and basedpyright passed.
- No original files or hosted datasets were changed. This does not complete
  the broader format-support contract, successor normalization or donor
  retirement. No unresolved finding blocks this bounded inventory change.

## 2026-08-31 — Standalone Budget operational receipt review

- The operational wrapper delegates all content checks to the existing pinned
  reader, emits no records, and never creates missing state. Both success and
  failure CLI/MCP contracts are tested through the public MCP handshake.
- Fixed metadata/context bounds, strict count schemas and rights/publication
  non-promotion prevent the receipt from claiming broader source acceptance.
- Focused coverage is 100%; independent parent review found no implementation
  finding. Native timing failures and their isolated passing reruns remain
  explicitly recorded; complete hosted assurance is still required.

## 2026-08-31 — Embedded-notice observation review

- Exact three-source allowlist, pre-parse snapshot hash, fixed cell/text digests,
  bounded ZIP/XML reads and redacted errors restrict this to reviewed evidence.
- Independent review found no actionable production issue. Suggested immutable
  profile, exact-coordinate, part-boundary and interrupt tests were included.
- No source text, historical external-link strings, rights grant or publication
  operation is exposed. Existing defusedxml is reused without dependency changes.
- Focused and mutation gates pass. The native CPI timing failure and isolated
  passing diagnostic remain visible; complete local assurance is not claimed.

## 2026-08-31 — Exclusive local additive staging review

- Independent parent and sibling reviews found no substantive copy/path/state
  defect within the explicitly reviewed-root, copy-integrity-only contract.
- Parent review identified inherited non-finite JSON acceptance in extra rights
  metadata. Seven red cases reproduced it; finite parsing and strict staging
  encoding now reject it without interpreting rights or changing original bytes.
- Full base history includes the original manifest/card; no active publication
  manifest, inherited approval or current publication claim is emitted.
- Exclusivity, copy fixity, full readback and redacted failure retention have
  focused negative coverage. Supplied forbidden roots are caller responsibility,
  not automatic publisher-config discovery or arbitrary uploader prevention.
- Refreshed combined evidence is 139 tests, 100% critical line/branch coverage,
  and 120/120 cold unfiltered mutant kills. Two final-source live builds match
  each other and the retained earlier pilot; native delivery evidence follows
  in [additive staging](./additive-staging.md).

## 2026-08-31 — Structural record-set review

Review is bounded to the additive eight-shape registry. It grants no
semantic projection, rights or full M-05 completion. Self-review caught and
corrected Parquet nested-list naming drift and rejected a Decimal256 carrier
unsupported by the locked DuckDB runtime. Wider original values remain
preserved; future projections must fail exactly rather than round them.
Independent read-only review found no actionable production issue and
requested full field type/nullability tests; those now pass together with
all 30 cold mutants. Native and hosted assurance remain distinct gates.

## 2026-08-31 — JSON row-shape review

The fresh descriptors enforce structural columns, constants, nullability and
exact fixed-point transport bounds. Deep-copy isolation and unknown-type
failure prevent mutable shared descriptors or binary/text fallback. Format
validation explicitly requires the caller's checker. Two independent reviews
found no actionable finding within this structural scope. All 51 tests and
two cold source mutants pass; ten separately seeded descriptor counterexamples
are not counted as production mutants. Native assurance passed at `d71d431`.
No identity, rights, temporal alignment, source projection or lineage semantic
claim is made. General/Python style and the repository formatter/type checker
pass; no platform-specific application guide is selected for this pure module.
## 2026-08-31 — Historical snapshot boundary review

The reader attests byte snapshots, exact physical source-specific schemas and
manifest counts, not cell semantics or canonical promotion. Source execution,
network and output writes are absent. Strict JSON rejects duplicate/nonfinite
values; direct symlinks, wrong pins, extras and corrupt Parquet fail closed.
All hashes precede decoding and aggregate caps bound the admitted payloads.
Source parent directories remain caller-trusted, explicitly not a sandbox.
Independent review found no actionable issue in that scope and suggested tests
for exact resource boundaries and hash-before-decode ordering; both now pass.
The Parquet list-name mismatch was corrected without relaxing metadata checks.
Native and hosted evidence remain separate from focused/mutation results.
## 2026-08-31 — Pure historical projection review

Scope is reviewed historical Health/GDP fact and lineage projection only, with
caller-supplied inputs and no fixity/publication claim. Independent review found
two integrity gaps: contradictory disposition cell literals were not joined to
lineage, and six unused historical source fields could disappear if non-null.
Nine negative tests reproduced both findings before the guards were added.
The source number format remains an explicit attribute exception, and both
retained snapshots pass exact JSON-string cell joins without numeric coercion.
Read-only re-review reports both findings resolved and no additional finding.
The original input package remains required for retained-only information.
See `historical-projection.md` for mapping, red-phase evidence and limits.

## Budget classification occurrence projection

The pure source-label projection passed independent read-only review, 42 focused
tests with 100% critical line/branch coverage and 29/29 cold mutant kills.
Two verified retained Budget packages yield 400 unmapped occurrence dimensions
and full 6800-row lineage accounting without input mutation. Exact Parquet
round-trip and source-object identity boundary tests pass. No authoritative
identifier, valid-time interval, crosswalk or rights promotion is invented.

Required native validation at `b651907` passed all 3014 tests (8 existing resource
warnings), 97.12% coverage and all subsequent gates. Two owned timestamp-only
fixture changes were restored after exit. Source and tests remain unchanged;
hosted delivery is pending. See [full receipt](./budget-classification.md).
## 2026-08-31 — Exclusive canonical export review

Independent read-only review of the complete exporter and tests found no
actionable issue after the dry-run refinement. Both modes now serialize and
budget the same complete marker before reservation; only dry-run labels output
hashes planned. Expected failures cannot write into unowned/raced directories.
Partial data and partial markers remain intact; a marker filename alone is not
validity evidence. Exact bytes/schema readback and file membership precede
completion. Caller parent-directory trust, source-package retention and no
publication/rights promotion remain explicit. No generic filesystem sandbox or
global semantic/canonical-registry completion is claimed.

## Exclusive local classification export

The source-only occurrence projection now has an exclusive local persistence
wrapper. Independent review findings were reproduced by red tests and resolved;
final re-review found no actionable issue in its trusted-parent scope.54tests
pass at100%critical coverage, and44/44cold mutants were killed without pardons
or cached results. Nativef46e4b6 passed3426tests and every subsequent gate.

Two builds per retained Budget vintage independently reconcile all five files,
400dimensions and6800lineage-accounting rows, with originals/input packages
unchanged. The local marker is not a publication manifest and can survive a
failed readback; only full validation establishes local completion. Errors are
redacted and partial evidence retained. See [receipt](./classification-export.md)
for exact hashes, failure observations and the append-only timestamp correction.
## Original-to-products replay — 2026-08-31 UTC

Two fresh output trees independently match all 38 files. Investigated the
failed older compatibility-byte comparison instead of normalizing its header:
SQLite versions differ, only offsets 98/99 change, schemas/341 rows and all
other payloads match. Preserve both versions and exact manifests. No broad
AC-12, source-area, rights or publication conclusion follows.

Forecast preflight follow-up: full native harness passed at `8ace367` with
3,414 tests and all gates. This supersedes the earlier native-pending status
only; hosted delivery and full source/rights/recovery phases remain separate.
## Detected structural accounting review — 2026-08-31

Scope remains detected structural units only, never complete normalization.
Review identified names-only structural joins and insufficient range bounds;
11 red cases preceded fixes for shared-attribute/rich-range agreement,
ordered Excel/sheet boundaries and coordinate-only forecast selection retention.
Independent re-review found no further actionable finding. Mappings remain
assertion-only, adapter exclusions never imply global scope, PDF page counts
never manufacture table/page identities, and partial selections leave unresolved
whole-unit coverage. Final assurance: 107 focused tests/100% critical coverage,
144 cold mutant kills, full native 3,531-test pass. Hosted delivery is separate.

## 2026-08-31 — Read-only resume planner review

Independent parent and sibling review identified transformation/profile and
count consistency plus uncapped directory/Parquet metadata reads. All were
reproduced by red tests before correction; final review found no further
issue in the reviewed-root fixity/transport-only scope. Expected stage diagnostics
are bounded machine reasons, while global low-level input exceptions are not
claimed as a CLI redaction boundary. No attempt is copied, repaired or executed.
102 tests/100% critical coverage, 95/95 cold mutants and the full 3,797-test native
harness passed. Exact-head hosted delivery remains a separate gate.

## 2026-08-31: Budget appropriation projection review

Parent and sibling independently reviewed exact Decimal copying, contextual IDs,
all-field retention and lineage closure. Provenance ambiguity findings were
reproduced by red tests before adding inherited-field receipts and explicit
unmapped-classification/inherited-unit/currency-unknown flags. Final frozen
source/test review had no remaining finding. Critical 100%, 28/28 cold mutants,
full 3,955-test native and the pinned in-memory 400-fact pilot passed; hosted
exact-head delivery is separate. See [scope and receipts](./budget-canonical-projection.md).

## 2026-08-31 — Bounded PROV entity projection review

Two independent reviews found no actionable issue in the entity/derivation-only
projection. Typed identifiers, edge direction/closure, deterministic digests,
fresh outputs and unchanged full inventory are tested. No activity, actor,
time, licence or verification claim is manufactured. Initial missing-module red
preceded implementation; 71 combined tests/100% critical coverage and six cold
mutant kills passed. Full standards validation and AC-14 remain open.

Native assurance subsequently passed all gates at `1a58841`; the reviewed reader
stack was merged ordinarily without source changes. 141 integration tests passed;
both conflict-side documentation entries and all 119 incoming ledger lines were
retained. Hosted delivery is still separate from this local assurance receipt.

## 2026-08-31: Budget reader metadata bounds review

Parent and sibling independently reviewed the exact source/test delta and found
no remaining actionable issue. Five-entry directory enumeration rejects extras
without exhausting arbitrary directories; explicit Thrift limits precede parser
metadata/materialization. Existing byte/row/expanded guards and propagated
OSError boundary remain. This is not hostile-Parquet sandboxing. All 63 critical
tests, 112 cold mutants and the full 4,239-test native passed; hosted exact-head remains
separate. See [scope and evidence](./budget-reader-bounds.md).
# Implementation continuation review — 2026-09-03

Repository-owned validation is current and passing on Python 3.14.6. Existing
inventory, workbook-safety, formula-cache, macro/embedded-part, and bounded
format contracts are present and covered by the test suite. The track is not
archive-eligible: source enumeration and national derived-series work remain
incomplete, and public publication, rights/privacy review, external payload
access, and hosted evidence are still gated. No external repository outside
`edithatogo` was contacted or mutated.
# Conductor review — 2026-09-03

Review outcome: repository-owned implementation and Python 3.14 validation are
current; no high-confidence code defect was identified in this review slice.
The track remains incomplete and cannot be archived. Pending plan tasks cover
official source enumeration, derived-series and Gold/Platinum construction,
rights/privacy qualification, public Hugging Face delivery/readback, hosted
recovery and operational evidence, and final release acceptance. These remain
factual or external gates. No unsupported completion or publication claim is
made.

## 2026-09-05 — Donor retirement reconciliation

The legacy donor repository was archived after the user-authorized retirement
action. The bounded `donor_retirement_github_observation` receipt in
`evidence.jsonl` preserves the observed response fields and
`response_sha256=6c1e320396c23b0868dcef7fa345a331f8d1f033b82e0cfc6896fe8709e3dd44`;
the response records `isArchived=true` and `archivedAt=2026-09-05T07:53:19Z` for
`edithatogo/nz_health_appropriations`. The donor remains recoverable by its owner;
no files were deleted, and the retained raw/original evidence and provenance
boundary are unchanged. The Conductor `donor-retirement` gate is therefore
reconciled to `satisfied` (explicitly out of this track's implementation scope).
This observation does not close the track: official-source enumeration,
derived-series and Gold/Platinum construction, rights/privacy qualification,
hosted recovery/operational evidence, and final release acceptance remain
pending as documented in `remaining-acceptance.md`.

## 2026-09-03: Exclusive Budget appropriation exporter review

Independent review found four actionable issues in the initial reconstruction:
output-root pathname replacement, post-materialization resource checks, missing
adversarial/exact-parity cases, and failure-marker exception precedence. The
fix anchors I/O to the exclusively opened directory descriptor and verifies
the public output pathname still names that inode at every boundary, adds bounded
incremental serialization and running aggregate admission, covers source-order,
Decimal/context, equality/over-boundary, extra-entry, root-replacement,
readback and double-interrupt cases, and ensures the saved original exception
wins. Post-fix review found no unresolved issue in this bounded local-only
scope. Final focused coverage, 63 cold mutants and the full native harness pass.

The subsequent exact-head retained two-vintage replay passed independently of
the focused fixtures: four fresh packages, exact six-file closure, dry/write
hash parity, paired-build byte identity, public projector/readback equality,
400 facts, 4,400 canonical lineage records and complete 6,800-entry original
lineage accounting. Ten retained input files were byte-unchanged. This evidence
remains local-only and does not alter the rights or publication assessment.

Hosted macOS subsequently exposed an order-dependent test-only assertion: the
caller-local Decimal context was correctly unchanged, but the test additionally
assumed an unrelated process-global `Inexact` flag began false. The failed log
was retained and classified as an assertion failure. Removing only that global
precondition preserves the exact local flags/traps/precision and Decimal(38,18)
checks without changing production code or weakening a repository gate.
The refreshed 63-mutant cold lane and 4,626-test native harness both passed;
the correction is locally closed subject to fresh exact-head hosted checks.

## 2026-09-03: Windows persistence portability review

Hosted Windows exposed a deterministic platform mismatch in the POSIX-only
directory-fd reservation path. The scoped correction preserves descriptor-
relative no-follow I/O on POSIX and uses repeated inode and reparse-point checks
under the existing trusted-parent contract where directory fds are unavailable.
It explicitly does not claim hostile-filesystem transactional equivalence.
Adversarial tests cover junction/symlink rejection and modeled ordinary root
replacement at reservation, write and listing boundaries. Focused line/branch
coverage is 100%; all 83 cold mutants and the 4,631-test native harness pass.
Fresh exact-head hosted validation remains pending.

The next Windows run exposed short-write semantics rather than another path-
identity defect. The final writer loops over a bounded memoryview, rejects no-
progress writes, and retains the existing size and identity checks. POSIX-only
fault injection is capability-scoped without weakening any fallback test. The
focused, 88-mutant cold and 4,632-test native lanes pass; hosted exact-head
validation remains separate.

Explicit capability-safe binary flags on Windows complete the fallback
descriptor correction. Focused, cold mutation and native validation pass;
fresh exact-head hosted validation remains required.

The last Windows failure was isolated to synthetic test setup; all production
tests passed. The capability-aware correction is test-only, and focused, cold
mutation and full native validation pass.

# 2026-09-03 historical canonical consumer checkpoint

Reviewed `historical_consumer.py`, its adversarial tests and the paired track
records against M-07, M-09, M-10 and M-18. Exact canonical schema/value/order
and receipt checks, public analysis semantics, reversible accounting, resource
bounds, Decimal context isolation and interruption behavior are covered. No
secret, personal data, filesystem mutation, network action, new dependency or
unsupported rights/publication claim was introduced. No actionable focused
finding remains. Self-review corrected the parent receipt to match the existing
exporter's exact newline-terminated canonical bytes and applied the declared
100,000-row / 64-MiB bound to all three raw and all three canonical tables. The
fresh 51-mutant cold gate and full native harness pass. Hosted delivery remains
separate evidence, not implied completion.

## 2026-09-05 — Exact normalization prerequisite review

Reviewed new source/tests plus track diff against M-05/M-06/M-18 and
AC-05/AC-16. Existing JSON and Arrow registries remain byte-unchanged. Exact
coefficient arithmetic avoids Decimal-context rounding; microsecond admission
prevents timestamp truncation; input dictionaries and list order are preserved.
All eight synthetic row sets round-trip through Parquet deterministically.
Invalid row errors contain a fixed reason only. No source file, remote system,
rights decision or publication path is accessed by the API.

Review boundary: local ID uniqueness is not stable-ID derivation; null/date/
precision consistency is not source-level semantic validation. Unit inference,
classification approval, formula freshness, source fixity, input file bounds
and lineage closure remain with separately tested callers. Main's pending
fixture work is preserved and its conversion/precision follow-up is documented.
No selected platform-guide manifest was found; platform-specific guides are
not applicable to this pure Python/Arrow increment. Shared registry edits are
excluded by explicit user ownership instructions, and its in-progress health
entry remains consistent. Whole Phase 3 completion is not claimed.

Final focused review: 117 tests, 100% new-module coverage and 35/35 cold mutants
pass. All post-test assurance stages pass. No actionable in-scope finding
remains. The original full-suite timing failures and interrupted retry remain
in the receipt; combined full checks are explicitly assigned to the parent by
the user, without suppressing or editing the unrelated failing tests.

## 2026-09-05 — Admission/readback negative-fixture review

Reviewed JSON bytes, typed Arrow/Parquet readback, metadata, nullability,
precision, time and resource-bound failures. Exact schema equality does not
substitute for row checks; unknown offsets and out-of-range UTC dates fail
before a table is emitted. Binary inputs, duplicate members and invalid UTF-8
receive fixed diagnostics. No public schema or source adapter is promoted.

The existing source-profile negatives cover layouts, units, periods, lineage,
formula/cache distinction and unsupported classification labels; their bounded
scope is recorded instead of asserting universal source qualification. The
original positive-fixture task and Phase 3 checkpoint stay pending. Final
focused and cold mutation gates pass; no in-scope finding remains. Parent owns
combined full validation. Global registry and main fixture files are unchanged.

## 2026-09-05 — SQLite structural adapter review

Verified literal path encoding keeps `mode=ro` outside URI fragments and table
names are identifiers rather than SQL syntax. The observed alias creation was
confined to synthetic red tests. Successful tests prove no missing file is
created, actual connections reject writes and close, and stable source bytes
and directory contents survive repeated inventory. Source schema text and row
counts are unchanged. The scoped spy avoids coverage-tool interception.

The complete formats module reaches 100% line/branch coverage and all 35 cold
mutants are killed. This does not grant snapshot, WAL sidecar, hostile database,
row normalization or donor parity guarantees; those remain explicit future
contracts. No high-confidence in-scope finding remains. No full harness ran.

## 2026-09-07 — Eight-recordset fixture review

Reviewed new fixture/test and all track edits against the original broad task,
M-05/M-06/M-18 and AC-05/AC-16. Independent field values and typed oracles avoid
schema-derived tautologies. Negative cases reach existing normalization and
readback; semantic gap characterization explicitly prevents completeness claims.
Corrected four raw-regex lint findings. Focused tests/lint/format/types pass.
The [full acceptance matrix](./eight-recordset-fixture-acceptance.md) records
unmet source identity, units/time, rights and Bronze lineage requirements.
No source/global registry/dirty checkout changes and no phase completion.
Parent must run integrated assurance. No additional in-scope fix is outstanding.

## 2026-09-07 — Fixture acceptance correction and completion review

Reassessed the preceding broad-source blockers against the actual fixture task.
They were an overbroad interpretation, not missing production functionality
required by this task. Verified all eight linked fixtures, 40 source-field
observations, nine corruptions caught by the independent fixture oracle,
approved adapter ID preimages, actual projection replay/accounting and eight
source-lineage corruptions rejected by production adapters. CPI/Pharmac mapping
is explicitly test-only and retains source ID/amount lineage without asserting
complete canonical projection. Existing source-specific negative/property tests
are included in the 673-test affected run. Lint/format/types pass.

The [final matrix](./eight-recordset-fixture-completion.md) identifies no unmet
fixture clause. Marking the fixture task complete does not close source-family
projection tasks or the full AC-16 checkpoint. No new production validator,
dependency or external action was needed. No in-scope review finding remains.
# 2026-09-07 — Bronze checkpoint follow-up

Phase 2.1 cooperative per-resource resume and non-overwriting WARC paths are
implemented in the isolated Bronze worktree after `0cf0f32b`. Initial missing
checkpoint red is retained in `bronze-checkpoint-contracts.md`; final 43 focused
and 149 affected tests pass, runner coverage is 100% line/branch, four seeded
mutants are caught, and Ruff/format/basedpyright pass. The paired machine
receipt is `bronze-checkpoint-validation.json`. Self-review checked receipt
fixity, repeated interruption, orphan preservation, competing-writer fencing,
and manifest compatibility. Exact Phase 2.1 gaps remain documented; no broad
completion, full-harness, source-census, rights, parent-edit or Phase 3 claim.
# 2026-09-07 — Phase 2.1 hard-kill recovery

Replaced ambiguous directory ownership with an OS-released SQLite transaction
lock. Real subprocess kill/resume passed after the recorded red failure;
44 tests, 100% runner coverage and three killed mutants. Static checks pass.
Paired evidence: `bronze-process-recovery.md` / `bronze-process-recovery.json`.
Self-review retains legacy-lock, power-loss and filesystem boundaries. No
parent, census, rights, registry, Phase 3 or full-harness changes.
# 2026-09-07 — Phase 2.1 encoded length

Reviewed pinned HTTPX raw-counter/decoder semantics before three red tests.
Encoded transport-body length is now verified without comparing decoded size;
preconsumed encoded responses with length fail closed as unverifiable.
161 affected tests pass, with 99.02% capture coverage and four caught mutants.
Paired evidence: `bronze-wire-length.md` / `bronze-wire-length.json`. Static
checks pass. Review retains precise framing/codec and AC-16 coverage limits;
no weaker verification, raw-wire assurance, source promotion or full harness.
# 2026-09-07 — Phase 2.1 local review boundary

Eight valid HTTP redirect-budget characterization tests passed before the
behavior-preserving fallback routing change. Final affected suite: 169 passed,
capture 100% line/branch coverage, three killed mutants, static checks passed.
Paired evidence: `bronze-redirect-boundary.md` / `.json`. Self-review found no
remaining actionable defect in the requested slice. Stop here for parent full
assurance and independent review; no full harness or further implementation.

## 2026-09-13 — Normalization checkpoint review

Plan compliance: the normalization and SQLite implementation and tests already
match the final receipt; the missing item was its checkpoint handoff. Original
receipts and existing ledger bytes are preserved. New source-ref verification
and 260 focused tests support the bounded checkpoint, without reusing historical
mutation counts as fresh results or closing broader Health acceptance. No
actionable finding remains in the evidence integration; full gates are in the PR.
## Scheduled discovery heartbeat — 2026-09-28

Self-review confirms the heartbeat hashes the exact bounded manifest bytes,
redacts read/parse failure details, and reports workflow success independently
from discovery, metadata drift, capture, normalization, validation, and
publication. Missing, unreadable, malformed, unavailable, oversized, and
contract-drifted inputs are covered. The workflow remains metadata-only and
grants no additional permissions. No actionable finding remains in this
bounded task; actual hosted heartbeat evidence is pending the next workflow
run and is not asserted here.

## Read-only Health status resource — 2026-09-28

Self-review confirms the resource is a fixed local URI, delegates to the
existing schema-validated read-only status query, performs no writes and
preserves exact manifest digests and paths. Tests exercise MCP protocol
listing/read and the non-interactive CLI parser. No capture or publication
behavior is added. Remaining operation families are outside this slice.

## Coverage follow-up — 2026-09-28

The initial hosted review flagged incomplete patch coverage. The follow-up
covers normal CLI reads, the module entrypoint, non-object JSON, invalid UTF-8
and excessive JSON nesting; the heartbeat module now passes all statement and
branch cases. No behavior or workflow permission changed.

## Drift baseline review correction — 2026-09-28

Addressed the automated review finding: the scheduled lane supplies no prior
manifest, so the heartbeat now reports metadata drift as unavailable. Only a
complete, observed prior manifest with count-matched SHA-256 fingerprints can
enable drift counts. Missing or malformed baselines remain metadata-only and
do not change discovery or downstream-stage claims. Focused contracts pass;
the clean full harness passed 7,035 tests with all configured gates. Hosted
assurance is pending on the corrected PR head.

## 2026-09-29 — Expanded clean-room recovery review

The recovery runner now executes the pinned four-profile original-to-raw
pipeline twice, verifies each raw-run manifest, then rebuilds compatibility
SQLite/sidecars, Gold and six plot images in separate empty directories. It also
rebuilds population Silver, contextual Gold and historical canonical Gold.
Repeated output file inventories match within this runtime, and the complete
Bronze CAS inventory is unchanged. The contract is intentionally scoped to the
pinned donor profiles and currently supported canonical/context builders.

The receipt remains partial: all source-native Silver families, donor/canonical
reports and complete validated Platinum metadata are not rebuilt. AC-12/M-16
remain open. Prior cross-runtime SQLite header drift is preserved as a limitation;
no database header bytes are patched. Rights are not evaluated and publication
is not performed.


Full `./scripts/validate.sh` passes 7,114 tests (9 skipped), 98.19% branch
coverage, all 52 schemas/42 representative documents, parity 9/9, and configured
mutation/supply-chain gates. The automatic `phase_7_gates` Conductor review
also passes. The recovery test remains partial and does not close AC-12/M-16.

## Whole-census source-health report — 2026-09-29 UTC

Scoped self-review of `source_health_report.py`, its generator, schema, tests and
rendered report found no remaining actionable defect within the report's stated
contract. Resource and context rows are uniquely identified and sorted; captured
rows are joined against the full census and retained manifest, and every CAS
object is rehashed and size-checked before reconciliation is reported. Capture
workflow rights labels remain separate from the report's unapproved rights
state. The renderer exposes explicit temporal/layout non-assessment states and
the report records its census and manifest digests. Malformed input, mismatch,
missing-object and corrupted-object cases fail closed in the focused tests.

The report does not claim legal rights approval, full calendar/discovery
coverage, per-vintage layout drift, analytical comparability or donor-value
reconciliation. Those phase gaps remain open. Validation passed locally with
67 focused source-health/census/review tests, 78/78 focused mutation kills and
the full repository harness; see the dated machine receipts. This is not hosted
CI evidence or phase completion.

### Patch-coverage follow-up — 2026-09-29 UTC

The initial hosted patch report found that malformed-input and CAS mismatch
branches in the new module lacked direct coverage. Added focused error-contract
tests rather than changing the repository's coverage threshold. The complete
source-health module now has 100% statement and branch coverage (30 focused
tests), and 78/78 module mutants are killed. Full local harness passes at
98.27% overall against the unchanged 80% floor. Hosted CI must be rerun on the
coverage-correction commit before merge.

### GDP June-vintage source census follow-up — 2026-09-30 UTC

The June 2026 Stats NZ current-price GDP workbook is captured as a new Bronze
object and kept separate from the March 2026 vintage. The exact selector is
Table 1!C27:BK27 (reference SG03AB01GE00S900, prefix SNEQ), covering 61
quarter observations through June 2026; the distinct seasonally adjusted Table
2 series remains excluded. The source census now records 142 resources (74
captured, 68 discovery-only), and the refreshed report replays all 74 captured
objects against the whole-census manifest and Bronze CAS.

The census and capture receipt retain `rights: not_evaluated` and
`qualification: unqualified`. The official Stats NZ terms page states CC BY
4.0 applies unless otherwise specified and includes exceptions and attribution
conditions; capture eligibility is not legal approval. Currency, annual GDP
aggregation, vintage splicing, denominator joins and publication remain
unqualified. March data are not replaced or spliced.

Focused census, report, measure-review and recovery-binding tests passed (95).
The full required harness passed with 7,181 tests, 9 skips and 98.27% coverage
against the existing 80% floor; 53 schemas/43 documents, 9/9 parity, all
configured mutation lanes, hygiene, CAS benchmark (705.77 MB/s), audit, license, secret and
SBOM stages passed. The automatic Bronze Conductor phase gate passed format,
lint, schema and targeted Bronze tests; receipt SHA-256 begins
`c065138752d73750`. Hosted PR checks have not yet run.

## 2026-09-30 — June GDP successor extractor review

The June-quarter addition is versioned independently from the March GDP
profile. It requires the June release title/date, exact `C27:BK27` extent and
merged range, period labels, reference/prefix, unit, numeric format and all
selected workbook metadata before emitting facts. The Q2 source operation has
an exact profile-to-vintage binding; the Bronze dispatcher uses the same strict
extractor. Tests cover 61-period chronology, separate vintage identity,
preservation of unknown currency and no rights promotion. The captured Bronze
source rebuilt twice with identical Silver manifests and payloads; byte fixity
and census/source bindings were independently checked by the clean-room runner.
No June observation enters the March Context Gold or canonical projection, and
no annualization or denominator is performed.

Remaining limits are explicit: the new vintage has no canonical projection,
cross-vintage revision comparison, annual aggregation, currency qualification,
rights approval or publication. Focused GDP, dispatcher, operation and recovery
tests pass (596 passed, 10 skipped). The full local harness passes 7,220 tests,
10 skipped at 98.27% branch coverage, plus schemas, parity, mutation, hygiene,
supply-chain and SBOM gates. The automatic `phase_7_gates` review passes its
targeted phase checks. Full track-level completion review and current-head
hosted assurance remain pending; no phase or whole-track completion is claimed.

## 2026-09-30 — Coverage gate alignment

Hosted review found that Codecov's implicit patch `auto` target was 97.92%,
above the intended 80% threshold. The configured patch target is now 80%, and
the assurance-policy test pins both the repository total-coverage floor and
the Codecov patch floor to 80%. Codecov's YAML validator and the focused test
passed; final hosted checks for this update remain pending.

## 2026-10-03 — Phase 3 integrated assurance

The integrated full harness passes on `496cdff9`: 7,286 passed, 10 skipped,
98.14% branch-aware coverage against the agreed 80% floor. Schema, typing,
mutation, parity, archive-safety and source-lineage checks pass. The Phase 3
contracts were reviewed as a whole and already exercise its boundaries; the
checkpoint adds no coverage-only tests. Exact-head hosted checks remain pending
for the PR.

## 2026-10-03 — Vote Health 2002/03 Part F revenue self-review

The new operation is pinned to the exact source hash and 44-page document, and
only admits the reviewed Part F marker and page span. The parser requires the
expected row count and totals, preserves the three distinct fiscal columns,
retains source tokens and explicit page/field lineage, and leaves dash values
null. The common Bronze adapter is unique for the pinned 2002/03 source and
accounts for every page; its revenue records match the independent Silver
build by ID and every emitted field. Repeated manifests and outputs are
identical, and source fixity is unchanged.

No substantive finding remains for this bounded profile. Limits remain:
rights are not legally evaluated; no currency or cross-source comparability is
claimed; summary and other editions remain open; no canonical Gold or
publication is produced. Focused tests and Ruff pass; the full repository gate
is pending.

## 2026-10-03 — Vote Health 2002/03 overview headlines self-review

The added overview operation binds extraction to the same exact 44-page source
hash as the 2002/03 detail and revenue profiles. It requires all seven reviewed
phrases exactly once on pages 2–3, emits decimal `$ million` values with a null
currency code, and preserves raw tokens, source phrases, and page/field
lineage. It does not infer an earlier total or normalize surrounding
components. Targeted tests cover the expected values, phrase drift and
ambiguous duplicates; source-operation dispatch remains allowlisted and its
receipt schema validates the output package. Rights are still not legally
evaluated, other page content remains preserved-only, and no Gold or
publication claim follows. Full validation is pending.

## 2026-10-03 — Vote Health 2004/05 overview headlines self-review

The new profile binds extraction to the exact 48-page captured Treasury PDF
hash. It requires all eight observed monetary phrases exactly once across PDF
pages 2–3, preserves decimal amounts, source phrases, raw tokens, distinct
period labels and page/field lineage, and does not recompute totals. The
captured-source integration test confirmed all eight values and local output
readback. The common operation registry and committed JSON schema include the
new profile and transformation. Rights remain unevaluated, the extraction is
local-only, and no conclusion is made about the rest of the PDF, other editions
or comparability. Focused tests and Ruff pass; full repository validation is
pending.

## 2026-10-03 — Source-health layout evidence recovery and pinning

PR #610 review identified four evidence-integrity gaps. Recovery replay now
loads and supplies the pinned PDF layout baseline, and its fixture exercises
the same input. Offline report regeneration can retain layout states only when
the prior report is bound to the exact current source-census bytes; otherwise
layout, capture-manifest hash, and capture receipt are not copied forward.
Baseline source IDs are joined to census object SHA-256 values before structural
states are admitted. The builder accepts an explicit `--recorded-report` path
so evidence retention does not depend on whether the output already exists.

Focused source-health and recovery suites pass (53 tests); repository-wide lint,
format, and typing pass. The required `./scripts/validate.sh` run passed 7,331
tests, 10 skips, 80% coverage floor (98.01% observed), 53 schemas, 9/9 parity,
all configured mutation suites, hygiene, benchmark, dependency, license, secret,
and SBOM checks. Recovery remains structural only; PDF text/table semantics,
rights, and complete source coverage are not claimed.


## 2026-10-03 — Vote Health 2005/06 overview headlines self-review

The new profile binds extraction to the exact 50-page captured Treasury PDF
hash. It requires each of the eight observed monetary phrases exactly once
across PDF pages 2–3, retains distinct GST basis labels, decimal values, source
phrases, raw tokens, period labels and page/field lineage, and does not
recompute totals. Captured-source integration readback confirmed all eight
values and page dispositions. The operation registry and committed JSON schema
include the profile and transformation. Rights remain unevaluated, extraction
is local-only, and no conclusion is made about the remainder of the PDF, other
editions or comparability. Focused parser and dispatch suites pass. The required `./scripts/validate.sh`
passed 7,351 tests with 10 skips and 98.08% branch-aware coverage against the
80% floor; schema, parity, configured mutation, hygiene, supply-chain and SBOM
gates passed. Automatic `phase_7_gates` review passed; its immutable receipt is
`phase_7_gates-review-receipt-20261003-vote-health-overview-2005-06.json`
with SHA-256 `b3507de62fca41ec3da8c2b4935013ca160ac69edcc28453930e168fc91c537e`.


## 2026-10-03 — Vote Health 2006/07 overview headlines self-review

The new profile binds extraction to the exact 41-page captured Treasury PDF
hash. It requires all eight observed monetary phrases exactly once across
pages 2–3, retains decimal values, source phrases/tokens, period labels and
page/field lineage, and makes no inferred sums. Captured-source integration
readback confirmed all eight values and page dispositions. The operation
registry and committed JSON schema include this profile and transformation.
Rights remain unevaluated, the extraction is local-only, and the rest of the
PDF, other editions and comparability are outside the claim. Focused tests pass;
the required full harness passed 7,355 tests with 10 skips and 98.08% branch-aware coverage against the 80% floor. Schema, parity, configured mutation, hygiene, supply-chain and SBOM gates passed; automatic phase review passed with receipt SHA-256 `58789359490b10dd969e9792b05ff0aa4021d7a2c5beb116d12be72e081a4a93`.


## 2026-10-03 — Vote Health 2007/08 overview headlines self-review

The new profile binds extraction to the captured 53-page Treasury PDF and its
SHA-256. It requires the eight observed monetary phrases across pages 2–3,
retains decimal values, exact source phrases/tokens, periods and page/field
lineage, and recomputes no totals. Captured-source readback confirmed the eight
values and output digests. The operation registry and generated JSON schema
include this profile and transformation. Rights remain unevaluated, extraction
is local-only, and claims exclude the rest of the PDF and other editions.
Focused parser/dispatch tests passed; the full required harness passed 7,357
tests, 10 skipped, and 98.08% branch-aware coverage against the 80% floor.
Automatic phase review passed with receipt SHA-256
`3486688fca2a3f1d99894abd9db8364fd198e0090dfccd91d62134c9c807f9d2`.


## 2026-10-03 — Vote Health 2008/09 overview headlines self-review

The profile is bound to the captured eight-page Treasury PDF hash and selects
six observed page-2 phrases. The source values are approximate rounded whole
millions; the “just over” and “nearly” qualifiers remain in raw phrases and
quality flags explicitly reject exact-amount interpretation. Two separate
builds matched all three Silver output files byte-for-byte. The cumulative
capture manifest, WARC digest, census row and rights evidence are retained;
rights are eligible under CC BY 4.0 with attribution to The Treasury New
Zealand, while publication remains local-only. The refreshed census has 143
resources and 11 context vintages, and the structural PDF baseline reconciles
59 PDFs with 56 recorded and 3 unavailable. The pypdf Xref warning is recorded;
hash verification and six selected phrases passed. Only page 2 is in scope.
The required full harness passed 7,360 tests with 10 skips and 98.08%
branch-aware coverage against the 80% floor; schemas, parity, configured
mutation, hygiene, supply-chain and SBOM gates passed. Automatic phase review
passed with receipt SHA-256
`871382eb7ccf42d01ed3e79084ba74b703d6bd74bfb82a6d76da3623472d3655`.

The PR review also identified two evidence issues, now corrected: combined
Supplementary Estimates volumes containing appended supporting information are
counted as editions, while supporting-information-only documents remain
excluded; page 3 is now explicitly `preserved_unreviewed` because no facts are
extracted from it.


## 2026-10-04 — QES adjustment evidence follow-up

The selected QES measure is still the retained June 2026 Table 8
`QEMQ.SASZ9A` series. The retained June 2026 workbook's Table 8 maps its `QEMQ` / `SASZ9A`
selector to ordinary-time hourly earnings, and the official June 2026 labour-market
summary says this measure is not seasonally adjusted. The supplemental
definition and source-measure inventory now carry that bounded disposition.
The workbook's `$` label does not establish an ISO currency code; currency and
rights remain unknown/unadjudicated, and analytical selection, annual weighting
and fiscal-period joins remain unselected. No source or Silver bytes changed.

Focused QES and source-measure tests passed (65 tests); the required full
repository harness passed 7,360 tests, 10 skips, and 98.08% branch-aware
coverage against the 80% floor. Schema, parity, configured mutation, hygiene,
supply-chain and SBOM gates passed. Automatic `phase_7_gates` review passed
with receipt SHA-256
`1d9873173e8c6973fbad2d7d79ae130d7d7c930bcc4f5d8741744fb598582ac0`.


## 2026-10-04 — Vote Health 2009/10 overview increment

Self-review confirms the extractor is pinned to one captured Treasury PDF hash,
release vintage, and exact page count. All 17 selected values are anchored to
unique source phrases and preserve their raw amount tokens; approximate
whole-million source wording is surfaced in unit/quality metadata. Regression
and captured-source CLI builds match. The remaining seven pages are explicitly
preserved-unreviewed, rights on extracted facts remain not evaluated, and no
publication or cross-edition comparability claim is made. The retained Xref
warning is disclosed. Required full assurance and automatic phase-7 review are
still pending at this entry.

Final assurance for this increment passed on 2026-10-04: `./scripts/validate.sh` reported 7,373 passed, 10 skipped and 98.08% branch coverage; all schema, parity, configured mutation, supply-chain, secret-scan and 113-component SBOM checks passed. Automatic `phase_7_gates` review passed; its retained receipt is `phase_7_gates-review-receipt-20261004-vote-health-overview-2009-10.json` (file SHA-256 `7320aeb3a4350021a8e161c33a86418452b332a3e755842e448f99c4655a5b53`). The first preliminary run exposed a formatting issue, a lint issue and the stale source-review evidence pin after index links changed; each was fixed and the corresponding focused/full validation passed.
The exact captured object also has an additive one-resource census and an
independent source-health reconciliation. An initial reconciliation invocation
used the Bronze parent directory where this report helper expects the CAS
`sha256` directory; it failed closed with `capture_object_missing`. The retry
used the correct root, verified the 60,661-byte object, and passed. This did not
change source bytes or the pinned census baseline.


Review follow-up for PR #619: the review's page-disposition completeness finding
was valid. The extraction now emits dispositions across all eight PDF pages;
page 2 is partially normalized and pages 1, 3–8 are preserved-unreviewed. The
receipt, test, and repeat-build hashes were refreshed. The full required harness
passed (7,363 passed, 10 skipped, 98.08% coverage against 80%); schema, parity,
mutation, supply-chain, secret-scan, SBOM and Phase 7 checks passed.


2010/11 Vote Health Estimates increment: Treasury identifies the signed,
superseded Estimates as issued 20 May 2010 and its publication as CC BY 4.0.
The exact 55,369-byte PDF was captured and independently reconciled against its
WARC and Bronze fixity. The edition-pinned adapter extracts 18 statements on
pages 2–3; each source page receives an explicit disposition (2–3 partially
normalized; pages 1 and 4–9 preserved-unreviewed). The extracted amounts and
qualifiers remain source-led; no sums are recomputed. Two repeated CLI builds
match byte for byte. pypdf's Xref correction warning is retained. Rights on the
derivative are unevaluated, publication is not approved, and seven pages remain
unreviewed.


2010/11 Vote Health Estimates assurance is complete for this bounded overview
increment: `./scripts/validate.sh` passed with 7,366 tests passed, 10 skipped,
and 98.08% branch coverage against the 80% floor. Schema (53/43), parity 9/9,
configured mutation, supply-chain, secret scan, and strict 113-component SBOM
checks passed. Automatic Phase 7 review passed; receipt SHA-256 is
`a5853c57d094b40f20dd59ab7a03576c25ab54af8102bb5ed0c1e4f1c814bbf8`.

## 2026-10-04 — Source-qualified Fiscal share self-review

The verified query uses the same pinned original for historical and Crown
inputs. Pure arithmetic is explicitly separate from package verification.
Source/year/unit/basis and identity gates reject incompatible inputs, and
missing/nonpositive denominators retain reasons and input IDs. Exact dollar
million ratios avoid an unsupported ISO currency inference; Total Crown
shares preserve the Core Crown Health numerator scope. Source-year caveats
remain per row, and annual periods follow the retained Treasury definition.

Fresh Bronze replay and independent rational checks pass. No other edition,
context deflator, cross-source join or publication is admitted. The query
product still needs canonical Gold exporter, CLI/MCP and plotting integration.
Full repository and hosted gates remain pending at this entry.

Final local assurance passed: `./scripts/validate.sh` reported 7,395 passed,
10 skipped, 98.09% coverage against the 80% floor, 53 schemas/43 representative
documents, parity 9/9, configured mutation gates, supply-chain/secret checks
and strict 113-component SBOM validation. The automatic `phase_7_gates` review
passed; its dated receipt is retained beside the share replay receipt. The
first full invocation stopped at three test-style lint diagnostics; those
were corrected before the successful run. Hosted validation remains separate.

### PR #627 period evidence correction

Codex identified that the reviewed query did not hash-bind the external fiscal-period definitions. The correction requires the exact retained observation input, rejects missing/changed bytes, preserves source time-status labels in every derived row, and validates null source starts. Eighteen focused tests passed. Native Bronze replays regenerated the product twice with identical bytes and all 115 independent rational checks. Full assurance is being repeated for the corrected code.

The first remote assurance run and corrected local full run both stopped on the secret scanner misclassifying the local product path as Base64 entropy. The receipt now separates its external root and relative path, preserving the exact product location without a gate exclusion. Tests (7,396 passed; 10 skipped), schemas, parity, typing and all mutation gates passed before that failure. A fresh required harness run checks the final receipt representation.

Final corrected validation passed: `./scripts/validate.sh` exit 0, 7,396 tests passed, 10 skipped, 80% coverage floor retained; schemas, parity, configured mutation and supply-chain gates passed. Automatic scoped Conductor review also passed. The full Health track completion gate remains open.

### Fiscal spending per annual mean resident (4 October 2026)

After PR #627 passed all exact-head hosted checks, it was merged and its clean
worktree removed after remote integration/tree equality proof. Primary main
fast-forwarded cleanly. This fresh worktree adds a bounded pinned two-vintage
per-capita policy. Initial red tests failed on the absent module; 18 focused
tests now pass, with typing/lint and all changed-module branches exercised.
Two fresh native Bronze rebuilds agree byte-for-byte; all 34 calculated rates
match independent rational arithmetic. Missing population and March-year
exclusions remain explicit. Source/provisional/accounting/revision flags and
period evidence identities remain visible. No rights/publication gate closes.

Required local harness passed: 7,414 tests, 10 skipped; 80% coverage floor unchanged, measured 98.09%; 53 schemas, 43 representative documents, parity 9/9, all configured mutation gates and supply-chain controls passed. Scoped automatic Conductor phase review passed; its receipt is retained. Full Health track review/completion remains open.

PR #628 review: accepted Codex's omission finding and carried both source
time-status labels into the derived table. Eighteen focused tests still pass;
two fresh native replays again agree and all 34 rates independently match.
Amazon Q's precision concern was rejected: the existing test deliberately
checks isolation from caller ambient precision; an additional bounded probe
confirmed the exact result under ambient precision 2 and caught a production
precision-2 mutant. No arithmetic policy change was made. Repeat full assurance
is required for the added provenance fields.

Corrected full harness and scoped phase review passed: 7,414 tests, 10 skipped; 80% coverage floor retained; all configured schemas, parity, mutation and supply-chain controls passed.

### Household CPI fiscal purchasing-power benchmark (4 October 2026)

PR #628 passed exact-head hosted checks, merged and its clean worktree was
removed after remote integration and tree-equality proof. Primary main is
current and clean. This fresh worktree implements a bounded Fiscal/CPI policy
with equal-quarter means, FY2025 benchmark and complete source quarter/time
lineage. Initial red tests failed on the absent module; 17 focused tests now
pass, with lint/typing and all changed-module statements/branches exercised.
Two fresh native Bronze rebuilds agree byte-for-byte; all 54 means/rates match
independent source-CSV rational calculations. The independent audit parser's
initial `NA` failure was recorded and corrected to missing-value handling; all
27 such source observations predate this fiscal cohort. No production value
or original changed. No health-input-cost, ISO-currency or rights/publication
claim is made. Integrated Gold and final completion gates remain open.

Full required harness and scoped phase review passed: 7,431 tests, 10 skipped; 80% coverage floor retained; schemas, parity, all configured mutation and supply-chain gates passed. This bounded query evidence does not close integrated Gold, operations or final track review.

## Fiscal analytical Gold package (2026-10-04)

Nine focused tests pass at 86.81% coverage with the requested 80% floor. Two native
source-reverified package builds produce identical manifest/Parquet bytes and all
four typed tables read back. Three originals retain their digests. This is a
bounded local export; it does not close DuckDB, plots, operations or final review.

Required validation harness passed: 7,440 tests, 10 skipped, 98.05% aggregate
coverage with the 80% floor; schemas, parity, configured mutation gates and
supply-chain checks passed. Final nominal schema-label correction was checked
with the nine focused tests, typing and a new identical native pair. Scoped
phase_7_gates review passed; the full track completion gate remains open.

## Named Fiscal analytical queries (2026-10-04)

Initial red collection demonstrated the absent adapter. Nine focused tests now
pass. All 324 native rows match independent Arrow and real console/initialized
MCP readbacks. Package files remain unchanged; bad pin returns console exit 2.
No arbitrary SQL, source re-verification, rights or publication claim is added.

Required harness passed: 7,449 tests, 10 skipped, 98.05% aggregate coverage
with the 80% floor; schemas, parity, configured mutation and supply-chain gates
passed. Scoped automatic phase_7_gates review passed. This does not close the
remaining products or full-track review gate.

PR #631 review accepted the failed-query MCP error-flag finding. The new
protocol regression failed before the correction; failed structured receipts
now set isError true. Native all-row parity still passes, and invalid-pin MCP
readback confirms an error flag with the bounded receipt preserved. Ten focused
query tests and the adjacent inspection suite pass. Original replay recipe and
receipt were retained as version 1 before the version 2 readback.

After the transport correction, the full harness passed again: 7,450 tests,
10 skipped, 98.05% aggregate coverage with the 80% floor. All schema, parity,
configured mutation and supply-chain gates passed. The scoped automatic review
also passed again. Native successful results remain identical; failed MCP calls
now carry the correct protocol error flag and structured failure receipt.

## Fiscal analytical reports — bounded evidence

Two native CLI builds match all twelve files; 257 points and 67 exclusions match
independent direct Arrow values. Focused tests cover dry-run, exclusive writes,
input overlap, malformed source results, tampering and independently parsed RDF
checksums/edges. The 80% coverage floor remains unchanged. This scoped delivery
does not close the full track completion gate.

PR #632 review: accepted cross-table parent-validation finding and added one
regression exercising fourteen share/per-capita context mutations. Rejected two
Amazon Q syntax findings against the required Python 3.14 runtime; actual CLI
execution, AST parse, typing and tests prove the supported exception syntax.
Bounded adjudication is retained externally.

## Integrated Fiscal recovery

The three new failure contracts pass and the existing wider receipt contract
requires the added product entry. Required local validation passed: 7,460 tests,
10 skipped, 97.85% aggregate coverage with the 80% floor unchanged. Scoped
Conductor phase review passed. The final metadata-only blocker-label correction
is rechecked with the 13 focused assurance tests. Native reconstruction is
still running; full Health completion is not asserted.

The focused native recovery passed: 34 files per run, two fresh Bronze builds,
all 324 console/MCP rows equal direct Arrow and all Gold/report bytes equal the
retained qualified products. The wider native run exposed stale capture and PDF
layout references; failure and interruption receipts are retained externally.
The runner now selects the existing, separately pinned 3 October manifest and
PDF baseline. Source-health replay matches the unchanged recorded report and
verifies all 75 captured objects; classification and accepted non-mutating donor
replay preflights pass. Thirteen focused tests pass after the binding correction.
The final wider run and final full harness are running.

The wider native replay completed all 21 supported product groups with Bronze
unchanged. Its Fiscal inventories/receipts exactly match the focused proof.
Hosted patch coverage then failed at 51.92% against the unchanged 80% target.
Two added real-interface tests cover console/MCP/Arrow agreement and corrupt
or absent MCP delivery; the source-pin contract now covers definition evidence.
Five recovery tests measure 82.61% for the helper. The actual console test also
required selecting the installed .exe launcher on Windows. A new pair of fresh
Bronze builds after that portability correction still matches all 34 files,
324 query rows and retained qualified Gold/report bytes. Final harness reruns.

Final follow-up validation: required harness passed with 7,462 tests and 10 skips; 80% floor unchanged. Scoped review and fresh focused native recovery passed after the Windows launcher fix.

## 2026-10-05 — Budget estimate-transition self-review

Verified conservative all-dimension keys, no aggregation, no duplicate resolution or zero substitution, exact Decimal subtraction and input provenance bindings. Known reviewed original pins qualify period metadata; package consumption checks fixity/contracts and does not independently re-prove source cells. The external native replay separately audits those cells. Supplementary Estimates, restructuring and GST caveats prohibit performance/reconciliation claims. This closes only the bounded library query after evidence is complete; wider comparisons and operations remain open.

Final evidence: required ./scripts/validate.sh passed with 7,466 tests / 10 skips and all configured gates; four focused tests passed. Two fresh Bronze builds have identical complete inventories and unchanged originals. Independent OOXML checks cover all 400 selected facts across the source vintages and all their raw cells; 37 differences checked in integer thousandths. Output has 60 groups: 37 unique pairs, 11 earlier-only, 12 later-only, zero ambiguous. All 97 transition records accounted for; 303 records outside transitions. Native receipt SHA-256 8b4b93c0f482f5e4c2a0527c052d3469f0f3516c927474432d86e35678c4fdcd. Scoped phase gate is not the final Health completion review.

## 2026-10-05 — Budget comparison Gold delivery

M-13/M-15, AC-11/AC-13: three new tests red on missing module, then green after explicit Parquet list-element schema and MCP output contract fixes. Native installed build timed out after successful output; sampled shutdown showed Arrow ThreadPool waiting on a Python-buffer destructor trying to acquire the finalized GIL. Preserved v1 package/log/stack, stopped only the verified owned diagnostic PID, then used synchronous small-table decoding. Final native v2 builds exited and matched all five files; CLI/MCP/Arrow agree on 60 rows, 37 plot points and 23 exclusions; bad pins give exit 2/isError. Input packages and originals unchanged. Three focused tests pass; measured module coverage 100%, target unchanged at 80%. Source scope/semantics unchanged; reader does not reverify originals. Full harness and scoped review follow.

The first full harness retained one MCP standard failure (missing JSON Schema dialect URI); added the repository-required 2020-12 declaration to both schemas. All 21 focused MCP/delivery tests then passed. Native v3 after that contract fix exits successfully, matches v2 byte-for-byte and binds the current code. Scoped automatic phase review passes; it is not the final whole-Health completion review.

Final required harness passed: 7,469 tests and 10 skips, 97.93% aggregate coverage with the unchanged 80% floor. Format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates pass. Native v3 proves paired byte-identical packages and exact 60-row CLI/MCP/Arrow delivery. Scoped automatic review passed; broader Health completion remains open.

## 2026-10-05 — Local analytical Gold metadata

M-14 / AC-14: three focused tests began red on the missing module. Initial green verified exact metadata and offline RDF. Retained static-check and RDF fixture failures before fixing type-only imports and a graph/namespace name collision in the test. Three final tests pass, including installed CLI dry-run/write/reconstruction/exit-2 behavior and incompatible rights rejection. Native paired builds match all six files and describe five recordsets / 384 rows. Independent Gold-file reads verify every digest, schema, count and period summary; Gold inputs unchanged. Source re-verification, rights, release, broader Platinum and full Health completion are not asserted. Required harness and scoped automatic review follow.

Final required ./scripts/validate.sh passed: 7,472 tests / 10 skips, 97.90% aggregate coverage with the unchanged 80% floor. Format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates passed. Scoped phase review passed; native paired six-file metadata replay and input preservation passed. Broader Platinum and final Health gates remain open.

## 2026-10-05 — Gold discovery candidates

M-14 / AC-14: checked official Croissant 1.0 and RO-Crate 1.1 required properties. Publication date, creator, licensing and access metadata are not evidenced; generated local candidates and explicit gaps instead of default values or conformance assertions. Two tests red on missing module, then green; one long-line lint issue corrected. CLI process completion and exit-2 behavior pass. Native paired four-file builds agree; independent reads verify ten files, five recordsets and all columns; actual RDF graphs parse with external file/network access denied. Gold unchanged. Full harness and scoped phase review follow; broader standards/release/recovery gates stay open.

Self-review found returned contexts aliasing the internal profile dictionary. Added a regression assertion to an existing test: red showed altered context accepted. Copying each context makes that assertion green and preserves every candidate byte. Two native v2 builds after the fix exit successfully and match v1 exactly. Required harness and scoped review are repeated for the corrected code; no gate was weakened.

Final required harness passed: 7,474 tests / 10 skips, 97.87% aggregate coverage with the unchanged 80% floor. Format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates passed. The added assertion initially exceeded the test-function size limit; that failure was retained and the assertion moved into the existing RDF test. Corrected-code scoped phase review passed. Native v2 candidates remain byte-identical across both builds; broader standards, release, recovery and full Health completion remain open.

Hosted CI blocker: Linux passed the complete assurance harness twice, then Codecov CLI downloads failed with a TLS handshake error and missing signature files. The same host fails locally. The workflow now downloads the official GitHub v11.3.1 Linux release, verifies its pinned SHA-256 (independently matched against the release API and downloaded bytes) before execution, then uses the documented pre-downloaded binary input. OIDC, fail-on-upload-error and the 80% coverage floor remain enabled. Action lint and all six existing workflow-policy tests pass. Retained both hosted failures outside Git. See [Codecov action inputs](https://github.com/codecov/codecov-action) and [official CLI release](https://github.com/codecov/codecov-cli/releases/tag/v11.3.1).

Required harness after the CI transport fix passed again: 7,474 tests / 10 skips, 97.87% coverage with the 80% floor. Scoped phase review and workflow lint pass. Native candidate production code and bytes remain unchanged. Final-head hosted checks follow.

## 2026-10-05 — Integrated analytical metadata recovery

M-10/M-16/M-18, AC-08/AC-12/AC-16: earlier native prototype rebuilt all 57 scoped files twice from fresh Bronze and matched retained products. Added two failing contracts on the missing recovery module; after implementation both pass, including installed CLI failure handling. Retained lint failures before specifying the exact source-hash failure message. Format, lint and strict typing pass. Native installed CLI now runs against a separate clean archive containing only five original objects and three pinned definitions; final harness and scoped review follow. This does not close broader source, standards, rights, publication or final Health completion gates.

Final native installed CLI exits 0: clean archive has only eight copied inputs; two 57-file output inventories match, including retained qualified products. Dry-run, exclusive output and changed-source exit-2 behavior pass; originals and definitions unchanged. Full required harness passes (7,476 tests / 10 skips, 97.80% coverage; 80% floor unchanged), including format/lint/typing/schema/parity/mutation/supply-chain gates. Scoped automatic review passes, without asserting whole-Health completion. Integration PR remains sequentially queued behind #637 and its external Codecov policy decision.

The integrated Health recovery harness now consumes the new analytical recovery lane. Its existing Fiscal receipt key is preserved; an additional analytical Gold/metadata receipt records the full supported reconstruction. Complete Platinum standards, remaining source families, broader comparisons and the final completion gate remain explicitly unresolved. The existing integration test was extended (red on the missing hook, then all ten tests green); retained the import-order lint failure before fixing it. Native integrated assurance and repeated required validation are running.

Integrated native assurance exits 0, verifies the new two-run 57-file analytical lane and preserves the existing Fiscal receipt. All Bronze objects remain unchanged. Overall status remains partial_with_blockers: broader cross-source comparison, remaining source-native adapters and complete Platinum profiles are still required. Full harness passes again (7,476 tests / 10 skips, 97.80% coverage with the 80% floor); all ten integration tests and scoped phase review pass. This does not close the whole-Health gate.

## 2015/16 Vote Health overview — 2026-10-05

Source/WARC payload fixity and 17 source tokens verified. Fourteen explicit qualifiers retained; source-specific purchase/refinancing categories are not joined across editions. Native and installed-command builds match; wrong pin/vintage and existing output give exit 2. Capture date is unavailable; local source-verification timestamp is explicit. Remaining 99 PDF pages, normalized rights and publication remain unqualified. Scoped phase gate passed; full harness is pending and whole-Health review remains open.

Final required ./scripts/validate.sh exited 0: 7,476 tests / 10 skips; format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates passed. Scoped review passed. Coverage floor remains 80%; broader Health completion is not asserted.
## 2026-10-06 — Integrated recovery and whole-track reconciliation

Ran the integrated Bronze recovery runner and current source census validator;
the supported lanes repeat, Bronze remains unchanged, and the recovery receipt
correctly remains `partial_with_blockers`. Automatic claim-drift and Conductor
state validation pass. The final review cross-checked requirements, design,
plan, source coverage, rights, recovery and historical publication claims
against the receipts and live phase issues/PRs. No code defect was identified.
Missing implementation/evidence remains across 31 plan tasks, rights/source
decisions remain unresolved, and external publication/collection mutations
were not repeated. PR #647 is merged; phase issues #209, #210, #211, #213 and
#215 remain open. See `final-review-20261006.md`. The final documented tree
passed `./scripts/validate.sh`: 7,490 tests passed, 10 skipped, 97.77%
coverage against the 80% floor; all configured schema, parity, mutation,
security and supply-chain gates passed. The whole track is not complete.

## 2026-10-06 — Vote Health 2025/26 Supplementary summary self-review

- The new profile binds source identity to the retained Bronze SHA-256 and
  official locator; exact period, document page count, page span, headings,
  expected labels and row order fail closed on drift.
- Raw tokens, source labels, unit label, field coordinates and page disposition
  remain preserved. The dash token is represented as null in numeric fields
  while its raw token remains in lineage. No amounts are recomputed or joined
  to other editions.
- The operation profile is allowlisted with exact source vintage/hash and the
  committed receipt schema was regenerated and checked against the runtime
  contract. Two integrated clean-room builds match the retained Silver package;
  the receipt confirms Bronze unchanged.
- Rights remain `not_evaluated`, and publication was not performed. The whole
  recovery receipt remains `partial_with_blockers`; this slice does not close
  source census, cross-source reconciliation, complete Platinum, or track
  completion.
- Focused tests passed (526 passed, 10 skipped); the profile module has 100%
  line and branch coverage. `./scripts/validate.sh` passed with 7,555 tests,
  10 skips, 97.67% overall coverage against the 80% floor, and all configured
  schema, parity, mutation, security and supply-chain gates. No actionable code
  defect is currently observed. Whole-track recovery remains partial and its
  final review gate remains open.

## 2026-10-06 — Vote Health 2013/14 Supplementary category-total review

- The source object matches the captured census SHA-256, recorded locator and
  44-page PDF identity. The parser is pinned to the exact page span, edition,
  table headers, six row labels and order; it preserves the three printed
  columns and raw adjustment tokens.
- Fact values, 18 direct field lineage rows and five page dispositions match
  the source extraction. The local Silver package matches two independent
  Bronze rebuilds; Bronze is unchanged.
- Focused tests passed (523 passed, 10 skipped); the new adapter has 100% line
  and branch coverage. `./scripts/validate.sh` passed with 7,566 tests, 10
  skips, 97.68% coverage, and all configured gates.
- The census has a recorded Treasury CC-BY-4.0 entry, while fact-level rights
  remain `not_evaluated`. Other tables/pages, comparability, publication and
  track completion remain outside the claim. No actionable defect was found.

## 2026-10-06 — Vote Health 2014/15 Supplementary category-total review

- The source hash matches the captured census record; the adapter verifies the
  official locator, vintage, 38-page PDF identity, exact page span, headings,
  seven labels and source order before writing.
- Seven facts preserve the three `$000` columns, source row labels, raw tokens,
  21 direct field-lineage records and five partial-page dispositions. The
  persistent output matches both clean-room Bronze rebuilds, and Bronze is
  unchanged.
- Focused tests pass (520 passed, 10 skipped); profile module coverage is
  91.67% against the 80% floor. `./scripts/validate.sh` passes with 7,573
  tests, 10 skipped, 97.66% overall coverage, 56 schemas/46 representative
  documents, 9/9 parity, and mutation, security and supply-chain gates green.
- The captured census records the Treasury licence notice; normalized-fact
  rights remain `not_evaluated`. No cross-edition, Gold, federation, publication
  or whole-track completion claim is made.

## 2026-10-06 — Vote Health 2015/16 Supplementary category-total review

- The source hash matches the captured census record; the adapter verifies the
  official locator, vintage, 46-page PDF identity, exact page span, headings,
  seven labels and source order before writing.
- Seven facts preserve the three `$000` columns, source row labels, raw tokens,
  21 direct field-lineage records and five partial-page dispositions.
- Focused tests pass (521 passed, 10 skipped); profile module coverage is
  91.67% against the 80% floor. Integrated recovery matches persistent Silver
  and leaves Bronze unchanged. `./scripts/validate.sh` passes with 7,580 tests,
  10 skipped, 97.64% overall coverage, 56 schemas/46 representative documents,
  9/9 parity, and mutation, security and supply-chain gates green.
- The captured census records the Treasury licence notice; normalized-fact
  rights remain `not_evaluated`. No cross-edition, Gold, federation, publication
  or whole-track completion claim is made.

## Analytical context reconciliation — 2026-10-16

Self-review found three stale-contract failures in the first full harness: the
register digest pinned by the current census, the consequent census error
assertion, and an obsolete test requiring uncaptured population values.
Resolved current evidence closure through the census, source-health projection
and recovery pin; refined the existing register guard to distinguish quarterly
leads from the captured annual series and receipt-bound policies. Created a
newly dated source/measure review instead of rewriting historical receipts.
The 122 focused checks and required full harness now pass. All actionable
findings in this reconciliation slice are resolved. Deflator choice, broader
cross-family comparability and rights remain scoped open; hosted PR checks
remain the delivery gate.

### PR #688 correction — 2026-10-17

Resolved the two P2 findings in the current review's period fields: both now
name their implemented CPI/population policies and scope remaining selections
separately. Also distinguished Stats NZ GDP source projections from the
unselected Stats NZ denominator policy. The existing test now ties both period
fields to the pinned policy receipts. All 36 source/measure checks and the
format/lint/Conductor gates pass. Historical receipts are unchanged; exact-head
hosted assurance remains required before merge.

## Canonical Gold named queries — 2026-10-17

Reviewed M-10/M-13/M-15 and AC-08/AC-11/AC-13 against the fixed product registry,
closed CLI/MCP boundary, payload fixity/schema/count/nullability checks,
predecode bounds, disabled external access/spilling, deterministic order and
exact typed values. Native acceptance found host-dependent timezone rendering;
resolved by restoring the validated Arrow schema after SQL. The existing test
now asserts UTC timestamps and 131 integration checks pass. ICU loading was not
enabled. Two native builds and every product's direct/CLI/MCP readback agree;
Budget/Pharmac classification and revision qualifications remain explicit.
Full repository validation passed on implementation `ff91c196` with 7,693
tests/10 skipped and all later gates green. Remaining gates: exact-head hosted
PR checks and protected delivery. Broader Gold reconciliation and final track
review remain open; no unsupported semantic equivalence is inferred.

## Canonical Gold metadata — 2026-10-17

Reviewed full-table versus capped-query coverage, exact schemas/tokens, package
fixity and resource bounds, no date inference, immutable input inventories,
closed paired CLI/MCP inputs, graph offline access, and rights/publication
states. Resolved the retained card-indexing error and schema-evolution finding:
canonical metadata now uses separate v4/v2 schemas; original v3/v1 schemas and
Fiscal/Budget bytes remain unchanged. Native proof covers all 13 recordsets and
exact installed CLI/MCP receipts. 92 focused checks, typing/lint, schema and
Conductor validation pass. The full repository harness passed on `b2fde77e`
with 7,698 tests/10 skipped and all later gates green. The remaining delivery
gate is protected exact-head hosted assurance. This does not close broader metadata standards,
federation approvals or final Health review.

## Fresh canonical recovery wiring — 2026-10-17

Reviewed the actual retained-Silver input dependency and replaced it only in
the canonical reconstruction path. Locked source/token definitions preserve old
observation identities; source pin preflight/postflight and exclusive writes
protect originals and prior attempts. Each Gold build uses its corresponding
fresh domain inputs; query and metadata reconstruction are now included. New
adapter metadata remains evidence, not a value replacement or forced old hash.
Twenty focused checks pass. Native integrated assurance, whole-repository
validation and protected exact-head delivery remain pending. Other retained
comparison evidence and unsupported source/rights/standards gates are not
relabelled as completed clean-room products.

Native two-run recovery passed with unchanged Bronze, matching fresh inputs and Gold, all bounded query readbacks and 13-recordset metadata reconstruction. Independent actual-receipt validation caught a filename-schema gap hidden by the original synthetic fixture; the native-shaped JSONL fixture reproduced it red, and the narrow schema correction now validates both real receipts. No production-code or input change followed the native run. The cancelled queued harness never acquired the broad slot or executed tests. The full corrected-tree harness and hosted checks remain pending; this review does not close the whole recovery or track gate.

Full local `./scripts/validate.sh` passed on clean
`7946b24392d1053b76d3ef77cbc49263a08b3f23` with exit 0 (durable
`validation-2.log`/`validation-2.exit` outside Git): 7,708 passed, ten skipped,
97.44% coverage against the 80% floor, 60 schemas/50 representative documents,
parity and all mutation/hygiene/audit/licence/secrets/SBOM gates. SBOM has 113
components; external CDX validation was explicitly skipped. The bounded fresh
canonical-input recovery task is now complete locally; broader Phase 9 remains
in progress. This result bookkeeping changes only track documentation/evidence;
protected exact-head hosted validation and merge/prune remain pending.

## PR #691 query oracle correction — 2026-10-17

Accepted review `discussion_r4297628595`: subset membership and row counts cannot
prove the required ordered/truncated slice. Independent typed-column sorting now
checks the exact sequence, with adversarial wrong-subset/reversed-order cases
and numeric/null/list/duplicate semantics. Source and Gold builders are unchanged.
The old native receipt remains historical weaker evidence. Fresh targeted native
canonical/query verification, repeated full harness and corrected hosted checks
are pending; the review thread stays unresolved until the fix is verified.

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

Reviewed exact official links, URL-derived source identities, publication-native
DEFU naming and release dates. Publisher file size and licence text are metadata
observations; actual hashes/bytes and item rights remain unqualified. The
annex/glossary reader discrepancy is preserved rather than silently assigning
unobserved tables. The Core Crown period observation is bound to the separate
GAAP PDF reader result, with accounting and native-layout caveats. A new dated
review preserves earlier receipts, existing approved policies and capture counts;
all 30 historical editions remain pending. Forty-one focused checks and static
checks pass; full/hosted validation is pending. No donor or original changes.

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

## BEFU 1998 source census — 2026-10-17

Reviewed all ten official release hrefs and retained exact publisher labels.
GAAP Crown and SNA Central Government measures remain separate; SNA Budget
labels do not inherit GAAP Forecast/Projection status. Reader footer/header
discrepancies remain native-layout gaps. The Budget 1998 Supplementary notice
has no exact fiscal-period/object binding and does not mutate the referenced
1998/99 captures or their rights. All 76 prior resource rows and ten prior
reviewed series are unchanged. Forty-two focused checks pass; full/hosted
validation remains pending. No scope, native-fixity or admission completeness
claim is made for the 30-edition inventory.

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

## BEFU 1999 and year-end dispositions — 2026-10-17

Bounded self-review checked publisher link titles against browser readback,
source identity, rights wording and table-specific status definitions. The
2019 contents typo remains in the publisher-title field; the release stays
1999. The Fiscal header's forecast/projection labels are not replaced by GAAP
definitions. No numeric cells, native hashes/layout claims, ISO currency or
cross-basis relationships are admitted. The page-level CC BY 4.0 statement and
historical Crown copyright wording remain separate, unadjudicated evidence.

Beehive's dated publication statement and Parliament Appendix 1 corroborate
December 1998 publication but supply no qualified original locator. Parliament
note 2 reports December 1999 nonpublication. Each has its own reason-coded
record, null original URL and explicit prohibition on replacement admission;
no inferred BPS/PREFU substitution, whole-edition closure or capture mutation.
All 86 earlier resource objects and twelve reviewed series compare unchanged.
The prior dated review is preserved. Full local and hosted gates remain pending.


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

## Remaining locator gaps and component identities — 2026-10-17

Bounded self-review preserves all 93 earlier resource objects and twelve
unaffected reviewed source descriptors exactly, plus unchanged captured-census
and prior dated review bytes. Vote Health coverage wording in the new review
is corrected against the existing structured inventory. All 131 primary source IDs/URLs are unique. At least one locator
per scoped year does not establish complete per-edition families: the complete
edition list remains empty and every prior capture/rights boundary remains.
Four related 2000 links remain discovered with content-scope review pending.

Publisher labels, reader identities and dates are separate observations. The
2003 Financial Information/Summary Tables discrepancy, 2004 workbook year
mismatch and 2006 signed-date anomaly remain explicit. Issue dates are declared
as landing-release metadata, never verified native-document dates. Budget
2026 Treasury hrefs are not assumed byte-identical aliases of existing
Budget.govt.nz captures. No numeric values, currency, header relabelling or
cross-basis joins are admitted by the new historical descriptors.

Component-index records distinguish central-government LCI salary/wages from
PPI inputs and preserve social-assistance scope, exact table/dimension codes,
units/base, source update dates and historical-method vintage. No LCIQ/PPIQ
selector is guessed; full export references, numeric coverage/flags, weights,
GST/period alignment, native capture/fixity, rights and policy remain pending.
The agricultural PPI base exception and finance/FISIM nuance remain scoped.
No whole-Vote-Health deflator, QES substitution or numerical export is approved.

Before that wording correction, Conductor independently confirmed preservation
of all prior resources and source descriptors, unique identities, unknown
fixity/rights for additions,
and unchanged negative completion flags. Current review closure and local
focused checks verify 41 pinned evidence files. Full harness and exact-head
hosted delivery remain pending; this does not close the Health track.


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


## 17 October 2026 — capture cohort inventory self-review

- Preserve original 143-row aggregate and individual request/capture/census
  snapshots; derived output pins every input without rewriting any observation.
- Group by exact URL, not source ID or payload hash; retain aliases and revisions.
- Keep 76 legacy request-binding gaps explicit. Two original bare request shapes
  are accepted only as requests, not weakened census documents. The 2011/12
  census already matches its original capture hash and requires no fabricated
  request file. Fail closed on mismatched resume request, source URL or digest.
- Separate metadata projection from 84-object native fixity proof and from WARC,
  rights, analytical admission and whole-corpus completeness.
- Builder uses exclusive output and never modifies inputs or native payloads.
  Schema gate covers the committed product; focused contracts rebuild it from
  retained metadata alone. Full harness and hosted assurance remain pending.


Redirect review finding resolved locally: source identity follows the verified
original request, while the raw result retains its observed final URL. Two
requests sharing a destination or payload remain separate. Missing/mismatched
success hashes and ambiguous request IDs fail closed. Failed captures preserve
the capture tool's actual no-result-hash contract. Two red regressions preceded
the fix; no retained inventory bytes or native proof changed. Full corrected-tree
assurance and hosted delivery remain pending.

Conductor independently reviewed the corrected source against both producer
branches and found no blocking finding. Reviewed module SHA-256: `e1980ec253178f10f8ec3164deafa97c4b81657194c8b71c03755d343b9971da`; tests: `738f89a411c373975ef077dad262560b24a2a090f206ad6d65086457545d53ca`. Focused final checks: 69 passed; strict typing and Ruff pass.


## PR #697 automated review corrections

Two P2 findings were valid: a supplied request could still affect legacy
identity without a verified resume binding, and explicit CLI request arguments
could be silently omitted or their names selected by input order. Four red
regressions reproduce these contracts. The correction rejects supplied legacy
requests unless the resume contract/hash bind, indexes all candidate logical
names without overwrite, and rejects ambiguous/unused explicit requests before
output. Reversed alias argument order produces the same fail-closed result.
No source/census/manifest or inventory bytes changed; native CAS proof is reused.
Current-head full assurance, hosted checks and actual thread resolution pending.


## 17 October 2026 — distinct Addition census review

- Preserve native request/manifest bytes and original ordinary Supplementary;
  new inventory retains all 152 prior resource rows exactly. Distinct source
  URI/form is not another fiscal year or a replacement edition.
- Bind new identity to the qualified CAS/WARC verification; explicitly retain
  the external wrapper failure and subsequent verification-only success.
- Existing 84-source proof is reused with exact identity-set accounting; no
  repeated native reads or expanded WARC/rights assurance claim.
- Separate the two sampled five-column layouts by source/table headers and
  roles. All seventeen other pages and numeric semantics remain unqualified.
- Reuse the production builder/schema; 24 actual inputs, two byte-identical
  builds and the new schema fixture supply metadata verification without
  adding coverage-only tests. Full frozen-tree validation and PR delivery pending.


## 17 October2026 — operational overview bridge (in progress)

Self-review requires actual DispatchResult use, three native Parquet byte parity,
original losses retained and explicit compatibility projection. New verifier
requires an externally supplied manifestSHA, checks a closed manifest and exact
regenerated expected selection/context/losses, and checks all three files against
both manifest hashes and regenerated canonical table hashes before returning
provenance. Producer readback uses its own in-memory expected result; later
recovery cannot derive the authority pin from untrusted input. Existing accepted
outputs/direct APIs and2002 ownership remain untouched. Native proof and full
exact-head assurance are still pending; no phase completion claimed.


Operational native proof completed0 on clean276a8225 under the actual shared
guard:14 profiles,209 facts,42 reference Parquet files per repeat, two identical
new manifest sets and70 observed common dispatches with direct normalization
forbidden. All original/reference files were independently SHA-checked and
remained unchanged. See [scoped proof](./overview-operational-dispatch-20261017.md)
and [run inventory with retained manifest pins](./overview-operational-dispatch-20261017.json).
Focused545 passed/10 skipped, Ruff and typing passed. Full final-tree harness
is pending. No general recovery-profile or phase-completion claim.


PR #699 review finding `PRRT_kwDOTo2MOM6tb4vU` is valid: output under a
symlinked ancestor passed the leaf-only writer preflight, then readback rejected
the ancestor after four files were created. The real directory-symlink test
failed as expected (target/output left behind;1 failed in8.96s), preserving
external `red-review-1.log`. Writer and readback now share the same explicit
ancestor-symlink refusal before parsing/writing. No path resolution, generic
writer-policy weakening or adversarial filesystem-race guarantee introduced.
Earlier full/native passes remain historical evidence; coherent-head repeat
validation and thread resolution are pending.


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


## Two reviewed forecast common adapters — implementation review

Independent Conductor static review found no blocking issue in the inspected
parser/factory/registry refactor. Only two versioned successors register; legacy
generic profiles remain excluded from registration and all four native APIs
retain their source validation, default writes, partial status and receipts.
Common records project unchanged nullable canonical fields, preserve60 lineage
entries per full successor and account for every non-normalized cell plus
excluded sheets. Context cells stay accounted even when their amount is
rejected. Adapter selection is not operation success. Native proof, full
exact-head harness and hosted delivery remain pending. No claim closes M07/AC03
residuals, current operation manifest adoption, rights or analytical gates.


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


### 2026-10-18 — Historical adapter review boundary

The native extraction body, schemas and manifest values are unchanged; the path
wrapper retains context validation and bounded regular-file admission. The new
closed registration uses exact Fiscal2024 bytes and explicit context. Complete
cell descriptors include raw JSON and record associations; native lineage
context fields remain linked through corresponding fact IDs. Other vintages
and shared Fiscal2025 profiles are outside this registration. Focused contracts
compare complete native rows and warmed dispatch under Python file-API denial.
Registry checks compare stable configuration rather than newly bound callable
identity, respecting existing sorted output. Native/full qualification remains
pending; the replay discloses dependency initialization before dispatch denial.


### 2026-10-18 — Historical code-evidence dependency reconciled

Conductor independently confirmed the full1 failure and the sole drifting
census dependency, then released the terminated run's freeze for a bounded
repair. The historical parser refactor changes source code identity while its
four native output files remain byte-identical. Retain the old census binding;
the current census changes only historical.py's SHA256 to1af61ede62d2cf29eff896381c186688efadc30811361bd3f9ec21db5eb5638c.
No validator, regex assertion, source observation, denominator, rights,
qualification or join policy changes. Existing28affected tests pass; producer
and tests still match the native-qualified679a03a4 tree. Full2 is required on
the reconciled metadata head; native1 remains valid without repetition.


### 2026-10-18 — Historical full2 review

Conductor independently verified actual full2 exit0, clean780f3040, all original
check pins and unchanged native-qualified producer/tests/runtime. All32stages
completed; the census failures are resolved with evidence versioning, preserving
all series and rights/qualification fields. Native106/1143/1503/six-sheet parity
and full7954 qualification support this closed Fiscal2024 adapter only. Other
vintages, whole-worksheet semantics, mappings and rights stay separate. Final
recording changes documentation only; hosted checks and protected delivery must
still pass on the resulting PR head.


## Budget 2024 source and revenue profile review — 2026-10-18

- Actual definitions establish literal thousands and June year ends. The profile
  retains unknown ISO currency and period starts, with source-separated revenue.
- The 1,004 occupied rows exceed the legacy bound. The fix gives the exact
  captured hash/official locator and 2024 transformation their own 1,004-row
  bound, preserving 2025/2026 limits. Binding, boundary and common-dispatch
  tests pass; actual source accounting includes row 1,005 without truncation.
- Both embedded images are identical CC BY badges. Native Intro notices retain
  emblem restrictions; the source declaration is evidence, not blanket legal
  or publication approval. Originals and historical observations are unchanged.
- Two actual-source builds match in all four files, and common dispatch matches
  facts, lineage and losses. All 32 original harness stages pass on 64d40613.
  Subsequent edits contain only track receipts/documentation, checked separately.
  See [qualification](./budget-2024-revenue-qualification-20261018.json).
- No actionable local finding remains. Exact-head hosted checks and protected
  delivery remain pending. The 2024 expenditure profile, wider census and
  final track review remain incomplete. No quality or branch gate is weakened.


### Product-entry finding — resolved locally; hosted delivery pending

Conductor found the missing 2024 source-operation registry/vintage/schema entry.
The correction preserves the source hash/locator guard before parsing and the
closed result schema. Four focused routing/refusal cases and schema equality
pass; the broader source-operation/revenue suites pass 595 cases (10 skipped).

Actual retained-source qualification exercises CLI preflight, MCP JSON-RPC
preflight and explicit CLI writing. Preflight leaves the target absent; all
four written files match the previously qualified package. The corrected head
89fdb3c9 passes all 32 original harness stages with 8,038 tests passed, 14 skipped.
The source and earlier proof remain unchanged. Actual process termination,
clean head/tree/pins and the released kernel lock are independently verified.
See [entry qualification](./budget-2024-source-entry-20261018.json).

The local product-entry finding is resolved. Fresh hosted checks and protected
delivery remain pending; earlier 9f250a41 successes describe that earlier head.
No rights, currency, period-start, Gold or publication gate is promoted.


### 2026-10-18 — Budget2024 expenditure implementation review

A separate source profile avoids silently changing the qualified legacy v1
package contract. Source digest/locator/vintage are required before parsing or
output; the closed operation schema exposes the same reviewed profile. All17
columns and source-row dispositions are retained; parent/category fields are
not aggregated. Native A means annual OR permanent legislative authority; M
means multi-year. Neither establishes a period start. Currency and rights
remain unknown/not evaluated. Original OOXML amount tokens establish exact
values independently of the caller Decimal precision. Other worksheets remain
inventoried with explicit exclusions. Focused/static review found no further
actionable defect; actual-source and full qualification are still required.


### Expenditure qualification review — native passed, full hosted pending

Actual source confirms all17 columns,244facts/6100lineage, complete6645row
accounting, byte-identical fourfile packages and CLI/MCP/common-dispatch parity.
Currency/period-start/classification/rights holds remain intact. Three local
full-harness attempts failed on unchanged timing checks or the original cap;
failures are preserved and no check is suppressed. A fail-fast legislation
allowlist opportunity was identified but remains outside this focused change.
Run the identical required checker on clean hosted runners; keep allseven
exact-head checks and review resolution before protected merge. Do not claim
local full success or mark the wider track complete.


### 2026-10-18 — Next release boundary

Budget 2023 uses its own registered URLs, issue/update dates and June-year
labels. The page's licence declaration does not substitute for native notices
or redistribution assessment. No 2024 row bound, unit, source hash or numeric
profile is applied to uninspected 2023 bytes. Retained-evidence matching is
explicitly limited to four inventories and first headers in the primary WARC
directory. The next action is bounded preservation through the existing core.


Budget2023 review: exact decoded definition equality verified; JSON display escaping must not become source text. Closed schema and unknown-vintage fixture drift repaired. Source binding remains fail-closed. Native repeat/full delivery gates remain open.


Budget2023 revenue: original full harness passed all32stages. No suppression, timeout/coverage change, source mutation, netting, inferred currency/start/rights or publication. Native producer-to-full delta is documentation only. Required hosted checks and protected delivery remain open; broader track is incomplete.


PR719 automated P2 receipt status inconsistency: corrected the top-level status to distinguish passed local assurance from pending protected delivery. Detailed producer evidence and facts unchanged.


2023 expenditure implementation review: shared parser replaces edition constants without copying its row logic. Public2024defaults and source binding remain separate; old legacy profile refuses2023. Reviewed B3/period map is explicit lineage only for2023, leaving2024output lineage unchanged. All native/2024byte/full/hosted gates remain open.


2023 expenditure native review: both2023builds and actual entry points agree, and the2024default package is byte-identical to its prior qualified oracle. Context/rights/Gold exclusions remain explicit. Source-native qualification is complete; full and hosted assurance and protected delivery still required.


Local full review: completed five fast stages, then test timeout at the unchanged900s cap. Preserve failure evidence and make no local full-pass claim. All new/existing expenditure cases passed before timeout and actual-source/2024byte qualification remains valid. A reviewablePR may proceed under the original run-before-PR contract; protected merge still requires unchanged all32stage hosted success on all three platforms, seven exact-head checks and resolved findings.


PR720 P2 census scope finding: the current observation_scope now includes both separately qualified native profiles. Counts, explicit rights/Gold/join exclusions and qualification references agree; no broader admission or full local pass is claimed.


PDF layout review: encryption metadata alone did not establish inaccessible page content. Normal reader access is used with no credentials; genuinely locked inputs keep encrypted_pdf. Dictionary subscription resolves real indirect metadata references. Synthetic contracts and downstream report checks pass; actual59-PDF cohort and prior56-recorded-layout parity must be verified before full assurance/delivery.

- PDF cohort self-review: all 56 prior recorded rows match exactly; three default-readable sources add geometry-only descriptors. Required-password fixture remains excluded. No source recapture, rights claim or financial extraction. Native qualification passed; full/hosted delivery pending.

- PDF final local review: original all32stage harness passes. Source-health control explicitly separates pre-existing CPI context changes from the3PDFstate delta; both schema versions repeat and CPI449label evidence is preserved. Old reports/originals unchanged. First stale-input comparison failure preserved. No actionable code finding remains; exact-head hosted checks and protected delivery are still pending.

- PR721 final delivery review: exact-head7checks and all32stages on all3platforms verified;0unresolved threads/CodeQL alerts. Normal protected merge ancestry/equal-tree/zero-unique guards pass. Stale remote-tracking cleanup assertion corrected after fresh remote-absence proof. Primary and all original/native evidence retained.

- Budget2022 capture review: distinguish complete workbook CAS/WARC proof from terminal page403; do not repeat successful files or weaken access controls. Source page web metadata is observational only, without a native page-transport receipt. Conductor consulted; independent source-native work continues.

- Budget2022 native review: actual layouts fit the existing literal named-column contracts, but require independent edition/hash/B3/period/row profiles. Decode JSON display strings before comparison; all existing shared non-edition definitions match. Preserve earlier-edition output bytes, unknown currency/start and rights holds. Page403 is separate from eligible local source inspection/normalization.

- Budget2022 implementation review: source identity/row/period metadata is edition-specific, while parser logic is reused. Native literals independently matched; two added schema profiles leave the entire prior schema unchanged when removed. Retain first failure logs, including wrong copied locator and schema/unknown-year fixture drift. Do not claim actual-source or full qualification from focused tests.

- Actual-source review: both 2022 native profiles pass with zero rejected rows, complete row accounting, all original columns, semantic holds and exact entry-point parity. Earlier 2024 expenditure and 2023 revenue products reproduce byte-for-byte. Terminal processes and all frozen inputs verified; no original recapture or rights promotion. Full assurance and protected delivery remain open.

- Full-attempt review: preserve original900s local test cap at99% with no invented pass or coverage result. Native/current/old-product byte proofs and source/code/runtime pins remain unchanged. Use the established run-before-PR path with explicit disclosure, all32stages on3clean platforms,7exact-head checks and resolved review before merge. No branch/gate weakening.


- PR722 review correction (routing): all seven original-head checks passed,
  but unresolved thread PRRT_kwDOTo2MOM6tqRuj correctly identified missing
  Budget2022 routing in the shared registry and legacy workbook normalizer.
  Regression reproduced with empty common records (1failed/1passed/4deselected);
  route the exact edition through its pinned registration/normalizer. Keep the
  legacy generic adapter fail-closed and all currency/start/rights holds.
  New affected tests, actual-source route parity and full/exact-head hosted
  assurance are required before resolving the finding and protected delivery.
  Earlier native and local timeout receipts remain historical evidence.


PR722 delivered: all7exact-head checks/all32hosted stages per platform; merge95f9f638 verified fetched main/head ancestry/equal merge tree/zero unique commits and patches/clean. Topic local/remote/tracking absent; one primary/CAS/runtime/proofs retained. See budget-2022-delivery-20261018.json. Local full2 remains124 with2observed failures, not a pass. Serial/instrumented probes and140unchanged affected-module tests distinguish startup sensitivity from proven FIFO rejection; earlier timeout location unproven. Conductor advice requested, no approval claimed. Next bounded Phase8 task isolates input-spec inspection from plot/product startup without widening limits or changing product bytes.


Reader startup implementation: dependency-boundary red reproduced plotting import during plain input inspection. Initial local import deferral still reached plots through eager MCP schema projection; preserve intermediate failure. Native Context Gold now imports rendering only at the existing export call; operation canonical/render imports stay in product construction. All41focused tests pass316.31s, Ruff/format pass. FIFO10s/full900s/80%floor unchanged; no product format, numeric rules, rights, joins or publication changed. Actual retained-product/native and full/protected qualification remain pending; see context-reader-startup-implementation-20261018.json.


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

Final static review found two functions at53statements against the existing50
limit after the request-policy/inventory integration refinement. Extracted
source selection and an inventory assertion helper; no rule suppression or
threshold change. Ruff and strict typing pass after refactoring; focused
capture/recovery replay is recorded separately on the final implementation.


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


### PR727 final delivery reconciliation

Exact immutable metadata-candidate adjudication is delivered through protected
merge cdbc3652 after full original local assurance and exact-head three-platform
hosted checks. No scanner scope, protection, timeout or coverage change.
Archive-candidate coverage does not qualify rights, periods, units or legacy
workbook structure. Next reader must disclose unsupported structure and cached
value semantics rather than fabricate XLSX-equivalent inventory.

Legacy reader review: merged-range output is independent of rectangular cells. Add a cumulative20,000 merged-range limit before projection; a fixture-backed existing rejection parameter is red before implementation. Keep the post-load allocation limitation explicit.

Native BIFF8 inspection succeeded for all32source hashes without changing Bronze or granting semantic/rights admission.210worksheet observations and bounded5x12 previews do not establish complete period/unit/definition coverage. Preserve the original qualification checkpoint; append later assurance/delivery receipts separately. No external publication action repeated.

Legacy-reader local gate complete: real synthetic reader contracts plus native32candidate repeats and original full32stage harness pass. Review found and fixed independent merged-range output growth before native/full qualification. No existing XLSX behavior,30historical donor dispositions, rights policy, coverage floor, stage caps or protections changed. Producer checkpoints remain immutable and wider track gates stay open.

Reproduced contract defect: synthetic BIFF8 empty sheet title is accepted by xlrd and emitted as inspected despite the nonempty-title schema. Minimal fail-closed rejection is verified with one existing real-reader rejection parameter. This repairs the declared output contract, without broader format validation or a coverage-target change. Original79dc7ec0 all32 hosted successes remain preserved; corrected code must receive fresh assurance before merging.

The reproduced nonempty-title contract defect is fixed with a3-line rejection and one existing real-reader test parameter. Valid-source stdout hashes match both preserved repeats for all32candidates, and fresh original full assurance passes. No additional general Excel validator, scanner exemption, test function, dependency or policy change was introduced by the correction. Keep original producer receipts immutable and require fresh final-head hosted checks.

### 2026-10-20 — Budget2021 bounded profile review (delivery pending)

The exact workbook preflight covers headers and all Explanation cells in bounded windows twice. Coordinate changes require explicit lineage configuration: expense defaults remain identical for2022–24, while2021 revenue introduces B4 rather than misreading B3=Overview. The existing named-column fallback must refuse2021; pinned wrappers and source operations/common registry must select the reviewed profile. All are wired in this slice. No source totals, currency, rights, comparability or whole-phase completion claim is admitted. Native repeat builds, prior-package equality, CLI/MCP preflight and original full validation remain gates before PR delivery.

Budget2021 native review resolved the coordinate, source-row-bound, fallback-routing and operational performance findings. The preserved pair produces329 expenditure/64 revenue facts with all6425/1014 rows dispositioned and8883/1024 lineage rows respectively (machine receipt is authoritative for exact counts). All four derivative hashes match each repeat and operations route; common dispatch facts agree. Both CLI/MCP modes pass twice under30s, and six prior2022–24 packages match all24 hashes. Existing cache-state/type tests now also require bounded streaming under an exaggerated declared dimension; no cached value admitted as fiscal truth. Native1/2/3 timeouts and all diagnostics retained. Local original full validation, hosted exact-head assurance and protected delivery remain open.

The pre-merge copied-context scope finding is fixed with a shared active-owner flag and an extended existing regression (no extra cases). Native5 requalifies all eight source packages and all32 output hashes equal native4; both2021 CLI/MCP entry modes pass twice under unchanged30s. Source-byte preservation, full inventory/cached-state checks and provenance remain unchanged. Full3 and new-head hosted delivery are required; earlier-head CI is insufficient for this lifecycle correction.

### 2026-10-20 — Budget2020 bounded profile review (qualification pending)

Use expense source SHA d6a4f001 and revenue5b3fc350 with exact2020-05 locators and edition-specific Explanation cells. Headers and definition text match the shared parsers but physical cells differ from2021. Prospective periods follow the literal introductions (2016–2019 Actuals/2020 Estimated Actual/2021 Main Estimates); source-native currency/start-date/rights/join holds stay unchanged. The row bounds6303/1026 count source records, excluding worksheet headers. Common registry, legacy normalizer, pinned-source fallback refusal, source operation schema and CLI/MCP dispatch are all extended together. Two new contract cases verify periods, exact lineage, competing dispatch, repeat/operation bytes and wrong-observation refusal. Native complete-row accounting and prior-package hashes remain open gates.

Budget2020 native1 resolves the row/period/lineage/routing concerns:318 expense facts/8586 lineage from6303 rows,62 revenue facts/992 lineage from1026 rows; zero rejected/blank rows. All four output hashes match repeats/operations, common-dispatch facts agree, both CLI/MCP modes pass twice under30s, and all32 prior2021–24 output hashes agree. All5569 frozen pins stable, owner85798/group absent and independent lease free after actual exit0. Original full assurance and protected delivery remain open.

### 2026-10-20 — Legacy definition census review

All 32 sources have every Explanation cell accounted for and complete raw headers; decoded stored/cached text is metadata evidence only. Reviewed period years follow literal source descriptions, and text digests preserve Unicode/spaces. Nine missing amount scales remain pending after complete header checks. Budget 2014 revenue retains the contradictory Budget 2015 statement at B10; no silent correction or profile binding. Rights keyword absence is scoped to Explanation, never a publisher-policy or whole-workbook claim. Earlier producer receipts remain immutable. Two private projection failures were recorded before any public write: an older exit-field name and an Explanation-only record selected as header evidence. The corrected projection explicitly checks old/new native schemas and reuses the original complete 2010 revenue raw header. No runtime/test/schema/dependency changes; original full validation and exact-head hosted delivery remain required.

### 2026-10-20 — BIFF stored-value implementation selected

Conductor advice identifies a distinct stored-integer evidence class; an integer from xlrd is not a source lexical token. The native2019 preflight contains both RK floating-point and integer encodings, requiring exact handling of both. The qualified fictional CFB fixture includes NUMBER, RK, MULRK scaling/fraction and an integer-valued formula cache to exercise real encoding/refusal boundaries. Plan/design precede code. Complete native companion tables and witness-aware downstream validation prevent a side format that silently loses provenance; old literal consumers remain unchanged. No numerical or rights admission is claimed before production contracts and native qualification pass.

BIFF decoder primitive review: exact float ratios avoid display/text round trips; RK sign/scaling are explicit, formula kinds are refused, only immutable byte payloads/exact integer record-type arguments are accepted, fractions/nonfinite/overflow reject without rounding. This function decodes a previously classified encoding and cannot prove source origin; the upcoming witness resolver must bind it to source bytes and cell/member identity before admission. Seventeen meaningful encoding/refusal cases and static checks pass; the complete source-adapter task remains in progress.

Witness-core review found a typed-wire defect: dataclass equality alone accepted a float record kind and boolean coordinate/member aliases. Three observed failing cases preceded the strict per-field type/value replay fix. The fictional fixture exercises real CFB source bindings, NUMBER/RK/MULRK, formula-cache refusal, encryption/dialog/macro/duplicate/malformed/high-stream-size rejection and identity/scan caps. Original64-bit CFB directory sizes are checked because the reader exposes only low32bits. The shared byte inspector preserves the existing path reader contract. Focused59checks and static gates pass; native original replay and prior inventory byte parity remain open. No normalizer, rights or product admission is claimed yet.

BIFF numeric consumer review: source-column maps are caller-trusted profile declarations; witness metadata cannot choose its own field/coordinate. All projected numeric fields require one-to-one evidence plus numeric lineage, same source/row, exact scalar identity and fact agreement. Amounts additionally enforce decimal128(20,3) range without rounding and preserve canonical stored integer/reference. Whole-package disposition/text-lineage checks and source profile admission remain separate, pending work. No rights, currency, period alignment or aggregation claim.

Budget2019 implementation review: no fabricated source_number_token is emitted; decoded_values_json is explicitly reader-display context and numeric raw lineage is null. All selected constants replay through their exact source witnesses before Arrow construction. Numeric companion rows retain the source_object_sha256 alias needed by existing native closure validation while preserving original witness source_sha256. No shared OOXML schemas or lexical consumers were loosened; new profile IDs and schemas are separate. Invalid selected rows remain dispositioned in the parser and hold the entire native/operation admission. The witness-aware numeric projection is qualified independently; full canonical/Gold product mapping and source rights remain incomplete. Actual-source, preflight, regression package and original/full/hosted assurance remain required.


2026-10-20 bounded BIFF8 canonical/Gold self-review: requirementsM05/06/07/10/11/13/16 mapped to explicit v3 carriers, full original-to-Silver replay, canonical replay and unchanged witness companions. Source numeric bytes never become lexical tokens. All rows and definition links remain pinned; Gold performs identity projection only. Checkpoints from PR732 remain immutable. Reviewed refusal cases cover rehashed deletion of each of four Silver tables and canonical closure; actual Bronze pair repeat counts and hashes verified. Finding: redundant text coordinates nearly exceeded existing manifest read cap. Resolved by retaining full hashed lineage companion and inlining numeric lookups plus companion references; new native2 is1,401,950bytes, canonical/table hashes unchanged. Rights/currency/start-date/aggregation/comparability, nine earlier unit gaps,2014revenue edition conflict and30historical donor differences remain held. Original full32-stage harness and exact-head three-platform required checks are still delivery gates; this is not whole-track completion.

Original full1 review corrections: close v3 admission to its three actually implemented shapes; retain original unsupported source_inventory/v3 tests, update expanded recovery fixture inventories, and positively verify alternative Parquet encoding using the existing revenue fixture. No changes to CLI30s, Hypothesis health checks or stage900s limits. Focused157pass; fresh full2 and protected hosted delivery remain required.


Original full3 on2a36724d terminated124 at the unchanged900s test-stage cap: 5822observed PASSED,1observed FAILED (checkpoint property contract; no final trace before cap),71percent, no final suite/coverage summary and no all32local pass. Five fast stages passed. All4884pins stable, all captured owner/nested groups absent and kernel lease independently free. Preserve original full1 failures and aborted full2launch; no old log was overwritten. Under AGENTS.md run-before-PR contract, proceed to focused PR with incomplete local assurance explicit; require original all32stages on exact final head across Ubuntu/macOS/Windows, all required checks and resolved findings before normal protected merge/prune. This does not complete whole-track final assurance or change any threshold/deadline.

### BIFF8-inclusive bounded recovery review — 2026-10-20

[Review report](biff8-recovery-review-20261020.md) and
[native receipt](biff8-recovery-native-20261020.json) close the missing BIFF8
reconstruction and combined Gold reader-bound defects for this slice. Original
full validation/protected delivery remain pending; this is not final track signoff.

### Budget2018 source-native review — 2026-10-21

[Bounded review](budget-2018-biff8-review-20261021.md) and
[native qualification](budget-2018-biff8-native-qualification-20261021.json)
record complete source/operation/native parity and30s interface checks, with
unchanged2019 bytes. Original/full/hosted delivery is pending.2018 downstream
canonical/Gold/recovery and whole-track final gates remain open.

## 2026-10-21 — Multi-vintage canonical/Gold/recovery review

Reviewed exact trusted profile selection, edition-specific identity, complete
original/Silver replay, deterministic concatenation without financial aggregation,
companion fixity and metadata references, v1/v2 compatibility and v3 source
selection against M-05/M-07/M-10/M-13/M-16 and the bounded product contract.
Focused regression:55 passed with two existing RDF warnings; the frozen integrated
focused lane:69 passed with two warnings. Ruff passes; strict typing has zero
errors/warnings/notes. Native originals-to-products assurance passes, including
83/61-file repeat inventories, all ten exact queries and full three-package
metadata. Prior47/65/60-file inventories stay byte-identical. No actionable
implementation finding remains. Original harness/hosted checks are still required
before merge. Coverage stays at the agreed80% floor; no rights, donor-difference,
comparability, publication or whole-track completion claim is made.

## 2026-10-21 — Budget2017 source-to-products review

Reviewed the registered plan and M-02/M-05/M-06/M-07/M-10/M-11/M-13/M-15/M-16/M-18
against exact source hashes, full source statements/headers, explicit periods,
MCOA labels, the unchanged integer-witness policy and qualified local observation
context. No new decoder, dependency, source value replacement, currency, fiscal
start, rights, donor disposition or comparability decision is introduced.
Source profiles replay all rows and all four native tables; sixteen actual
console/initialized stdio preflights pass under30s with no output creation.
Prior2018/2019 source files remain byte-identical.

Existing canonical/Gold contracts consume2017 with explicit edition identity,
complete numeric/field companions and no financial aggregation or netting.
Recovery v4 explicitly admits11 fixed sources; v1/v2/v3 selectors and all
qualified output bytes remain unchanged. Scoped tests:562 pass/ten skips;
frozen integration72 pass/two existing RDF warnings; Ruff, strict typing and
69 schemas/59 representatives pass. Native original-to-products repeat, ten
exact queries and full three-package metadata verification pass on6b6c2cba.
No actionable implementation finding remains. Original final-tree harness
and protected PR checks are pending before merge; the coverage floor stays80%.
This is bounded source/product progress, not whole-track or publication closure.
