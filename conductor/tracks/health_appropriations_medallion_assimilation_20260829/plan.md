# Implementation Plan: New Zealand Health Appropriations Medallion Assimilation

## Execution contract

Work proceeds in the sequence below. `[ ]` means pending, `[~]` in progress,
`[x]` evidence-backed complete, and `[!]` blocked by a recorded gate. For each
behavior-changing task, establish the smallest failing executable contract
before implementation, then run focused green, refactor/hardening, affected
gates, self-review and evidence updates. Characterization tests that cannot
begin red must identify the observed contract explicitly.

Originals remain in Bronze throughout every phase. Silver, Gold, Platinum,
SQLite, plots, indexes and publication packages are derivatives; no task may
replace or discard an original object.

A phase checkpoint requires paired human/machine evidence, self-review,
reconstruction or recovery checks where applicable, and the full relevant
repository validation command. External gates block only their affected task.

## Phase 0 — Track activation and hosted traceability

### Review correction — current-state reconciliation

- [x] Record a substantial-milestone continuation route and unattended-run
  boundaries so implementation can resume without repeated scope prompts.
  This does not activate a scheduler or broaden publication authority.
  [M-19; AC-04, AC-16] (`3932caf`)

- [x] Reconcile the track entry page with canonical receipts and live hosted
  state; prevent status drift with a focused contract. Keep completed
  publication distinct from pending assimilation tasks and reconcile the parent
  issue with the still-active plan. [M-19; AC-04, AC-15, AC-16] (`11117f7`)

### 0.1 Reconcile the implementation baseline

- [x] Re-observe the current Archive Govt NZ head, donor ref/tree, live source
  landing pages, Hugging Face collection membership and local toolchain; append
  machine-readable receipts without changing external state. [M-01, M-19;
  AC-01, AC-04]
- [x] Verify the pinned 23-path donor inventory, 6,604,301-byte total,
  deterministic archive digest, five SQLite tables/312 rows, three scripts and
  six plots. Record any drift as a new source version rather than editing the
  baseline. [M-01, M-08, M-09; AC-01, AC-06, AC-07]

### 0.2 Establish hosted issue hierarchy when authorized

- [x] Create/link one parent GitHub issue and nested phase issues with stable
  Conductor references after the external issue-creation gate is satisfied.
  Local planning and preservation work may continue independently. [M-19;
  AC-16]

### 0.3 Phase review and checkpoint

- [x] Run automated self-review for baseline drift, unsupported claims and
  secret/restricted-content leakage; resolve findings. [M-18, M-19; AC-16]
- [x] Run the full repository harness and record the checkpoint as local or
  hosted evidence precisely. [M-18, M-19; AC-16]

## Phase 1 — Source census and format characterization

### 1.1 Source-inventory contracts first

- [x] Add failing/characterization tests for inventory schema, cutoff,
  dispositions, URL normalization, source replacement, duplicate bytes,
  unchanged observations, gaps, restricted resources and drift. [M-02, M-04,
  M-18; AC-03, AC-04, AC-09, AC-16]
- [x] Implement only the typed census and reason-coded disposition model needed
  to pass the contracts; keep it independent of payload publication. [M-02,
  M-04; AC-03, AC-04, AC-09]

### 1.2 Inventory the seed and direct official corpus

- [x] Register the 38 verified primary locators across the six remaining
  year-level gaps (BEFU 2000/2003/2004/2006 and Budget 2025/2026). Preserve
  publisher/reader label discrepancies, period and accounting/GST boundaries,
  four related links pending content-scope review, and current-capture URL
  distinctions. Add the independently observed LCI/PPI component table and
  dimension identities as discovery-only candidates, retaining unresolved
  export references, rights, native fixity, weights and policy selection.
  Reconcile a new dated review without claiming full source-family coverage
  or analytical admission. [M-02, M-04, M-06, M-11, M-12, M-18;
  AC-03, AC-04, AC-09, AC-10, AC-16]

- [x] Register the seven official BEFU 1999 PDFs and their publisher-label,
  table-status and rights-evidence discrepancies. Record source-backed,
  separate December 1998 publication/locator and December 1999 nonpublication
  dispositions without substituting BPS/PREFU documents or changing captures.
  Reconcile a new dated source-measure review, preserving prior observations
  and whole-edition gaps. [M-02, M-04, M-11, M-18;
  AC-03, AC-04, AC-09, AC-16]

- [x] Register the ten files linked by the official BEFU 1998 release,
  with native source scopes and status labels, explicit reader-layout gaps
  and resource rights/fixity boundaries. Record the separate Budget 1998
  Supplementary withdrawal notice without changing captured 1998/99 originals
  or inferring a matching fiscal period. Preserve earlier observations and
  reconcile a new current source-measure review. [M-02, M-04, M-11, M-18;
  AC-03, AC-04, AC-09, AC-16]

- [x] Register the five newly identified BEFU/DEFU 2002 GAAP, annex and
  forecast resources with exact official locators, publication-native release
  identity, period/definition evidence and explicit rights/fixity/layout gaps.
  Reconcile the historical register and current source-measure review without
  recapturing the Vote Health preflight or granting whole-edition completion.
  [M-02, M-04, M-11, M-18; AC-03, AC-04, AC-09, AC-16]

- [x] Freeze the donor tree as the seed inventory, including code, documents,
  SQLite, plots and all eight source originals. [M-01, M-02; AC-01, AC-03]
- [x] Enumerate the Treasury historical Vote Health index and all retrievable
  Estimates/Supplementary Estimates across its observed 1998–2026 span; record
  exact edition, URL, media type, rights evidence and gap disposition. [M-02,
  M-11; AC-03, AC-09]
- [~] Enumerate annual Budget expenditure/revenue workbooks, BEFU/HYEFU
  charts/core Crown expense/forecast files, the current Fiscal Time Series,
  Ministry of Health Vote Health series and Pharmac CPB series. Include Budget
  2025 seed inputs and Budget 2026 successors without assuming identical
  schemas. [M-02, M-11; AC-03, AC-09]
  Historical scope and unresolved editions are recorded in
  `historical-source-register.json`; link discovery does not establish capture.
  BEFU 2002 GAAP Series Tables are now identified as an official Crown expense
  source with June-year periods, `$ million` units, forecast/actual status and
  the page-level CC BY 4.0 statement recorded. Item-level rights remain
  unevaluated; 2002's other source families and annual Budget workbooks remain
  unresolved. This locator and period assessment are pinned in
  `source-measure-review-20261006.json`; they do not mark 2002 complete.
  Treasury's historical Vote Health index and exact 2002/03 main and 2001/02
  Supplementary Estimates PDFs are now separately registered. Fiscal periods,
  `$000` Supplementary Estimates fields, page-level rights evidence, and the
  Vote Health Service Providers merger into Vote Health are recorded; bytes
  remain uncaptured and the 2002 edition remains incomplete.
  The Budget 2026 Estimates expenditure workbook's public release periods,
  restructuring caveat, exclusion of 2025/26 Supplementary Estimates and
  publisher-declared licence are recorded in
  `budget-2026-estimates-workbook-profile-20261003.md`. This resolves only the
  release-level census for that captured workbook; workbook-native units and
  annual/source coverage remain to be verified.
  The 2016/17 Vote Health Estimates PDF now has a source-census addendum
  reconciled to its existing captured object, WARC, fiscal period and structural
  layout baseline. It does not recapture the PDF or close the wider annual
  Budget/BEFU/HYEFU/Pharmac census.
  The captured 2017/18 Estimates PDF also has a hash-pinned page-2 overview
  profile for 25 source-reported amount statements. It preserves category names,
  period and share qualifiers; page 3 is only the edition-specific layout
  check, and the remaining pages are outside this profile.
- [x] Review fix: isolate invariant legislation fixtures from generated archive
  ordering and union-algebra examples; retain all strategies, deadlines and
  semantic assertions, then verify full assurance. [M-18; AC-16; d1f2ff31]
- [x] Review fix: give historical discovery rows stable URL-derived source IDs
  and verify uniqueness without substituting locator identity for byte fixity.
  [d1f2ff31; full assurance f111dbf0]
- [~] Enumerate the exact official CPI, QES wage, population, GDP and Crown
  expense series needed for approved derived measures; reject discovery leads
  that lack a stable definition or join. [M-02, M-12; AC-03, AC-10]
  The annual June mean resident-population export is captured and projected;
  the pinned Fiscal 2025 / population-20260818 policy supports nominal per-capita
  rates for matching June fiscal years, with missing/March-period exclusions.
  The same-workbook Treasury Health/GDP and core/total Crown share policies
  and the separate household-CPI FY2025 benchmark are also implemented.
  `analytical-context-register.md` now distinguishes these qualified policies
  from source projections and remaining cross-family/deflator decisions.
  The June 2026 GDP successor workbook and Table 1 expenditure selector are
  separately captured, source-profiled, canonically projected and included in
  Context Gold, with March/June vintages separate. GDP currency, broader
  comparability and resource-specific rights gates remain scoped open; see
  `context-gold-gdp-vintages-20261002.md` and the named analytical receipts.
  Stats NZ's June 2026 labour-market summary and QES series mapping now support
  a not-seasonally-adjusted disposition for QEMQ.SASZ9A; the ISO currency and
  analytical join remain unresolved. See
  `qes-methodology-rights-review-20261002.md` and
  `price-wage-context.validation.json`.
- [x] Evaluate published aggregate Health Survey indicators as a non-blocking
  Should item; include only if a documented analytical question, stable
  time/geography contract and public rights evidence exist. [S-05; AC-10]
- [x] Complete the bounded metadata-only Health Survey assessment, recording
  a contextual question, annual/pooled and revision boundaries, public rights
  observations and the unqualified export/dictionary gate. This does not
  complete conditional acquisition or integration above. [S-05; AC-10]
  See `health-survey-assessment.md`.

### 1.3 Characterize every donor binary and derivative

- [x] Observe embedded copyright/licence notices for the three exact reviewed
  legacy workbook hashes; emit bounded hash-bound cell evidence without source
  text, original modification, network access or eligibility promotion.
  Reject unsupported/tampered inputs. [M-04, M-07, M-18; AC-04, AC-16]
  (PR #285 observed merged `5ff01ff`, seven exact-head checks; local native
  timing failure and isolated retry evidence remain retained.)

- [x] Record hash-pinned static behavior and compile characterization of all
  three donor scripts without executing their side effects. [M-09; AC-07]
  (`d26e769`)

- [x] Complete inert macro-part, external-link and opaque/embedded-part
  inventory contracts; verify no external retrieval, no payload disclosure and
  byte-exact preservation. [M-07, M-18, S-03; AC-03, AC-16] (`ee54bc9`)

- [x] Harden workbook preflight with platform-independent member paths,
  duplicate-part rejection and a cumulative cell-scan limit; verify immutable
  inputs and exact limit boundaries before expanding operational exposure.
  [M-07, M-18; AC-03, AC-16] (`b2956a7`)
- [x] Add fixtures/contracts for safe ZIP/workbook inventory, archive-bomb and
  path controls, sheet/range discovery, formulas/cached values, hidden content,
  named ranges, tables, charts, external links, macros and unsupported parts.
  [M-07, M-18, S-03; AC-03, AC-16]
- [x] Expose deterministic worksheet ranges, formula/comment coordinates,
  hidden row/column spans, scoped defined names and original ZIP part names
  through the existing bounded inventory. Preserve source bytes and keep
  cached-value interpretation distinct. [M-07, S-03; AC-03, AC-16] (`dffa310`)
- [x] Characterize formula caches by coordinate, stored type and explicit
  stored-value/error/missing-or-empty state without evaluating formulas or
  asserting cache freshness. Preserve byte identity. [M-07, S-03; AC-03, AC-16]
  (`f73d678`)
- [x] Produce a machine-readable sheet/table/range census for all seven donor
  workbooks and a page/structure census for the donor PDF, without changing
  their bytes. [M-03, M-07, S-03; AC-02, AC-03]
- [x] Characterize the five-table SQLite schema, row order/keys, types, nulls,
  values and totals as parity fixtures. [M-08; AC-06, AC-11]
- [x] Characterize the intended behavior and failure behavior of
  `inspect_excel.py`, `process_data.py` and `run_analysis.py`, including the
  known compile failure, swallowed exceptions and positional heuristics.
  [M-09, M-18; AC-07, AC-16] (`4454d75`; pinned full compile without execution,
  defect-to-replacement test map, 253 focused and 1,907 full-suite tests)

### 1.4 Decide workbook and plotting dependencies

- [x] Compare repository-compatible workbook readers and plotting approaches
  against the characterization fixtures, including formula/metadata support,
  security, licence, maintenance, determinism and performance. Evaluate
  `openpyxl` and Matplotlib but do not presume adoption. [M-07, M-09, M-18;
  AC-03, AC-07, AC-16]
- [x] Before adding a material dependency, record the accountable decision,
  amend `conductor/tech-stack.md`, update the lock, add dependency contract
  tests, and pass audit/licence/SBOM gates. [M-18, M-19; AC-16]

### 1.5 Phase review and checkpoint

- [x] Reconcile pinned donor structural inventories with adapter-context
  exclusions and explicit mapping assertions. Default unresolved, preserve
  partial-sheet remainders and legacy inventory limitations; never infer PDF
  tables, semantic normalization or phase completion. [M-07; AC-03, AC-16]
  (`3564f2b`; 107 focused tests, 144 cold mutant kills, 3,531 native tests;
  see `area-accounting.md`; hosted delivery remains separate.)

- [x] Verify every discovered item has exactly one disposition and every donor
  binary/data area has an inventory result; report uncertainty and gaps rather
  than inferring completeness. Verified 141 unique source records with exactly
  one disposition (73 captured, 68 out of scope, zero unresolved) and retained
  the bounded donor binary/data-area census. [M-01, M-02, M-07; AC-01, AC-03,
  AC-09]
- [x] Run focused format/security/property checks, self-review and the full
  repository harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 2 — Bronze zero-loss preservation

### 2.1 Bronze integrity contracts first

- [x] Add failing tests for streaming single-pass ingestion, expected-length
  mismatch, SHA-256/BLAKE3/CID identity, CAS deduplication, atomicity, WARC
  linkage, resume, interruption, unchanged/changed observations, corrupt ZIPs,
  withdrawal, restriction and tombstones. [M-03, M-04, M-18, S-01, S-02;
  AC-01, AC-02, AC-04, AC-16] Contracts are covered by the focused health
  ingestion/checkpoint tests and existing Bronze multihash, CAS, inventory and
  versioning tests. The redirected-orphan regression additionally verifies
  query-free final-URL recovery; query/fragment cases remain explicitly
  unadopted to preserve URL privacy. No tests were added to increase coverage.
- [x] Fsync the checkpoint parent directory after atomic replacement on POSIX
  and verify ordering; retain the explicit Windows limitation. [M-03, M-15,
  AC-13]
- [x] Add a 23-path donor-manifest contract that fails on any omitted path,
  altered byte, wrong Git mode/blob, length mismatch or archive-digest drift.
  [M-01, M-03, M-18; AC-01, AC-16]

### 2.2 Preserve the complete donor snapshot

- [x] Import the deterministic donor Git archive and every tracked blob into
  Bronze CAS outside Git; retain path/mode/blob/commit/tree relationships and
  produce a reconstruction manifest. [M-01, M-03, M-04; AC-01, AC-02, AC-04]
- [x] Verify byte-for-byte reconstruction of all 23 donor paths and the pinned
  archive digest from Bronze objects alone. [M-03, M-16; AC-01, AC-12]

### 2.3 Capture eligible official originals

- [x] Apply per-resource preflight rights/access/size/type checks and capture
  every eligible census item with HTTP/WARC evidence; retain metadata-only or
  tombstone records for non-eligible and unavailable items. [M-02, M-03, M-04,
  M-11, M-12; AC-02, AC-04, AC-09]
- [~] Record retries, observed source versions and immutable versions;
  never let a current workbook replace a historical edition. [M-02, M-04,
  M-15, S-04; AC-04, AC-09, AC-13]
  Per-attempt retry events and captured-version fixity/validators are additive
  in the fiscal capture manifest. Scheduled heartbeats/source discovery and
  redirected-orphan WARC reconciliation remain open; unique same-URL orphan
  attempts can be recovered on explicit resume. See
  `bronze-checkpoint-contracts.md`.
- [~] Establish per-vintage source-layout baselines from retained Silver
  workbook inventories and captured official PDF page structures, linked to
  capture identities and Bronze fixity. The retained 2026-10-02 workbook baseline fingerprints six of its
  74 captured sources; BEFU-2026 and HYEFU-2025 show observed layout variation
  under their shared extraction profile. PDF evidence now fingerprints all 59 retained captured PDFs, including three
  default-readable encrypted originals previously excluded. All 56 previously
  recorded rows are unchanged; two complete builds are byte-identical. This is
  the pinned 2026-10-03 capture cohort, not the entire current census. Other
  source-layout coverage and mapping approval remain open.
  Structural variation is not an approved mapping. See
  `source-layout-baseline-20261002.md` and
  `source-pdf-layout-baseline-20261018.json` and
  `readable-pdf-layout-qualification-20261018.json`. [M-02, M-11, S-04; AC-03, AC-09]
- [x] Confirm Git contains manifests/schemas/evidence only, not source payloads
  or large generated derivatives. Verified 2,998 tracked paths against all 73
  captured object hashes: zero source-byte matches and zero tracked files above
  10 MiB. [M-03, M-18; AC-02, AC-16]

### 2.4 Phase review and checkpoint

- [x] Run CAS/WARC/manifest validation, property and mutation lanes, donor
  reconstruction, interruption/resume and restriction negative paths. [M-03,
  M-04, M-16, M-18; AC-01, AC-04, AC-12, AC-16]
- [x] Self-review and run the full repository harness; record which source
  states are observed, captured or still gated. [M-18, M-19; AC-16]

## Phase 3 — Silver schema and extraction foundation

### 3.1 Schema contracts first

- [x] Reconcile the final normalization/SQLite checkpoint with integrated source
  and test hashes; preserve the historical receipt and independently verify
  its remote source. Fresh focused tests: 260 passed, both modules at 100%
  coverage. See `normalization-checkpoint-integration-20260913.md`.
  [M-03, M-05, M-06, M-07, M-18; AC-05, AC-16]

- [x] Export independent JSON row-shape schemas from the eight Arrow contracts,
  preserving nullable fields, exact decimal strings and fixed record-set/version
  constants. Test formats and representation bounds without claiming semantic
  source validation, identity construction or canonical promotion. [M-05,
  M-06, M-18; AC-05, AC-16] (`7941162`; 51 focused tests, two cold mutant
  kills, 2,796 native tests; structural only, hosted delivery separate)
- [x] Establish an additive immutable Arrow registry for all eight record-set
  shapes, with nullable unknown valid times, source precision and provenance;
  test Parquet round trips without rewriting or promoting v1 source packages.
  Row-level semantic validation and source projections remain separate tasks.
  Functional commit `d67bd41`; 34 focused tests, 30 cold mutant kills and a
  full local harness pass with 2,424 tests. Hosted delivery remains separate.
  [M-05, M-06, M-18; AC-05, AC-16]
- [x] Add failing JSON Schema/Arrow/Parquet fixtures for the eight required
  `health_appropriations` record sets, versioning, stable IDs, fixed-precision
  money, null reasons, units, vintages, bitemporal fields, rights and lineage.
  Verified by the merged linked-fixture suite (673 affected tests); see
  `eight-recordset-fixture-completion.md` and its paired JSON receipt.
  Transport admission is not semantic source approval. [M-05, M-06, M-18;
  AC-05, AC-16]
- [x] Add negative fixtures for binary-as-text decoding, unknown layouts,
  ambiguous units, duplicate keys, incompatible periods, missing lineage,
  formula/cached-value ambiguity and unjustified classification mappings.
  Existing rejection and boundary fixtures cover binary payloads, duplicate
  JSON keys/IDs, unsupported layouts, interval conflicts, formula/cache
  uncertainty and evidence-bearing mappings. Unknown or unjustified facts
  remain preserved/unqualified where transport is intentionally permissive.
  [M-05, M-06, M-07, M-18; AC-05, AC-11, AC-16]

The fixture tasks above are complete from their task-specific evidence. The
full Phase 3.4 integration checkpoint remains open and must run on the
integrated parent head.

### 3.2 Implement the domain and adapter protocol

- [x] Project reviewed Budget-2025/2026 facts into canonical appropriation
  fields, composing existing unmapped source-label occurrences and complete
  lineage accounting. Preserve source Decimal(20,3) exactly, year tokens and
  amount types; leave dates/currency/price basis unestablished. No I/O, rights
  promotion or original-token claim beyond extraction lineage. [M-05, M-06,
  M-07, M-18; AC-05, AC-16]

- [x] Compose verified historical snapshots and the pure canonical projection
  into an exclusive local-only export, defaulting to dry-run, with complete
  readback and retained partial failures. Keep source packages and publication
  unchanged. [M-05, M-06, M-07, M-16, M-18; AC-05, AC-16]
  (`8bee922`; 52 focused tests, 41/41 cold mutants, 3,194 native tests;
  see `historical-canonical-export.md`; standalone verification remains pending.)
- [x] Project reviewed historical Health/GDP facts and field lineage into the
  canonical Arrow shapes with exact Decimal bounds, vintage-aware identities,
  unknown starts, period dependencies and complete mapped/retained lineage
  accounting. Keep input verification and publication separate. [M-05, M-06,
  M-07, M-18; AC-05, AC-16]
  (121 focused tests, 129/129 cold mutants, 2,866 native tests; see
  `historical-projection.md`; other source projections remain pending.)

- [x] Register the dedicated health-appropriations domain and versioned
  multi-recordset schemas without weakening other domain contracts. [M-05;
  AC-05]
- [~] Establish hash-bound explicit adapter selection from Bronze bytes,
  bounded XLSX preflight, ambiguity rejection and `preserved_only` fallback.
  The common dispatch boundary now records considered/matched adapter IDs and
  uses bounded layout probes to select between the named-column Budget Health
  expenditure and edition-bound revenue profiles. Production registrations
  now also cover exact CPIQ.SE9A CSV, DPE056AA annual population CSV, QES Table 8
  earnings workbook, and GDP Table 1 workbook. These emit typed records, loss
  accounting and source lineage through the same hash-bound dispatcher;
  CPI/population/vintage boundaries remain explicit. Four context adapters
  additionally emit unresolved literal dimension assertions and source-row
  links. Common dispatch coverage for other source-operation profiles,
  Pharmac CPB HTML is now supported through its exact-profile adapter;
  the reviewed 2003/04 Vote Health composite PDF profile is now registered;
  the pinned 2016/17 Estimates overview now also dispatches through its
  source-specific parser with all-page dispositions and field lineage. Pinned donor SQLite dispatch was delivered in PR #711; the five literal
  bundles now have native/full qualification. Other source-specific PDF and
  historical workbook coverage, mappings and integrated drift remain open. See
  `adapter-dispatch.validation.json`, `budget-adapter.validation.json`, and
  `budget-revenue-adapter.validation.json` and
  `context-adapters.validation.json`. [M-05, M-07; AC-03, AC-05]
- [x] Register one non-ambiguous common Bronze adapter for the reviewed
  2003/04 Vote Health PDF. It extracts the exact summary, complete Part B1
  rows, and fixed Part F revenue table, preserves page dispositions and field
  lineage, and matches the three existing normalizers on their shared fixtures.
  Other PDF editions/layouts remain preserved-only. [M-05, M-07, M-10, M-18;
  AC-03, AC-05, AC-08, AC-16]
- [~] Implement stable dimension and mapping contracts for vote,
  appropriation, department, portfolio, amount type, functional/economic
  classification, measure, unit and period. The Budget expenditure adapter now
  emits source-literal assertions and field links for its observed labels,
  period token, amount header and adapter measure rule; all mapping targets stay
  unresolved. Economic classification, evidence-backed crosswalks, confidence
  and effective periods remain open. See
  `budget-source-dimensions.validation.json`. [M-06; AC-05, AC-11]

### 3.3 Determinism and drift hardening

- [x] Bound public Budget reader directory enumeration to four expected files
  plus one and impose explicit Parquet Thrift metadata limits before decoding;
  retain existing snapshot/row/expanded-byte guards and transport-only scope.
  [M-07, M-18; AC-05, AC-16]

- [x] Make dispatch selection evidence canonical-JSON serializable and SHA-256
  bound, including exact source fixity, declared/detected media types, selected
  adapter or preserved-only reason, and sorted considered/matched IDs. [M-05,
  M-07, M-18; AC-03, AC-05, AC-16]
- [x] Persist the verified expenditure adapter-selection receipt in the raw
  Budget expenditure and revenue extraction manifests and verify repeated
  builds have identical receipt and Parquet bytes. Unsupported layouts retain
  their established fail-closed parser errors and write no package. Other
  adapter manifests remain pending. [M-05, M-07, M-10, M-16; AC-03, AC-05,
  AC-08, AC-12]
- [~] Add schema fingerprints, adapter selection evidence, deterministic
  ordering/serialization, source-layout drift reports and fail-closed unknown
  layout handling. Dispatch selection and source-family Arrow schema/layout
  fingerprint comparison now have deterministic contracts; per-source captured
  layout baselines and integrated drift receipts remain open. See
  `context-adapters.md` and its validation receipt. [M-05, M-07, M-18, S-04;
  AC-03, AC-05, AC-16]
- [x] Demonstrate repeat normalization yields identical manifests and Parquet
  content identity for the same inputs/environment. [M-10, M-16; AC-08,
  AC-12] All 15 fixture-backed source-operation profiles now compare complete
  two-build output digests and bytes with unchanged sources. The seven
  registered Bronze adapters also compare their hash-bound selection receipts
  and complete typed extraction outputs across two dispatches. Existing
  independent normalizer contracts cover Budget expenditure/revenue, CPI, QES,
  GDP, Pharmac, and annual population products. See
  `silver-repeat-normalization-20261001.json`; these checks establish local
  determinism, not source rights or semantic approval.

### 3.4 Phase review and checkpoint

- [x] Run schema, golden, property, mutation, archive-safety, typing and focused
  coverage gates; review binary preservation and lineage boundaries. [M-18;
  AC-05, AC-16] The integrated repository harness passed on `496cdff9`:
  7,286 passed, 10 skipped, 98.14% branch-aware coverage against the configured
  80% floor; schemas, parity, mutation, format, lint and strict typing passed.
  Existing contracts cover the Phase 3 schema, adapter, lineage, drift and
  repeat-build boundaries; no tests were added to raise coverage.
- [x] Run the full repository harness and record paired evidence. [M-18,
  M-19; AC-16] Local full-harness evidence is recorded in the 2026-10-03
  runlog entry; hosted exact-head checks will be paired through the PR gate.

## Phase 4 — Donor extraction and functional parity

### 4.1 Donor normalization tests first

- [x] Create red/golden tests for the donor's fiscal spending, GDP,
  appropriation and HYEFU/BEFU summary extraction using Bronze-derived test
  fixtures; cover headers, footers, blanks, formulas, duplicates, units and
  source-layout failures. [M-07, M-08, M-18; AC-03, AC-06, AC-16] (2026-09-28:
  expanded footer/formula and detailed formula-total fixtures; see
  `donor-area-normalization-20260928.md`.)
- [x] Execute the type-tagged row-level parity oracle for all five donor
  SQLite tables/312 rows against their pinned original workbook sources. All
  312 donor rows matched; 29 additional annotated historical Health years were
  retained as candidate-only deviations and joined to source-cell evidence.
  `donor-source-parity.validation.json` records the exact source, database and
  normalization-manifest pins. [M-08, M-18; AC-06, AC-11, AC-16]
- [x] Require explicit reconciliation rationale and source coordinates for
  source-present deviations in the repair ledger; donor-only records retain a
  null source coordinate and require a reason. This records evidence only and
  does not approve a repair or publication. [M-08, M-18; AC-06, AC-11]

### 4.2 Build source-faithful donor Silver records

- [x] Extract historical Health spending and nominal GDP from the pinned
  workbook, retaining exact stored numeric tokens, annotated years, footnotes,
  March/June period context and accounting-basis transitions. Reconcile every
  source/oracle row through explicit difference records without rounding away
  source precision or dropping annotations. [M-05, M-06, M-07, M-08;
  AC-03, AC-05, AC-06, AC-11] (`3376695`)

- [x] Extract BEFU/HYEFU literal Health summaries from verified originals,
  preserving Actual/Forecast, units, vintage, cell lineage and explicit
  unselected-area dispositions. Reconcile both ten-row donor oracles without
  selecting the separate cached-formula totals. [M-05, M-06, M-07, M-08;
  AC-03, AC-05, AC-06] (`801783d`)

- [x] Implement the named-column Budget expenditure adapter from verified
  original bytes, with full row dispositions, source-cell lineage, fixed decimal
  amounts and a non-overwriting Parquet/manifest command. Reconcile the pinned
  workbook's 215 Health rows against its donor-table oracle without altering
  the existing donor-SQLite products. [M-05, M-07, M-08, M-09; AC-03, AC-05, AC-06]
  (`d26e769`)

- [x] Normalize all in-scope donor workbook data areas into the dedicated
  record sets; attach field/cell lineage and reason-coded exclusions. [M-05,
  M-07; AC-03, AC-05] (2026-09-28: seven donor workbooks, 12 expected-count
  guarded stages, 739 facts, 11,565 lineage links and 14,278 row/cell
  dispositions; two 50-file replays were identical. The explicit functional
  scope and the still-open 152-sheet census boundary are in
  `donor-area-normalization-20260928.md` and its JSON receipt.)
- [x] Reconcile against the donor SQLite derivative, preserve the observed
  donor tables, and resolve every difference through a test-backed repair
  ledger. The 29 source-only rows have pinned footnote markers that the donor
  transform coerces away; the 1976 decimal token and SQLite REAL have equal
  binary-float values. All differences are accepted as retain-both
  dispositions, with null replacements and publication approval false.
  [M-08; AC-06, AC-11] (2026-09-27; see
  `donor-historical-dispositions-20260927.json`; fixture guards in
  `test_parity_replay_contracts.py`)

### 4.3 Replace donor utilities and analyses

- [x] Orchestrate the four original-workbook adapters from a pinned donor
  manifest and verified CAS, with a read-only preflight, exclusive new-run
  outputs, complete-run hash verification and preserved failure evidence.
  Keep raw extraction state separate from published donor-derived products.
  [M-09, M-15, M-16, M-18; AC-07, AC-12, AC-13, AC-16] (`578235c`)

- [x] Implement a typed workbook/source inventory CLI equivalent to
  `inspect_excel.py`, with structured output and bounded failures. [M-09,
  M-15; AC-07, AC-13] (`446a82d`)
- [x] Implement the raw-to-Silver pipeline equivalent to `process_data.py`;
  regression-test the compile defect, positional heuristics and swallowed
  exceptions rather than retaining them. [M-09, M-18; AC-07, AC-16]
  (`578235c`, conformance `4454d75`; four donor-intended workbook profiles,
  341 facts and verified raw-run readback; full workbook-area normalization,
  further vintages and partial-stage resume remain separate pending tasks)
- [x] Generate the five-table SQLite compatibility database from canonical
  Parquet and validate schema/row/value parity or approved repairs. [M-08,
  M-09, M-10; AC-06, AC-08] (`e91d24b`)
- [x] Implement structured equivalents of `run_analysis.py` for long-term
  nominal trends, year-on-year growth, GDP share, recent appropriation
  breakdown and classification trends. [M-09, M-13; AC-07, AC-08]
  (`b38069c`, PR #261 merged `15b47b9`; four matching local builds,
  seven exact-head hosted checks; earlier local timing failures retained)
- [x] Reproduce all six donor plots with semantic parity contracts covering
  query inputs, filters, series, units, labels and rendering parameters; retain
  donor PNGs unchanged in Bronze. [M-03, M-09, M-13; AC-02, AC-07, AC-08]
  (`eeb6200`; PR #269 merged `b149d37`, seven exact-head checks;
  three byte-identical builds, visual QA and disclosed semantic differences)

### 4.4 Phase review and checkpoint

- [x] Run the 23-file, 312-row, four-analysis-family and six-plot parity suites,
  plus deterministic rebuild and unsupported-layout tests. [M-01, M-08,
  M-09, M-16; AC-01, AC-06, AC-07, AC-12] (2026-09-27: 23 donor objects /
  6,604,301 bytes and 29 comparison inputs reverified; five-table/312-row
  oracle, historical ledger and the complete health-appropriations domain
  suite passed. Twelve-stage Bronze replay rebuilt 739 observations into 50
  files in two byte-identical clean runs. The 30 historical deviations now
  have source-backed retain-both dispositions; no replacements or publication
  approvals were made. See `donor-historical-dispositions-20260927.json`.)
- [x] Self-review, full harness, and paired evidence; no parity claim may hide
  an unexplained difference. [M-18, M-19; AC-16] (2026-09-27: required
  `./scripts/validate.sh` passed 6,963 tests / 9 skipped at 97.95% branch
  coverage; 48 schemas, 38 representative documents, differential parity 9/9,
  all configured mutation/hygiene and supply-chain gates, and strict 113-part
  SBOM. Historical differences retain source and donor observations separately;
  no value replacements or publication approvals were granted.)

## Phase 5 — Longitudinal Silver expansion and contextual data

### 5.1 Source-family contracts first

- [x] Normalize the exact retained Stats NZ GDP Table 1 expenditure-measure
  profile: 60 quarterly current-price actual observations, separate series
  prefix/reference, literal dollar-million units with ISO currency unverified,
  full cell dispositions and field lineage. No annual aggregation, denominator
  selection, source download or publication. [M-05, M-06, M-07, M-18; AC-05,
  AC-09, AC-16]
  Delivered PR302, merge `1d134bfea0cdcfea49162da3a99b7db99b3485cc`;
  local native and hosted receipts remain distinct in [GDP receipt](./gdp-profile.md).

- [x] Persist canonical Budget label occurrences in an exclusive local-only
  package composed with the pinned Budget reader and original-byte verification.
  Dry run serializes/caps all planned bytes without state creation; preserve
  complete lineage accounting and partial failure evidence. No crosswalk,
  spending-fact mutation or publication. [M-05, M-06, M-07, M-18; AC-05, AC-09, AC-16]
  Native validation and two-build retained-input pilots pass; hosted delivery
  remains separate. See [local-only receipt](./classification-export.md).

- [x] Project verified Budget functional-classification source-label occurrences
  into the canonical dimension shape: four literal labels, local scheme,
  unknown scheme version/identifier and unmapped state; preserve per-source
  vintage/coordinate identity and complete input-lineage accounting. No
  authoritative crosswalk, source mutation or publication. [M-05, M-06,
  M-07, M-18; AC-05, AC-09, AC-16]
  Local pure projection, focused/mutation/native assurance and in-memory pilots
  pass; hosted delivery remains separate. See [receipt](./budget-classification.md).

- [x] Normalize the retained Pharmac medicines-budget HTML profile into
  pharmaceutical-budget facts, preserving all 14 financial-year rows, supplied
  changes/percentages, literal missing markers and trailing empty cells. Bind
  July–June dates to the page's explicit definition; retain caption mismatch
  and 2022 budget-holder reform context without claiming actual expenditure,
  cross-regime equivalence, or new publication rights. [M-05, M-06, M-07,
  M-11, M-18; AC-05, AC-09, AC-11, AC-16]
  Delivered PR295, merge `9e559799f441651e79d4109fcd28e5fa89be668e`;
  see separate local/hosted [receipts](./pharmac-cpb.md).

- [x] Register bounded BEFU-2026/v1 and HYEFU-2025/v1 literal Health-summary
  contracts from retained originals, with version-specific sheets, coordinates,
  year/type/unit context, synthetic drift tests and independent OOXML pilot
  reconciliation. Keep all other fiscal tables and formula totals excluded.
  [M-05, M-06, M-07, M-11, M-18; AC-05, AC-09, AC-11, AC-16]
  (PR #283 merged `565dd88`, seven exact-head checks; 50 focused tests,
  100% critical coverage and 64/64 cold mutants)
- [x] Retain two independent local builds per successor forecast profile and
  reconcile all 20 literal facts, 120 lineage entries and 4,721 dispositions
  independently against OOXML, with original hashes unchanged. This does not
  complete broader fiscal-table, historical-edition or publication coverage.
  [M-05, M-07, M-11, M-18; AC-05, AC-09, AC-11, AC-16]
- [x] Validate full 17-column Budget-2025/Budget-2026 synthetic layouts and
  cross-vintage non-pooling; independently reconcile the captured 2026 pilot
  against literal source XML, retaining its original and all dispositions.
  [M-06, M-07, M-11, M-18; AC-05, AC-09, AC-16]
  (`525dd5f`; PR #273 merged `d0a36f1`, seven exact-head checks;
  two byte-identical pilot builds and independent literal-XML reconciliation)
- [x] Add a bounded read-only consumer for pinned individual Budget extraction
  packages, validating counts, source context, identity and complete lineage
  without assuming every source belongs to the donor's fixed four profiles.
  [M-05, M-07, M-10, M-15, M-18; AC-05, AC-08, AC-13, AC-16]
  (`07029cc`; PR #273 merged `d0a36f1`, seven exact-head checks;
  61 focused tests, 100% critical coverage and recovered 110/110 cold mutants)

- [x] Add versioned fixtures for each approved Vote Health, Budget,
  BEFU/HYEFU, Treasury fiscal, Ministry Vote Health, Pharmac CPB, CPI, wage and
  population layout before enabling its adapter. [M-06, M-07, M-11, M-12,
  M-18; AC-05, AC-09, AC-10, AC-16] The v1 fixture manifest now binds every
  enabled local operation profile to an available layout and rejects operation
  profiles for the still-required Budget, Vote Health and population layouts.
  Focused fixture and source-operation tests passed; full-harness evidence is
  recorded with this implementation checkpoint.
- [x] Add gap, revision, supersession, incompatible-classification and
  cross-source variance tests for multi-vintage series. [M-06, M-11, M-12,
  M-18; AC-09, AC-11, AC-16] The source-family guard checkpoint combines
  historical discovery gaps, Budget vintage isolation, period/basis variance,
  overlapping-revision rejection and unmapped-classification contracts. These
  guardrails preserve distinct sources and versions; they do not normalize the
  pending source families or establish semantic equivalence.

### 5.2 Normalize direct official datasets

- [x] Normalize the two retained HAIR2024 Ministry CSVs as separately
  attributed published indicators, preserving exact tokens and unknown units,
  real-price base and denominator methodology without semantic promotion.
  [M-05, M-06, M-07, M-11, M-18; AC-05, AC-09, AC-11, AC-16]
  (PR #291, observed merge25f9fb5 after seven exact-head passing checks;
  broader Ministry coverage and methodology remain pending)
- [x] Characterize and independently rebuild the retained fiscal 1972–2025
  Health/GDP selection using the existing strict adapter; retain 108 facts,
  lineage, period transitions and explicit 2017–2024 GDP revisions without
  replacing the 2024 edition or publishing. This is not whole-workbook or
  full annual-edition coverage. [M-05, M-06, M-11; AC-05, AC-09, AC-11]

- [~] Promote eligible Vote Health Estimates/Supplementary Estimates and
  annual Budget expenditure/revenue data from Bronze to Silver, preserving
  source-specific labels and explicit coverage gaps. [M-05, M-06, M-11;
  AC-05, AC-09]
  Budget 2026 revenue now has one locally verified edition-specific extraction
  and canonical projection; see `budget-revenue-2026.md`. Common hash-bound
  dispatch now registers the reviewed named-column Budget expenditure profile
  and one exact Budget 2025/2026 revenue vintage per registry set; see the
  `budget-expenditure-common-dispatch-20261003.md` and
  `budget-revenue-common-dispatch-20261003.md` notes. Other Budget revenue and
  expenditure editions and most Vote Health Estimates remain incomplete. One
  exact 2002/03 Treasury Estimates PDF has a Part B1 detail profile with 27
  facts and an edition-specific Part F profile with 16 revenue facts,
  preserving the 2001/02 and 2002/03 column meanings. Edition-pinned overview
  profiles now cover 2002/03, 2004/05, 2005/06, 2006/07 and 2007/08, with
  separate source-specific measures. The 2008/09 PDF contributes six rounded,
  qualified overview amounts, explicitly marked approximate and not treated as
  exact totals. Surrounding prose, remaining editions, rights, comparability
  and annual coverage remain unresolved, so this parent task remains open.
  See `vote-health-estimates-overview-2008-09-20261003.md` and its receipt.
  The next 2009/10 Estimates PDF is now captured under its Treasury CC BY 4.0
  statement. A separate pinned profile preserves 17 page-2 monetary statements
  with their rounded qualifiers, source phrases, and lineage; two independent
  builds match. This adds one overview slice only and does not close the
  remaining edition, whole-PDF, rights, comparability, or annual-coverage work.
  See `vote-health-estimates-overview-2009-10-20261004.md` and its receipt.
  On 2026-10-03, the exact 2002/03 detail package rebuilt twice from its pinned
  Bronze object and matched all retained Silver outputs. The eligible captured
  2003/04 Supplementary Estimates PDF now has separate exact-profile summary,
  Part B1 and Part F Silver products (9, 26 and 17 facts); each rebuilt twice
  with byte-identical outputs and unchanged Bronze. The registered Bronze
  adapter selects this PDF uniquely; all 52 dispatched records match the three
  Silver products by record ID and complete fields. Rights remain unevaluated,
  and other Vote Health editions/layouts and full-year coverage remain open.
  See `vote-health-silver-2003-04-20261003.json`,
  `vote-health-estimates-2002-03-recovery-20261003.json`, and
  `vote-health-silver-20261003.md`.
  The 2002/03 Part F revenue profile was independently rebuilt twice from the
  same pinned Bronze object; 16 facts, 48 lineage rows and 2 page
  dispositions match byte-for-byte between runs. The unique 2002/03 Bronze
  adapter now emits the 27 detail and 16 revenue records; every revenue fact
  matches the Silver package by ID and complete fields. Rights remain
  unevaluated and output remains local-only. See
  `vote-health-revenue-2002-03-20261003.md` and its machine receipt.
  The 2002/03 overview operation emits seven page-2/3 headline facts with
  source phrases, raw tokens, units and lineage; all other page content remains
  preserved-only. See `vote-health-estimates-overview-2002-03-20261003.md` and
  its machine receipt.
  The captured 2011/12 Supplementary Estimates PDF now has a distinct
  source-pinned profile for seven edition-specific category totals across
  pages 2–5. It preserves three `$000` columns, dash/null tokens, negative
  adjustments, lineage, and four partial-page dispositions; departmental and
  non-departmental other expenses are separate in this edition. Rights remain
  unevaluated. See
  `vote-health-supplementary-2011-12-category-totals-20261006.md`.
  The adjacent captured 2010/11 Supplementary Estimates PDF now has a separate
  pinned profile for six printed category totals from pages 2–6. It retains
  all three `$000` budget columns, parenthesized adjustments, direct lineage,
  and partial-page dispositions. Two clean-room Bronze rebuilds and the full
  repository validation result are recorded in
  `vote-health-supplementary-2010-11-category-totals-20261006.md` and its
  machine evidence. Rights remain unevaluated; other source rows and editions
  remain open.
  The 2007/08 Supplementary Estimates and Supporting Information PDF now has
  an edition-specific profile for six category totals on pages 2–6. It retains
  this edition's different Crown-expense and capital labels verbatim, all
  three `$000` columns, source adjustment tokens including a dash/null, direct
  lineage, and partial-page dispositions. Persistent Silver matches two
  clean-room Bronze rebuilds; rights remain unevaluated and other rows and
  editions remain open.
  The captured 2008/09 Supplementary Estimates PDF now has its own pinned
  profile for six printed category totals from pages 2–6. It preserves the
  three `$000` budget columns, parenthesized adjustments, direct lineage, and
  partial-page dispositions. Persistent Silver matches two clean-room Bronze
  rebuilds; the integrated recovery receipt and source-specific evidence are
  linked in `index.md`. Rights remain unevaluated, and the other source rows,
  editions, and Phase 5 products remain open.
  The captured 2006/07 Supplementary Estimates PDF now has an edition-specific
  overview profile for seven appropriation rows on page 3. It retains the six
  printed `$000` columns, original labels, and raw dash/`N/A` tokens with
  field lineage; the separate Crown Revenue and Receipts table remains outside
  this slice. Persistent Silver matches two clean-room Bronze rebuilds and the
  Bronze object is unchanged. Rights remain unevaluated and other source rows,
  editions, and Phase 5 products remain open. See
  `vote-health-supplementary-2006-07-overview-totals-20261007.md`.
  The adjacent captured 2005/06 Supplementary Estimates PDF now has its own
  source-hash-pinned page-3 overview profile for seven appropriation rows. It
  preserves six printed `$000` columns, original labels, and raw dash/`N/A`
  tokens with 42 field-lineage rows; the separate Crown Revenue and Receipts
  table remains outside this slice. Persistent Silver matches two integrated
  clean-room Bronze rebuilds, and Bronze is unchanged. Rights remain
  unevaluated; remaining source content, editions and Phase 5 products stay
  open. See `vote-health-supplementary-2005-06-overview-totals-20261007.md`.
  The adjacent captured 2009/10 Supplementary Estimates PDF now has a pinned
  profile for six printed category totals on pages 2–6, with three `$000`
  columns, parenthesized adjustments, direct lineage, and partial-page
  dispositions. Two clean-room Bronze builds and repository validation are
  recorded in `vote-health-supplementary-2009-10-category-totals-20261006.md`
  and its machine evidence. Rights remain unevaluated; other source rows and
  editions remain open.
  The captured 2013/14 Supplementary Estimates PDF now has a separate pinned
  profile for six explicit appropriation totals from pages 2–6. It preserves
  the three printed `$000` columns, parenthesized adjustments, raw dash token,
  direct lineage and partial-page dispositions. Two clean-room Bronze rebuilds
  match the persistent Silver package. Focused tests and the full repository
  harness pass; rights and remaining table/page coverage stay unresolved.
  See `vote-health-supplementary-2013-14-category-totals-20261006.md`.
  The captured 2014/15 Supplementary Estimates PDF now has a separate
  hash-pinned profile for seven printed category totals on pages 2–6. It
  preserves the three `$000` budget columns, parenthesized adjustments, direct
  field lineage, and partial-page dispositions. Persistent Silver and the
  integrated recovery receipt are repeat-build checked; normalized-fact rights
  remain unevaluated and other PDF content and editions remain open. See
  `vote-health-supplementary-2014-15-category-totals-20261006.md`. The focused
  profile tests and full repository harness pass; the latter reports 7,573
  tests, 10 skipped and 97.66% coverage against the 80% floor.
  The captured 2015/16 Supplementary Estimates PDF now has a separate
  hash-pinned profile for seven printed category totals on pages 2–6. It
  preserves the three `$000` budget columns, parenthesized adjustments, direct
  field lineage, and partial-page dispositions. Persistent Silver and
  integrated recovery builds match, with Bronze unchanged. The focused profile
  tests and full repository harness pass; the latter reports 7,580 tests, 10
  skipped and 97.64% coverage against the 80% floor. Normalized-fact rights
  remain unevaluated and other PDF content and editions remain open. See
  `vote-health-supplementary-2015-16-category-totals-20261006.md`.
  The 2016/17 Supplementary Estimates PDF now has a separate source-hash-pinned
  profile for seven named category totals across pages 2–5, with printed `$000`
  columns, signed parenthesized values, direct lineage, and four partial-page
  dispositions. Persistent Silver matches two clean-room Bronze rebuilds and
  Bronze remains unchanged. Rights remain unevaluated; broader source coverage
  and final recovery gates stay open. See
  `vote-health-supplementary-2016-17-category-totals-20261006.md`.
  The adjacent 2017/18 Supplementary Estimates PDF now has a separate pinned
  profile for seven named category totals across pages 2–5. It retains the
  three `$000` columns, signed parenthesized values, direct lineage, and four
  partial-page dispositions. Persistent Silver is recorded and Bronze remains
  unchanged; rights remain unevaluated. See
  `vote-health-supplementary-2017-18-category-totals-20261006.md`.
  The same bounded overview extraction now covers eight reviewed headlines on
  pages 2–3 of the 48-page 2004/05 Estimates PDF, with its own source hash,
  vintage, transformation and profile. No amounts are summed; remaining PDF
  content, rights and edition coverage remain open. See
  `vote-health-estimates-overview-2004-05-20261003.md`.
  The adjacent 2005/06 edition now has a separate pinned profile for eight
  headlines on pages 2–3 of its 50-page PDF. It retains GST basis, phrase/token
  evidence and lineage, with no inferred sums. Remaining PDF content, rights,
  and edition coverage stay open. See
  `vote-health-estimates-overview-2005-06-20261003.md` and its receipt.
  The 2006/07 edition now has a distinct source-pinned profile for eight
  headlines on pages 2–3 of its 41-page PDF, preserving source phrases, tokens,
  period labels and lineage without recomputing totals. Rights and remaining
  source content stay open. See
  `vote-health-estimates-overview-2006-07-20261003.md` and its receipt.
- [x] Promote the two retained HAIR2024 Ministry published-indicator profiles
  into source-separated canonical Gold with source-coordinate lineage and
  discrete plots. Published real/nominal labels are preserved, while units,
  price bases, denominators and rights remain unevaluated; this does not derive
  actual expenditure or establish comparability. See
  `moh-canonical-gold-20261001.md`.
- [x] Promote the pinned BEFU-2026 and HYEFU-2025 core Crown expense projections
  into separate canonical Gold fact and source-coordinate lineage products,
  preserving distinct release vintages and discrete plots. Financial-year
  alignment, currency/accounting basis, rights, and actual/forecast
  comparability remain unresolved. See `crown-canonical-gold-20261001.md` and
  the repeat-identical Bronze recovery receipt.
- [x] Promote the historical Fiscal Time Series as a separate source-bound
  canonical Gold product; retain its distinct core/total measure definitions
  and unresolved currency, valid-time and rights states. Repeated clean-room
  Bronze rebuild and integrated Gold digests match. See
  `fiscal-crown-canonical-gold-20261001.md` and the recovery receipt.
  [M-05, M-06, M-11; AC-05, AC-09, AC-11]
- [x] Promote Pharmac CPB into the source-separated local canonical Gold
  product, retaining financial-year tokens, published budget-allocation scope,
  the pre/post-2022 funding regimes, eight source-coordinate lineage fields per
  fact, and two regime-separated display plots. This does not establish rights,
  actual expenditure, cross-source comparability, or publication; those remain
  explicit boundaries. [M-05, M-06, M-11; AC-05, AC-09] (see
  `pharmac-canonical-gold-20261001.md`)

- [x] Add the source-pinned 2015/16 Vote Health overview profile and registered
  extraction operation: 17 page-2 statements, phrase/qualifier lineage, repeated
  native and installed CLI agreement; other 99 pages and broader coverage remain
  open. See `vote-health-estimates-overview-2015-16-20261005.md`.
  [M-05, M-06, M-11; AC-05, AC-09]

- [x] Add a source-pinned 2016/17 Vote Health overview profile and reconcile its
  existing source-census/capture/layout records for the 24 monetary statements
  on PDF pages 2–3. Preserve source-specific category names,
  tokens, page phrases and share qualifiers without summing or mapping across
  editions; disposition the other 100 pages as preserved-unreviewed. Keep
  fact-level rights unevaluated and the output local-only until supported
  evidence changes those states. No recapture was performed. Required full
  validation and scoped phase review pass for this bounded slice; broader
  annual source census remains open. [M-05, M-06, M-11; AC-05, AC-09]

- [x] Add a hash-pinned 2017/18 Vote Health Estimates overview profile for the
  25 amount statements on PDF page 2. Preserve source category names, whole-
  million amounts, source phrases, periods and all share qualifiers; leave the
  currency code and rights state unevaluated. The other 94 pages remain outside
  this profile. CPI, wage, population, GDP and Crown series remain separate.
  Repeat builds are byte-stable; wider source census remains open. [M-05, M-06,
  M-11; AC-05, AC-09]

- [x] Add a hash-pinned 2018/19 Vote Health Supplementary Estimates source
  operation for the seven named category totals on PDF pages 2–6. Preserve its
  three printed Budget columns, `$000` unit, null dash tokens, page/field
  lineage and unevaluated rights state. Two builds match byte-for-byte and the
  Bronze hash is unchanged. Other tables/pages and edition coverage remain
  open. See `vote-health-supplementary-2018-19-category-totals-20261006.md`.
  [M-05, M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2019/20 Vote Health Supplementary Estimates
  category-total profile over PDF pages 2–6. Preserve the three source-labelled
  `$000` Budget columns, seven category totals, dash/null tokens, parenthesized
  negatives, page lineage and explicit page dispositions; keep rights unevaluated
  and editions source-separated. Two clean-room Bronze rebuilds match. Other
  rows/pages and wider edition coverage remain open. See
  `vote-health-supplementary-2019-20-category-totals-20261006.md`.
  [M-05, M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2020/21 Vote Health Supplementary Estimates
  summary profile for four named page-7 rows, preserving the three printed
  $000 budget columns, line-wrapped source label, field/page lineage and
  partial-page disposition. Two independent Bronze rebuilds, including the
  recovery entry point, match byte-for-byte; the Bronze object is unchanged.
  Rights remain unevaluated. Other PDF content, editions and comparability
  remain open. See
  `vote-health-supplementary-2020-21-summary-totals-20261006.md`. [M-05,
  M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2021/22 Vote Health Supplementary Estimates
  summary profile for four named page-7 rows, preserving the three printed
  $000 budget columns, line-wrapped source label, field/page lineage and
  partial-page disposition. Two independent Bronze recovery builds and the
  persistent local Silver package match byte-for-byte; the Bronze object is
  unchanged. Rights remain unevaluated. Other PDF content, editions and
  comparability remain open. See
  `vote-health-supplementary-2021-22-summary-totals-20261006.md`. [M-05,
  M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2022/23 Vote Health Supplementary Estimates
  summary profile for four named page-5 rows, preserving the three printed
  $000 budget columns, line-wrapped source label, field/page lineage and
  partial-page disposition. Two independent Bronze recovery builds and the
  persistent local Silver package match byte-for-byte; the Bronze object is
  unchanged. Rights remain unevaluated. Other PDF content, editions and
  comparability remain open. See
  `vote-health-supplementary-2022-23-summary-totals-20261006.md`. [M-05,
  M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2023/24 Vote Health Supplementary Estimates
  summary profile for four named page-5 rows, preserving the three printed
  $000 budget columns, line-wrapped source label, field/page lineage and
  partial-page disposition. Two independent Bronze recovery builds and the
  persistent local Silver package match byte-for-byte; the Bronze object is
  unchanged. Rights remain unevaluated. Other PDF content, editions and
  comparability remain open. See
  `vote-health-supplementary-2023-24-summary-totals-20261006.md`. [M-05,
  M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2024/25 Vote Health Supplementary Estimates
  summary profile for five named page-5 rows, preserving the three printed
  $000 budget columns, departmental-output MYA row, line-wrapped combined
  label, field/page lineage and partial-page disposition. Two independent
  Bronze recovery builds and the persistent local Silver package match
  byte-for-byte; the Bronze object is unchanged. Rights remain unevaluated.
  Other PDF content, editions and comparability remain open. See
  `vote-health-supplementary-2024-25-summary-totals-20261006.md`. [M-05,
  M-06, M-11; AC-05, AC-09]

- [x] Add a separate hash-pinned 2025/26 Vote Health Supplementary Estimates
  summary profile for the six named page-6 totals/authorisation rows. Preserve
  the source-labelled `$000` columns, dash/null tokens, page/field lineage and
  partial-page disposition; keep rights unevaluated and editions source-
  separated. Verify Bronze-to-Silver dispatch and two clean-room recovery
  builds. Other PDF content, edition comparability and wider source coverage
  remain open. Focused contracts pass at 100% line/branch coverage; the full
  repository harness passes on this tree. [M-05, M-06, M-11; AC-05, AC-09]

### 5.3 Normalize analytical context

- [x] Implement the bounded June2026 QES Table8 QEMQ.SASZ9A published
  ordinary-time hourly earnings profile (nine quarters), with literal values,
  unknown currency/sex/adjustment flags and all-cell dispositions; no deflator
  selection or wage-adjusted spending. [M-05, M-06, M-07, M-12, M-18;
  AC-05, AC-10, AC-16]
- [x] Implement the bounded, exact nine-column CPIQ.SE9A quarterly source
  profile with Decimal values, independent NA/status retention, unknown-base
  flag, full source-row dispositions and lineage; validate independent local
  builds without fiscal aggregation, real-value conversion or publication.
  [M-05, M-06, M-12, M-18; AC-05, AC-10, AC-16] (PR #271, checked head
  f4b90ea, observed merge 4ec9920; seven checks and 1,956 hosted tests passed;
  broader context/base/population work below remains pending)
- [~] Promote exact CPI, wage, population, GDP and total/core Crown expense
  observations required by Gold formulas, with base/definition/vintage
  metadata. [M-05, M-06, M-12; AC-05, AC-10]
  A Stats NZ DPE056AA annual mean export (1991–2026) is now preserved in Bronze
  with displayed status flags, a strict source-profile parser and typed
  context-only Silver facts, lineage and row dispositions. Rights, historical
  vintages, analytical selection and denominator approval remain open. See
  `population-annual-export.md` and `population-annual-silver.md`. A
  Bronze-bound canonical projection now verifies the exact Silver package and
  rebuilds 36 canonical context facts with 108 direct links plus two publisher-
  status links (110 lineage rows); the pre-refactor and October 17 operation
  consumer outputs match exactly. Denominator approval and source rights remain
  explicitly unqualified. See `context-operation-canonical-native-20261017.json`.
  The BEFU 2026 core Crown expense formula-cache series has a bounded Silver
  extraction with side-by-side formula/cache lineage and a Bronze-bound
  canonical fiscal-context projection (10 facts, 80 direct lineage rows). A
  clean-room two-run rebuild matched, but cache freshness, currency,
  financial-year boundaries, accounting basis and rights remain unqualified.
  See `befu-core-expense-20260925.md` and
  `crown-expense-canonical-projection-20260929.md`; this is context-only and
  does not qualify accounting comparability or Gold denominators. The historical
  Fiscal Time Series source now has a separate 61-fact Core/Total Crown canonical
  projection with 671 direct lineage rows and repeat-identical Bronze recovery;
  measure comparison, period starts, currency, rights and denominators remain
  unqualified. See `fiscal-crown-canonical-projection-20260929.md`.
  The captured HYEFU-2025 core Crown source now has a separate 10-fact Silver
  package and Bronze-bound canonical projection; it remains a distinct release
  vintage with the same unresolved cache, unit/currency, period, basis and
  rights qualifications.
  A verified local
  context Gold coverage product now includes the pinned CPI, QES, Stats NZ GDP
  and annual population Silver packages with exact source/vintage coverage and
  explicit excluded-value reasons. It does not approve CPI base, GDP currency,
  population denominator, rights, or any cross-series measure. See
  `context-gold-coverage-20260928.md`. The exact quarterly Stats NZ GDP actuals
  now also have a Bronze-bound canonical fiscal-context projection (60 facts,
  420 direct lineage rows) with currency and denominator status unresolved.
  The June 2026-quarter GDP release was published 17 September 2026, after the
  captured March-quarter vintage. Its exact current-price workbook is captured
  as a separate Bronze object and now rebuilds 61 Silver facts, 915 lineage
  rows and 2,323 cell dispositions from `Table 1!C27:BK27`. Repeated clean-room
  output is byte-identical; the pinned March profile and its canonical
  projection remain unchanged. The June series subsequently gained its separate
  canonical projection and source-vintage Context Gold group; the October 2
  receipt records 615 context observations, and the October 17 context-operation
  proof reproduces the entire June recovery report exactly. Currency,
  annualization, denominator selection and rights remain unqualified. See
  `gdp-june-profile-20260930.md`, `context-gold-gdp-vintages-20261002.md` and
  `context-operational-dispatch-native-20261017.json`.
- [x] Resolve the conditional S-05 scope: its exact-export, dictionary and
  resource-rights gate has not passed, so retain the aggregate Health Survey as
  a non-blocking deferred item and leave the Must scope unblocked. Reopen only
  after the source export, dictionary, revision and time/geography contracts
  are pinned. [S-05; AC-10] See `health-survey-assessment.md`.

### 5.4 Phase review and checkpoint

- [~] Generate source-health, temporal coverage, layout drift, rights and
  reconciliation reports; verify every target vintage has an explicit state.
  [M-02, M-11, M-12, S-04; AC-09, AC-11]
  The source-separated Context Gold output now includes quality summaries for
  its four exact pinned context series (observed tokens and retained Silver
  exclusion reasons); calendars and whole-census target-vintage status remain
  unassessed. See `context-gold-quality-20260928.md`.
  A generated Markdown report now accompanies the four series with exact
  source counts and non-assessment boundaries; it is included in the product
  hash closure and read-only verifier. Whole-census source health remains open.
  See `context-gold-readable-report-20260929.md`.
  The explicit selection report now accepts the BEFU-2026 core expense Silver
  manifest with exact source identity, versioned adapter profile, counts and
  output hashes. See
  `../../../evidence/assurance/health-expanded-coverage-20260925/README.md`.
  It covers one selection only. A deterministic source-health report now gives
  each of the 141 recorded source resources and ten context series/vintages
  explicit inventory, qualification, rights, temporal and layout states. Its
  capture reconciliation independently matched all 73 captured census entries
  to the retained capture manifest and verified the 73 referenced Bronze CAS
  objects (38,877,606 bytes) by SHA-256 and size. This does not assess legal
  rights, complete calendars, per-vintage layout drift, discovery completeness
  or donor-value reconciliation; those boundaries remain open. See
  `source-health-report.md` and `source-health-report.json`.
- [x] Run focused adapters, property/mutation checks, self-review and the full
  repository harness; record paired evidence. [M-18, M-19; AC-16]
  Focused source-health and evidence-pin suites, the full validation harness,
  and automatic `phase_7_gates` review passed on 2026-09-29 UTC; see
  `source-health-validation-20260929.json`,
  `source-health-mutation-20260929.json`, and the dated runlog.

## Phase 6 — Gold analytical products

### 6.1 Analytical contracts first

- [x] Add source-qualified, read-only Fiscal 1972–2025 Health/GDP and
  core/total Crown shares from one pinned workbook and verified canonical
  inputs. Retain periods, reporting bases, exact amounts and input lineage;
  report missing denominators explicitly. [M-10, M-12, M-13; AC-08, AC-10]

- [x] Add a verified Fiscal 2025 / Stats NZ annual June mean population
  per-capita query with explicit two-vintage policy, exact input lineage,
  provisional/revision flags and missing/unsupported period reasons.
  [M-10, M-12, M-13; AC-08, AC-10] See `fiscal-health-per-capita-20261004.md`.

- [x] Add a verified household-CPI fiscal purchasing-power benchmark with
  explicit equal-quarter weighting and FY2025 reference, quarter/source lineage,
  original time-status and quality flags, GST basis and incompatible/missing
  denominator controls. [M-10, M-12, M-13; AC-08, AC-10] See
  `fiscal-health-cpi-benchmark-20261004.md`.

- [ ] Add DuckDB query golden tests for nominal, real, per-capita, GDP share,
  total/core Crown share, budget-versus-actual, revisions, classifications,
  department/portfolio and CPB views. [M-10, M-13, M-18; AC-08, AC-10,
  AC-11, AC-16]
  Progress: `test_fiscal_analytical_operations.py` now checks exact source IDs,
  Decimal strings, statuses and contextual labels for all four pinned fiscal
  Gold DuckDB tables. Its cross-product golden matrix reconciles nominal,
  GDP-share, per-capita and household-CPI benchmark rows by fiscal period and
  source identity, and verifies that an unsupported `real` query fails closed.
  The household CPI benchmark is not an approved spending deflator; no derived
  real-spending view is emitted while base, GST and period comparability remain
  unqualified. Existing exact-output tests cover budget-versus-actual,
  revision/classification reports, department/portfolio breakdowns and CPB
  projections. The Crown matrix additionally checks both core/total Crown
  denominator identities and exact query values against shared nominal inputs,
  including a missing total-Crown denominator with null percentage. This is
  synthetic query/readback assurance; source calculation contracts remain in
  `test_fiscal_share_analysis.py`. The broader matrix across Budget, revisions,
  classifications, department/portfolio and CPB remains open; this checklist
  stays incomplete until those contracts are reconciled.
- [x] Add invariant/property tests for denominator identity, CPI base changes,
  financial-year alignment, additive/non-additive measures, revision isolation,
  rounding and incompatible series. [M-06, M-12, M-13, M-18; AC-10, AC-11,
  AC-16] Evidence: `test_fiscal_share_analysis.py` pins denominator IDs and
  per-year GDP shares; `test_fiscal_cpi_benchmark.py` verifies uniform CPI
  rebasing; fiscal share/CPI/per-capita tests cover March/June fiscal alignment,
  ambient Decimal precision, and incompatible or ambiguous inputs.
  `test_budget_vintages.py` verifies exact additive totals while keeping
  overlapping years and inputs separated by vintage and amount type.
  `test_canonical_consumer.py` verifies exact-context revision candidates,
  source IDs by vintage and explicit ambiguity handling. The five focused suites
  passed together (82 tests). This closes the listed invariant/property test
  contracts; cross-source and donor reconciliation remain separate open gates.

### 6.2 Build marts, quality products and reports

- [ ] Build versioned Parquet dimensions/facts and DuckDB views for the
  approved analytical measures, retaining input record IDs and formula
  metadata. [M-10, M-13; AC-08, AC-10]
  - [x] Add a dry-run-first local Gold observation mart and exact-context
    coverage report for verified historical packages. Preserve source record
    IDs and period tokens, verify readback and repeat-build bytes, and keep
    rights/publication unasserted; no cross-source or vintage join. [M-10,
    M-13, M-18; AC-08, AC-09, AC-11, AC-16] See
    `canonical-historical-gold-20260928.md`. Remaining analytical measures and
    source families are still open.
  - [x] Extend the verified local canonical Gold package to source-separated
    Budget appropriation and Budget revenue marts alongside historical Health and
    fiscal-context observations. Include exact-context coverage and a bounded
    per-product input/output report; verify all Parquet bytes and repeat builds.
    Preserve source IDs, avoid vintage pooling and cross-family joins, and forbid
    revenue netting. [M-10, M-13, M-18; AC-08, AC-11, AC-16] See
    `canonical-source-separated-gold-20260928.md`. This does not complete
    contextual joins, remaining Silver families or plot delivery.
  - [x] Add a pinned-source contextual observation and coverage mart for CPI,
    QES wage, current-price Stats NZ GDP and annual population. Numeric
    observations remain context-only; missing values and unretained population
    status evidence are excluded with reason codes, rights remain unevaluated,
    and no denominator or cross-series calculation is performed. See
    `context-gold-coverage-20260928.md`.
- [~] Build coverage, completeness, reconciliation, source-health,
  classification-drift and revision reports with defined thresholds. [M-13,
  S-04; AC-11]
  The local raw-derived Gold export now persists an edition-bounded Budget
  versus Estimated Actual diagnostic with exact input identities and explicit
  unverified period basis. Canonical Gold now also reports exact-context
  historical revision candidates. Coverage and quality reporting remain
  incomplete.
  - [x] Add a source-separated Budget/revenue label-change candidate report
    keyed by exact period and dimensions across observed vintages. The manifest
    does not infer mappings or semantic equivalence; other source families
    remain outside this bounded report. See
    `canonical-classification-drift-20261001.md`. [M-13, S-04; AC-11]
  - [x] Add a deterministic canonical-input identity completeness report to
    the source-separated Gold manifest. It maps each admitted input record ID
    to its exact product, reconciles all output identities, and explicitly
    leaves analytical completeness, source health, revision reconciliation,
    and cross-source reconciliation unevaluated. The separate bounded
    classification-drift report is described above. This
    is provenance accounting, not analytical promotion. See
    `canonical-gold-quality-20260928.md`.
  - [x] Add exact-context historical revision candidates to canonical Gold.
    Compare only unique rows sharing recordset, measure, literal source label,
    unit, price/currency context, denominator, coverage, accounting basis, and
    period across source vintages; retain source IDs and values, report
    duplicate groups as ambiguous, and leave change reasons and other products
    unassessed. The
    clean-room run found 8 candidates across 106 shared historical coordinates;
    Budget/Pharmac/MoH/Crown revisions and cross-source variance remain open.
    See `canonical-revision-reconciliation-20261002.md` and the exact recovery
    receipt. [M-13, S-04; AC-11, AC-12]
  - [x] Extend exact-context revision candidates to source-separated Budget
    appropriation and revenue products. Compare only literal source dimensions
    and identical period tokens across observed vintages; retain contributing
    record IDs and Decimal values, and leave fiscal-period comparability and
    change interpretation unassessed. [M-13, S-04; AC-11, AC-12]
  - [x] Extend exact-context revision candidates to Pharmac allocations,
    Ministry indicators and Crown expense products. Compare only exact
    source-context keys and literal period tokens across observed vintages;
    retain record IDs and Decimal values, report duplicate groups as ambiguous,
    and leave change interpretation and cross-source comparability unassessed.
    [M-13, S-04; AC-11, AC-12]
  - [x] Add a deterministic literal-period overlap catalog across observed
    canonical products, retaining source vintages, units and record identities.
    The verifier and example pin/summarize the report; comparability and
    numeric variance remain explicitly unassessed/not computed. This is
    overlap evidence only, not AC-11 cross-source variance completion.
  - [x] Extend the existing Fiscal analytical reports with an exact-key Gold
    reconciliation. Tie all 54 nominal source observations to 162 share rows,
    54 per-capita rows and 54 household-CPI benchmark rows; retain source IDs,
    fingerprints, periods, denominator/population/CPI lineage and reason-coded
    exclusions. Independently verify all 324 parent amount/identity ties against
    the pinned Arrow tables and prove byte-identical report rebuilds. Do not sum
    overlapping periods or reporting bases. See
    `fiscal-gold-source-reconciliation-20261005.md` and its machine receipt.
    [M-13, S-04; AC-11]
- [ ] Generate deterministic plots, structured summaries and consumer examples
  from the same queries; make source drill-through available. [M-09, M-10,
  M-13, S-06; AC-07, AC-08]
  - [x] Render bounded display-only PNGs from the source-separated canonical
    historical, appropriation and revenue tables. Use exact source context and
    discrete source-period/label categories, retain input IDs in the plot
    report, and report bounded omissions without interpolation. Preserve exact
    values in Parquet; numeric conversion is only for plot display. See
    `canonical-source-separated-gold-20260928.md`. Other measures and donor
    reports remain open; the bounded verified-package consumer example is
    described below.
  - [x] Add a manifest index from each admitted source record ID to its exact
    Parquet output row, bound by table-byte SHA-256 and deterministic sorted
    row position. Verify every link through Parquet readback. This links
    Silver identities within the canonical package; source rights and other
    reports remain open. See
    `canonical-gold-drillthrough-20260928.md`.
  - [x] Extend canonical Gold drill-through with source field coordinates,
    source-object SHA-256, vintage, and a digest of the source locator for each
    admitted record. Build links only from independently verified canonical
    field-lineage tables; do not persist locator text or upgrade rights state.
    See `canonical-gold-source-coordinate-drillthrough-20261001.md`.
  - [x] Add a temporal coverage report to the canonical Gold manifest, listing
    exact observed period tokens and counts by full source context for each
    available historical, Budget and revenue mart. Do not infer gaps, join
    sources or pool vintages. See
    `canonical-temporal-coverage-20260928.md`.
  - [x] Add an executable, read-only canonical Gold consumer example. Require
    the exact manifest digest, verify the package before reading its structured
    product and coverage summaries, and retain explicit unresolved revision,
    rights and publication states. Do not re-aggregate observation values or
    infer cross-source findings. See
    `canonical-gold-consumer-example-20261002.md`.
  - [x] Generate six deterministic fiscal analytical plots from the same
    pinned nominal, share, per-capita and household-CPI queries. Preserve exact
    query values, source record IDs, lineage, exclusions and the row-by-row
    reconciliation in structured reports; separate accounting/GST contexts
    and keep the PNGs display-only with no interpolation or deflator claim.
    Verify dry-run behavior, report readback and byte-identical repeat builds.
    See `test_fiscal_analytical_reports.py` and the fiscal analytical report
    recovery lane. Other source families and donor reports remain open.

- [x] Add a pinned-original Budget-2025/2026 estimate-to-later-value
  comparison for fiscal years 2025 and 2026. Match all literal source dimensions,
  retain unique pairs and unmatched/ambiguous groups, and report arithmetic
  differences without claiming restated appropriation comparability. [M-13; AC-11]

- [x] Package the source-qualified Budget comparison as separately pinned Gold,
  with exact reports, a discrete diagnostic plot and bounded read-only CLI/MCP
  delivery. Preserve unmatched groups and source caveats. [M-13, M-15; AC-11, AC-13]

### 6.3 Phase review and checkpoint

- [ ] Reconcile Gold totals against source, donor and cross-source controls;
  inspect classification/coverage caveats and prohibit causal/forecast claims.
  [M-08, M-11, M-12, M-13; AC-06, AC-10, AC-11]
- [ ] Run deterministic query/plot tests, self-review and the full repository
  harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 7 — Platinum metadata, federation and discovery

### 7.1 Metadata and rights contracts first

- [x] Review clarification: explicitly load the JSON-LD parser plugin without
  an unguarded warm-up parse; retain offline positive/negative fixtures and
  revalidate the exact change. [M-14, M-18; AC-14, AC-16; f111dbf0]

- [x] Validate generated DCAT and PROV JSON-LD with an offline RDF processor:
  compare expanded predicates, resource/literal types, checksum bytes and exact
  derivation edges; deny external context/file/network reads. Keep application
  profiles, rights, publication and graph indexing separate. [M-14; AC-14; c92c3d2f]

- [x] DCAT standards review: use the registered Parquet media-type IRI and
  expose verified payload SHA256 values through typed SPDX checksum nodes;
  independently compare graph digests with retained file bytes. [M-14; AC-14; 791845bc]

- [x] Generate local DCAT recordset/distribution metadata only after original,
  raw and canonical package verification and projection equality. Retain exact
  physical-schema/fixity inventory; reject forged or altered inputs and do not
  infer access URLs, licensing, publication dates or full standards conformance.
  [M-14, M-18; AC-14, AC-16; 791845bc]

- [x] Compose a read-only local provenance verifier for explicit canonical
  historical/classification marker pins, original objects and raw package pins.
  Compare retained tables/accounting with recomputed pure projections and return
  separate scoped fixity evidence; do not change the pure descriptor helper's
  claims or declare Platinum/publication complete. [M-14, M-16, M-18; AC-14, AC-16;
  merged reader evidence and full assurance]

- [x] Project validated typed local descriptors into an entity-only PROV
  JSON-LD graph with exact product-to-input derivation edges, retaining the
  complete inventory and explicit assertion-only scope. No invented activity,
  actor, date, licence, publication or full standards-conformance claim.
  [M-14, M-18; AC-14, AC-16]

- [x] Add a bounded pure local provenance inventory for explicitly supplied
  canonical historical and Budget classification product descriptors. Validate
  exact structural schemas, safe identities and dependency closure without I/O,
  fixity/eligibility claims or publication metadata. This does not complete
  Platinum or whole-product recovery. [M-14, M-18; AC-14, AC-16]

- [ ] Add failing contracts for schema-as-code, DCAT, Croissant, RO-Crate,
  PROV, estate cards, mixed/per-resource licensing, citations and fail-closed
  release readiness. Include missing, conflicting and incompatible rights
  states. [M-04, M-14, M-17, M-18; AC-04, AC-14, AC-16]
  - [x] Require exact rights-evidence bytes for each per-resource
    `eligible_asserted` assertion and verify their SHA256 pins. Reject absent,
    changed, and unreferenced evidence while keeping authority, eligibility,
    and release approval unasserted. See
    `platinum-rights-evidence-fixity-20260928.md`.
- [x] Add offline federation fixtures for namespace, versioned key, mapping
  method, confidence, period and lineage; reject live-runtime or unproven
  mappings. Examples cover unmatched and ambiguous records only; method and
  confidence remain `none`/unknown until reviewed mapping evidence exists.
  No partner links or federation tables are approved. [M-14, M-18; AC-14,
  AC-16] See `federation-fixture-contract-20260928.md`.

### 7.2 Produce governed projections

- [x] Generate and reconstruct local Croissant/RO-Crate inventory candidates
  for verified analytical Gold; parse inline graphs offline and report missing
  required publication/rights/access properties without conformance claims.
  Preserve exact Arrow types instead of inventing ML casts. [M-14; AC-14]

- [x] Generate separately pinned local catalogue records, Arrow schema descriptors,
  dataset cards and offline DCAT/PROV graphs from verified Fiscal analytical and
  Budget comparison Gold manifests. Keep rights, release and source re-verification
  separate; require byte-identical replay and reject altered inputs. [M-14; AC-14]

- [x] Extend the existing local metadata projector with a canonical
  source-separated Gold profile covering its eight fact products. Reuse the
  package verifier, bounded typed reader and existing card/RO-Crate inventory;
  emit full-table schema/observed-token descriptors, catalogue/DCAT/PROV,
  citations, snapshot changelog and explicit source references. Preserve exact
  period tokens without date conversion, existing Fiscal/Budget output bytes,
  rights/publication states and empty approved federation. Verify byte-identical
  reconstruction and offline graph/readback contracts. Extend existing CLI build/
  verify and read-only MCP verification with a paired optional canonical input;
  preserve the existing two-package invocation. [M-14, M-15, M-18; AC-13, AC-14,
  AC-16]

- [ ] Generate and validate metadata, cards, citations, changelogs, catalogue
  and source drill-through records from actual layer manifests. [M-14, S-06;
  AC-14]
  - [x] Generate deterministic local content-addressed citation identifiers
    and snapshot-only changelogs from the verified Fiscal and Budget Gold
    manifests. Bind each record to its manifest SHA256 and propagate only the
    manifest-verified `not_evaluated` rights and `not_performed` publication
    states. Do not claim upstream source citations or changes against a prior
    release; approved federation links remain absent. See
    `gold-metadata-citations-changelog-20261005.md`.
  - [x] Add a source-drillthrough projection containing only hash-pinned
    references copied from explicit source hash/locator fields in the verified
    package manifests. Validate every emitted field path against its exact
    manifest pin; disclose profiles whose manifests have no source-reference
    fields. Keep rights `not_evaluated` and publication `not_performed`; a
    recorded HTTPS locator is not an access or redistribution claim. See
    `gold-metadata-source-drillthrough-20261005.md`.
  - [x] Generate a deterministic RO-Crate 1.1 metadata file alongside each
    local canonical Gold package, enumerating every actual Parquet and plot
    payload with its byte size, media type and SHA-256. Keep the crate itself
    in the package fixity inventory, omit it from its own `hasPart` list, and
    do not add licensing, publication, date or publisher claims. This does not
    complete broader Platinum metadata or standards-processor validation.
  - [x] Generate a deterministic dataset card from canonical Gold product
    rows, exact-context temporal group counts and pinned input package markers.
    Include the card in the manifest and RO-Crate while preserving explicit
    source-health, classification, reconciliation, rights and publication
    boundaries. See `canonical-gold-dataset-card-20260928.md`.
- [ ] Add rebuildable federation tables for approved links to
  `reimbursement-atlas` and `global-medicines-atlas`; preserve unmatched and
  ambiguous mappings. [M-14; AC-14]
- [x] Evaluate graph/vector projections only as non-authoritative Could work
  after a demonstrated query/discovery benefit and pinned reproducibility
  contract. Evaluated and deferred: no health-specific discovery benefit or
  pinned embedding-model contract is evidenced; generic rebuildable search
  remains non-authoritative. [C-01, C-02; AC-14]

### 7.3 Phase review and checkpoint

- [ ] Review every metadata-level rights statement against resource evidence;
  reject hard-coded blanket licensing and unsupported federation claims.
  [M-04, M-14; AC-04, AC-14]
  - [x] Verify the current Fiscal and Budget Gold catalogue, citation,
    changelog, and source-drill-through rights/publication states against their
    exact manifest pins. No licence is emitted; resource-level rights and
    federation approvals remain unresolved. This bounded check does not close
    the broader review. See `gold-metadata-rights-provenance-review-20261005.md`.
- [ ] Run schema/metadata/federation/security gates, self-review and the full
  repository harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 8 — CLI, MCP and scheduled operation

### 8.1 Operational contracts first

- [x] Implement an exclusive local resume executor over an explicitly pinned
  read-only plan, preserving old attempts and originals, with bounded snapshots,
  separate child/envelope verification, interruption evidence and no publication.
  [M-15, M-18; AC-13, AC-16]
- [x] Add a read-only partial-rebuild planner joining pinned donor metadata,
  prior PLAN and explicit stage pins; verify selected originals and classify
  bounded stage fixity/structure reuse without copying or repairing attempts.
  Execution, semantic approval and publication remain separate. [M-15; AC-13]
- [ ] Add CLI/MCP/scheduler tests for inspect, capture, normalize, reconcile,
  analyze, rebuild, candidate-build and status commands, including JSON output,
  dry-run, idempotency, cancellation, partial state, retry/resume, missing
  credentials and redaction. [M-15, M-18; AC-13, AC-16]
- [x] Add scheduled-source heartbeat and drift tests that do not equate a
  successful workflow with capture, validation or publication. [M-04, M-15,
  M-19, S-04; AC-04, AC-09, AC-13]
  The heartbeat marks drift unavailable unless a complete hash-pinned prior
  discovery manifest was compared; the scheduled lane currently has no such
  baseline.

### 8.2 Implement bounded operations

- [x] Expose only BEFU-2026/HYEFU-2025 successor profiles through the existing
  dry-run-first CLI and read-only MCP after explicit forecast API dependency
  validation. Preserve partial failures, exact counts and source-specific
  actual/forecast observations; no annual joins or publication. [M-15, M-18;
  AC-13, AC-16]
  Delivered PR318, merge `d46d3983a1a40581bbd11f446c2b75a35e4f0d15`;
  see [scoped dispatch assurance](./forecast-source-operations.md).
- [x] Add an explicit no-write forecast API path while retaining the existing
  default-write contract and all four source profiles. Require real booleans,
  preserve partial/rejected status and prove old written bytes unchanged.
  This does not expose forecasts through CLI/MCP or assert write readiness.
  [M-09, M-18; AC-07, AC-16]
  (`a85ca41`; 92 focused tests/100% critical coverage, 66 cold mutation kills,
  3,414 native tests at `8ace367`; hosted delivery separate)

- [x] Extend the source-operation allowlist to exact Pharmac CPB and quarterly
  GDP profiles after dependency delivery, retaining source-specific shapes,
  compact counts, CLI default dry-run and forced-read-only MCP. Forecast's
  missing no-write path remains a separate task. [M-15, M-18; AC-13, AC-16]
  (PR313 merged `f41ef9b`; seven exact-head checks passed.)
- [x] Wire the four approved CPI/Ministry/QES source profiles through a
  dry-run-first CLI and forced-read-only MCP preflight, using compact typed
  redacted receipts without changing donor rebuild or archive-status semantics.
  [M-15, M-18; AC-13, AC-16]
- [x] Read an explicitly pinned historical package and original into bounded,
  hash-verified snapshots with exact source-specific schemas/counts. Return
  transport evidence without claiming semantic projection, source rights,
  original workbook execution or publication. [M-15, M-16, M-18; AC-12, AC-13,
  AC-16] (`7a0420e`; 49 focused tests, 57 cold mutants, 2,918 native tests;
  transport-only, hosted delivery separate)

- [x] Expose a compact hash-pinned standalone Budget-package verification
  receipt through matching read-only CLI/MCP contracts. Reject missing,
  partial or corrupt packages without creating state; retain not-evaluated
  rights and package-only verification boundaries. [M-15, M-18; AC-13, AC-16]
  (PR #280 observed merged `113bac5`; exact hosted head `199c82b`)

- [x] Expose hash-pinned read-only raw-run verification through CLI and MCP;
  reject missing, partial, corrupt and mismatched state without creating any
  output or invoking normalization. [M-15, M-16, M-18; AC-12, AC-13, AC-16]
  (`d25fd8d`)

- [ ] Expose typed non-interactive CLI commands and read-only MCP resources
  over stable manifests/queries; return structured state and provenance.
  [M-15; AC-13]
  Context Gold now has a hash-pinned CLI/MCP verifier for its closed output
  inventory and report bytes. This verifies declared fixity only; see
  `context-gold-verifier-20260929.md`.
  - [x] Add a finite read-only Health status MCP resource alongside the
    existing status tool, and exercise the actual non-interactive CLI parser,
    JSON-RPC resource listing/read, output parity and no-write behavior. This
    bounded status slice does not complete the remaining operation commands.
  - [x] Expose a typed read-only MCP preflight for the pinned contextual Gold
    build. It verifies the declared CPI, QES wage, GDP and annual population
    Silver inputs and returns the same dry-run receipt as the CLI, with no
    write option or output creation. Rights and denominator selection remain
    unevaluated. See `context-gold-mcp-preflight-20260928.md`.
  - [x] Add matching non-interactive CLI and read-only MCP verification for the
    pinned Gold metadata package. Require both source package pins and the
    output manifest pin; compare reconstructed metadata bytes without writes,
    preserving unassessed rights and publication states. See
    `gold-metadata-mcp-verifier-20261005.md`.
  - [x] Add named read-only queries over the eight existing canonical Gold
    fact products, with bounded Parquet/schema validation, exact Decimal and
    identity readback, deterministic ordering and CLI/MCP parity. Reuse the
    existing product schemas and fixity verifier; reject arbitrary SQL and
    preserve product-specific units, coverage, vintages and caveats. Exercise
    Budget department/portfolio and Pharmac CPB outputs alongside their
    classification/revision reports without asserting economic equivalence.
    The existing canonical Gold CLI/MCP verifier proves declared fixity only;
    this task closes the distinct data-query gap. [M-10, M-13, M-15; AC-08,
    AC-11, AC-13] See `canonical-gold-queries-20261017.md` for exact native
    readback, repeat-build, resource-limit and validation evidence.
- [x] Add a read-only canonical Gold package verifier to CLI and MCP. Check the
  hash-pinned manifest, exact direct-child output inventory, byte counts and
  SHA-256 values, plus presence of the temporal report; test malformed and
  tampered packages, redaction, JSON parity and no writes. This proves package
  fixity only, not Parquet semantics, source completeness, rights, or
  publication. See `canonical-gold-verification-20260928.md`.
- [ ] Add fast-first scheduled discovery/capture/normalization lanes with
  heavier reconciliation and reconstruction behind explicit triggers and
  bounded resource limits. [M-15, M-18; AC-13, AC-16]
- [ ] Produce operational dashboards/reports from evidence without exposing
  credentials, signed URLs, restricted bytes or personal information. [M-15,
  M-18; AC-13, AC-16]

### 8.3 Phase review and checkpoint

- [ ] Exercise interruption, resumption, concurrent invocation, replay,
  stale state, remote drift and recovery paths; review workflow permissions
  and secret handling. [M-15, M-18; AC-13, AC-16]
- [ ] Run full local validation and, when available, exact-head hosted checks;
  record these as separate evidence. [M-18, M-19; AC-16]

## Phase 9 — Recovery, assurance and publication candidate

### 9.1 Clean-room reconstruction

- [x] Correct PR #691's query recovery oracle to compare the independently
  ordered typed source slice, including nulls, list prefixes, numeric order and
  duplicate multiplicity. Reproduce wrong-subset/reversed-order acceptance,
  run targeted fresh canonical recovery with the stronger oracle, then full
  validation and protected exact-head delivery. Preserve the original weaker
  receipt separately. [M-10, M-16, M-18; AC-08, AC-12, AC-16]

- [x] Rebuild the five canonical historical/Budget input packages directly
  from pinned Bronze originals and locked observation-token definitions, with
  no retained Silver fallback. Preserve original observation identities and
  added adapter-selection evidence; compare two fresh raw/canonical inventories.
  Feed each fresh run's inputs into its canonical Gold build and verify the
  eight named query readbacks plus canonical/composite metadata reconstruction.
  Record new provenance separately from any value change; retain originals,
  dated receipts and rights/publication limits. [M-03, M-10, M-14, M-16, M-18;
  AC-02, AC-08, AC-12, AC-14, AC-16]

- [x] Add an installed dry-run/exclusive-write recovery command for two fresh
  analytical runs, consuming only five Bronze originals and three pinned
  definitions. Rebuild Fiscal products/reports, Budget comparison and both
  metadata packages; verify repeat inventories, unchanged originals and exact
  retained-product equality. Broader source families, standards conformance and
  final Health recovery remain open. [M-10, M-16, M-18; AC-08, AC-12, AC-16]

- [x] Perform two fresh empty-derivative four-profile original-to-raw,
  compatibility SQLite, Gold and plot replays; compare all files and reverify
  donor originals. Record cross-runtime SQLite drift separately. This excludes
  Platinum and interrupted-stage recovery. [M-16, M-18; AC-12, AC-16]
  (38 files per run, byte-identical; all 23 donor objects unchanged;
  `originals-product-replay.md`)
- [~] Add a failing recovery contract for empty derivative state, then rebuild
  Silver, Gold, SQLite, plots/reports and Platinum metadata from Bronze, locked
  code and parameters. [M-10, M-16, M-18; AC-08, AC-12, AC-16] Two fresh pinned
  donor replays rebuild 12 source-native profiles, compatibility SQLite, donor
  Gold and six plots; separate builders rebuild CPI/QES/GDP/population Silver,
  Context Gold and historical canonical Gold. See
  `clean-room-recovery-20260929.json` and
  `clean-room-recovery-20260930.json`. The exact CPI series now also rebuilds
  into 449 canonical price-population facts and 3,143 lineage records twice
  from fresh Silver, with identical output digests; base and rights remain
  unresolved. Donor/canonical reports, additional source-native profiles and
  canonical adapters, and complete validated Platinum remain open.
- [~] Compare output manifests/digests and explain permitted rendering-only
  variation; prove original objects were not mutated. [M-03, M-16; AC-02,
  AC-12] Repeat output inventories match within this runtime across raw, SQLite,
  Gold, plots, Context Gold and historical canonical Gold. Bronze CAS is
  unchanged. SQLite may differ across SQLite runtime versions; see the existing
  `originals-product-replay.md` boundary and new recovery receipt.
  The formerly missing BEFU-2026 charts object was reacquired from its official
  locator and matches both manifest SHA-256 and BLAKE3. A new WARC response
  receipt is additive; the historical capture manifest is unchanged. The
  earlier whole-census report verified 73/73 captured objects. A later census
  refresh adds the separate June-2026 GDP object; see the source-census receipt.
- [x] Refresh current-head clean-room evidence after source-coordinate Gold
  drill-through; verify two repeat builds and unchanged Bronze, and retain exact
  output pins. [M-10, M-16, M-18; AC-08, AC-12, AC-16]
  (`clean-room-recovery-20261001.json`; 12-profile Silver and currently
  supported products repeat identically. Remaining source families, integrated
  canonical reports, and complete validated Platinum remain open.)
  See
  `bronze-object-recovery-20260930.json` and the regenerated source-health
  report.

### 9.2 Build a rights-filtered Hugging Face candidate locally

- [x] Assemble an exclusive local staging bundle from the pinned additive
  inventory, retaining v4 history and new packages separately with full
  readback and bounded failure receipts. No publication-shaped candidate or
  inherited approval is emitted. [M-03, M-16, M-17, M-18; AC-02, AC-12, AC-15,
  AC-16]

- [x] Reject unsafe or colliding original-object destination paths before
  candidate output creation, including traversal and portable filename hazards.
  This bounded preflight does not establish derivative rights or full release
  readiness. [M-14, M-17, M-18; AC-14, AC-15, AC-16] (`1a3356a`; native
  2,219 tests and five mutation kills; hosted delivery remains separate)

- [x] Add a read-only additive inventory for the four explicitly pinned
  Budget-2026/CPI/BEFU-2026/HYEFU-2025 packages, verifying base bytes and exact
  recorded source-rights joins without building, approving or publishing a
  candidate. [M-03, M-04, M-14, M-17, M-18; AC-02, AC-14, AC-15, AC-16]
  (PR #290 merged `07143c8`; native timeout remains recorded, exact-head
  hosted checks passed; subsequent staging changes have separate assurance)

- [x] Add release-readiness negative tests for missing rights, incomplete
  source disposition, failed parity/recovery, stale evidence, non-pinned
  revisions, restricted content and candidate-manifest mismatch. [M-14, M-17,
  M-18; AC-14, AC-15, AC-16]
  Exact local candidate bytes, file-set closure, required metadata, per-original
  rights rows, source dispositions and release-state claims fail closed. A
  separately hash-pinned assurance receipt binds exact code/candidate revisions,
  parity, recovery and UTC freshness without performing publication.
- [x] Build a local candidate for `edithatogo/nz-health-appropriations` with
  rights-eligible originals/derivatives only, schemas, manifests, cards,
  limitations and checksums. Metadata-only/tombstone representations must
  remain explicit. [M-14, M-17; AC-14, AC-15]
  Candidate `2026-08-29-v4` was built and later published without broadening;
  see the checksum-pinned candidate and publication entries in `evidence.jsonl`.
- [x] Record exact candidate manifest hash, byte/file counts, intended splits,
  viewer expectations, collection target and rollback/reconciliation plan.
  [M-17, M-19; AC-15]
  Manifest `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`
  binds 94 pre-manifest files/39,390,246 bytes and the approved collection;
  upload and anonymous readback remain separately evidenced.

### 9.3 Final local assurance and review

- [x] Run focused, property, mutation, recovery, schema, format, lint, strict
  typing, security, vulnerability, licence, SBOM and full repository gates at
  the exact candidate code/tree. [M-18; AC-16]
- [x] Run automatic Conductor self-review across requirements, design, plan,
  evidence, source coverage, rights, reconstruction and publication claims;
  append and resolve every actionable finding. [M-19; AC-14, AC-16]
  Review register: `final-review-20261006.md`; latest clean-room receipt:
  `clean-room-recovery-20261006-vote-health-2018-19.json`. The 2018/19
  category-total profile is now included as a repeated Bronze rebuild;
  remaining implementation, evidence and rights decisions remain open as
  classified in the register.
- [x] Present the checksum-pinned candidate for explicit publication approval;
  local readiness does not satisfy the gate. [M-17, M-19; AC-15]

## Phase 10 — Explicit external Hugging Face publication gate

### 10.1 Upload only the approved candidate

- [x] After explicit approval of the exact manifest and credential
  availability, create/update `edithatogo/nz-health-appropriations` without
  broadening the candidate; retain immutable commit/revision and upload
  receipts. [M-17, M-19; AC-15]

### 10.2 Independently verify hosted state

- [x] Read back remote files and hashes, schema/card metadata, sizes, splits,
  representative records and Dataset Viewer/Parquet endpoints where
  applicable. Treat any mismatch as drift and fail closed. [M-17; AC-15]
- [x] Add the dataset to the approved HEOR collection, then independently
  verify collection membership and pinned revision. [M-17; AC-15]
- [x] Record upload, remote verification, collection membership and public
  release as distinct receipts; make no release claim until all approved gates
  pass. [M-17, M-19; AC-15]

### 10.3 Track completion

- [x] Reconcile local/hosted evidence, Git history, issue/PR state, HF revision,
  collection membership, requirements and known limitations. [M-19; AC-15,
  AC-16]
- [ ] Run final automated review and full harness, resolve findings, mark the
  track complete and archive it only when every Must is evidenced. Donor
  retirement and Zenodo remain out of scope. [M-18, M-19; AC-16]

## Review fixes

- [x] Add a bounded pure bridge from exact historical canonical projections to
  the existing public historical analysis contract, retaining canonical
  lineage, reversible identifiers and explicit field accounting without I/O,
  fixity, rights, execution or publication claims. [M-07, M-09, M-10, M-18;
  AC-05, AC-07, AC-08, AC-16] (`02d36bc`, `13e8d85`, `fbf710d`, `c867f97`,
  `50564fc`; focused mutation and native passed; hosted delivery remains
  separate)

- [x] Add the exclusive, deterministic six-file local Budget appropriation
  exporter with directory-descriptor race resistance, pre-serialization and
  running byte bounds, exact readback/closure, complete receipts, and redacted
  retained failures. This closes only the bounded exporter slice; retained
  two-vintage replay, persisted-provenance consumption, rights and publication
  remain separate. [M-03, M-04, M-07, M-18; AC-02, AC-04, AC-05, AC-16]
- [x] Replay the pinned retained Budget-2025/2026 packages twice each into
  fresh temporary outputs; independently prove exact dry-run/write hashes,
  six-file closure, canonical tables/schemas, full receipts/accounting,
  byte-identical builds and unchanged raw/original hashes. This is local
  validation only, not rights or publication evidence. [M-03, M-04, M-16,
  M-18; AC-02, AC-04, AC-05, AC-12, AC-16]
- [x] Remove the exporter Decimal test's process-global flag precondition after
  hosted macOS exposed test-order dependence; retain exact before/after local
  context and Decimal value assertions. [M-18; AC-16]

- [x] Keep disconnected source-plot segments styled by their full context and
  disambiguate colliding display labels without merging source identities.
  [M-09, M-18; AC-07, AC-16]
  Delivered PR274, merge `4dacd12be50fcc221906db0e497e2073e7e7b0f7`.

- [x] Remove scheduler-dependent Hypothesis deadline flakiness from the batch
  eligibility invariant without weakening generated cases or assertions.
  [M-18; AC-16] (`b2bf7b7`)
- [x] Add the first typed, read-only health-appropriations operational status
  surface shared by CLI and MCP, with explicit no-state, partial, ready and
  corrupt-manifest contracts. [M-15, M-18; AC-13, AC-16] (`da37f79`)
- [x] Bind each reported layer to its exact manifest path and SHA-256 from the
  same bytes used to derive its status, and require captured/selected count and
  result-list agreement with every result captured before reporting Bronze
  ready. This is local manifest evidence;
  it does not prove remote workflow health, source completeness, rights, or
  publication. [M-15, M-18; AC-13, AC-16]

- [x] Add source-separated contextual Gold categorical plots for CPI, wage,
  GDP and population observations. Plot only eligible Decimal values, retain
  exact source period tokens as discrete categories, convert to float only for
  display, and pin every image in the manifest and read-only verifier. This
  adds context plots only; source calendar continuity, rights, denominator
  selection and publication remain unassessed or unperformed.

## Gate register

| Gate | Blocks | Safe work while pending |
| --- | --- | --- |
| GitHub issue creation authority | hosted issue mutation only | all repository-local phases and evidence |
| Dependency-adoption decision | production use of a new workbook/plot dependency | format census, fixtures and comparative evaluation |
| Resource redistribution rights | capture/promotion/publication as specified per resource | metadata, fixity, tombstones, other cleared resources |
| Hugging Face credentials | external upload/readback mutation | all local candidate and recovery work |
| Exact candidate publication approval | upload of that manifest | local assurance and independent non-publishing checks |
| Collection mutation approval | adding/removing collection items | uploaded dataset verification if independently authorized |
| Donor archival/destructive authority | donor retirement only | all assimilation work; retirement remains out of scope |
| Zenodo release authority | deposition/DOI only | all track work; Zenodo remains out of scope |


- [x] Add a source-hash-pinned 2010/11 Vote Health Estimates overview adapter,
  operation schema and tests. Capture and reconcile the official nine-page PDF;
  normalize 18 phrase-anchored monetary statements across overview pages 2–3
  and disposition all nine source pages. Builds are local validation evidence;
  the remaining seven pages are unreviewed and no whole-edition, comparison,
  Gold or publication claim is made. [M-01, M-03, M-07, M-18; AC-01, AC-04,
  AC-05, AC-16]

- [x] Package the qualified Fiscal nominal, spending-share, annual mean resident
  and household CPI benchmark outputs as four bounded, source-qualified Gold
  tables with manifest pinning, typed readback, repeat-build evidence and safe
  exclusive writes. This completes a bounded export; DuckDB, plots/reports and
  operations remain open. [M-10, M-13, M-18; AC-08, AC-10, AC-16]

- [x] Expose bounded named Fiscal analytical Gold queries through an in-memory
  DuckDB adapter, CLI and read-only MCP with exact JSON values, manifest pinning,
  explicit truncation and native Arrow/CLI/MCP parity. Broader analytical views,
  plots and scheduled analytical operations remain open. [M-10, M-15, M-18;
  AC-08, AC-10, AC-13, AC-16]

- [x] Build and verify companion Fiscal analytical reports: six qualified plots,
  exact structured results, schema descriptors, dataset card and local PROV/DCAT
  projections; native repeat and Arrow comparison retained (4 October 2026).
  Full product recovery and final completion review remain open.

- [x] Include two independent pinned Bronze-to-Fiscal analytical Gold/report
  builds and complete CLI/MCP/Arrow readbacks in integrated clean-room assurance.
  Focused native evidence verifies 34 files per run and all 324 query rows;
  source-health and donor/classification preflights pass. The wider Health
  recovery/completion gate remains open.

- [x] Fix Vote Health fiscal coverage using pinned publisher editions separately
  for main and Supplementary Estimates; reject discovered URLs bound to another
  fiscal edition and preserve distinct published additions. PR #695 merged as
  `c490d327` after exact-head local/hosted assurance; clean topic pruned.

- [x] Correct captured Vote Health edition selection for the existing lowercase
  short 2012/13 Supplementary title, excluding its separate supporting-information
  volume. Reconcile current review without recapture; PR #695 merged as
  `c490d327` after exact-head local/hosted assurance; topic pruned.

- [x] Extend common Bronze dispatch to the thirteen already reviewed main
  Estimates overview profiles for 2004/05–2015/16 and 2017/18. Preserve the
  existing 2016/17 API/identities and the separate 2002/03 composite. Reuse
  edition-specific parsers, amount/qualifier/rounding flags, source pins,
  field lineage and every page disposition. Compare all fourteen profiles
  against retained native normalizer outputs (209 facts; 185 newly supported
  through common registrations), prove deterministic repeated dispatch and
  unchanged originals, run the required harness and deliver a focused PR.
  Registration alone does not close operational manifest integration or Phase 3.

- [x] Preserve bounded child-bootstrap evidence when the existing real-process
  capture-recovery checkpoint deadline fails. Retain every 10-second deadline
  and hard-kill/ownership/resume/WARC assertion; diagnose before any causal fix.


- [x] Reconcile the bounded source census plus retained Vote Health capture
  addenda into a deterministic observation-preserving inventory. Pin every
  census/request/manifest input; retain capture-time request hashes and explicit
  legacy-context gaps, source IDs, URLs, versions and rights observations.
  Verify retained CAS objects independently; distinguish this cohort from the
  whole corpus and publication-form completeness. Reuse existing preflight;
  do not recapture or infer analytical admission. [M-02, M-03, M-04; AC-02,
  AC-04, AC-09, AC-16]


- [x] Resolve PR #697 review findings: reject supplied unverified legacy
  requests, and reject unconsumed or ambiguous CLI request inputs rather than
  silently dropping evidence or choosing a logical filename by argument order.
  Preserve old successful assurance evidence; prove the actual cohort output
  unchanged, run exact-head assurance and resolve the actual review threads
  before protected merge. [M-02, M-04; AC-04, AC-16]


- [x] Integrate the separately captured 2019/20 Supplementary Addition as a
  distinct publication form in the bounded observation-preserving inventory.
  Reuse its exact request/capture/CAS/WARC verification, preserve original
  snapshots and the ordinary Supplementary edition, and reconcile publication
  identity, source periods/rights evidence and distinct table-layout roles.
  Do not normalize amounts, infer currency or claim whole-corpus completeness.
  Prove repeat-build stability and run required assurance before focused PR
  delivery. [M-02, M-03, M-04, M-06, M-11; AC-02, AC-04, AC-09, AC-16]


- [x] Route the fourteen reviewed 2004/05-2017/18 main overview source
  operations through actual common dispatch output. Preserve the three native
  Parquet tables, original common losses and explicit compatibility projection;
  persist selection in a versioned closed extraction manifest and qualify
  externally pinned readback/recovery. Keep compact source-operation/v1 and
  existing direct APIs/2002 composite ownership unchanged. Prove native parity,
  repeat-build and interruption/tamper boundaries before full assurance and PR.
  [M-04, M-05, M-07, M-10; AC-03, AC-05, AC-12, AC-16]


- [x] Fix PR #699 symlink-parent preflight/readback policy mismatch. Reject
  symlinked output ancestors before parsing or writing; preserve readback
  checks. Establish a failing real-directory-symlink regression proving no
  target files are left behind, then repeat focused/native/exact-head assurance
  and resolve the actual review thread before protected merge.
  [M-04, M-10; AC-12, AC-16]


- [x] Add explicit common adapters for the existing BEFU-2026/v1 and
  HYEFU-2025/v1 literal Health-summary profiles. Reuse their reviewed extraction
  boundary, preserve legacy APIs/receipts and source-specific Actual/Forecast,
  units, lineage, partial failures and all cell/sheet loss accounting. Retain
  existing direct operation behavior, qualify native parity against retained
  successor outputs, and run required assurance before focused PR delivery.
  This does not close general operational adoption or the donor-area census.
  [M-04, M-05, M-06, M-07; AC-03, AC-05, AC-09, AC-16]


- [x] Adopt common dispatch in the two reviewed forecast source operations.
  Build facts/lineage from actual common output; explicitly reconcile raw cell
  metadata from the same verified shared snapshot. Persist selection, all losses
  and versioned projection metadata with independent manifest-pin readback.
  Preserve compact public receipts, four native APIs, no-write failed preflight
  and retained four-file partial packages on explicit-write rejection. Exercise
  tamper, interruption, repeat-build and symlink-ancestor contracts before native
  and full assurance, focused PR, protected merge and clean topic pruning.
  [M-04, M-05, M-07, M-10; AC-03, AC-05, AC-12, AC-16]


- [x] Resolve PR #701 generated-output bound mismatch: reproduce a real
  native-accepted large-loss source, derive read limits and producer consistency
  pins from source-regenerated serialized outputs before writes, retain independent
  external-pin verification and tamper controls, then qualify large-source/native,
  focused/full/hosted results before resolving the review and merging.
  [M-04, M-05, M-07, M-10; AC-03, AC-05, AC-12, AC-16]


- [x] Adopt existing context common outputs in the five CPI, annual population,
  QES and GDP Q1/Q2 source-operation profiles. Preserve every common record,
  lineage, loss, unresolved dimension and link in versioned extraction evidence,
  with explicit source-specific projections to unchanged native Parquet tables.
  Bind literal vintage/version/layout controls, including recorded CPI context,
  population raw versus legacy canonical lineage and the existing GDP parser
  token. Preserve QES preflight/public compact behavior and every direct native
  API. Reuse source-regenerated bounds, independent manifest pins, repeat-build,
  tamper and interruption/no-overwrite contracts. Materialize only the missing
  June GDP native reference from verified Bronze and require independently
  recorded historical file pins before comparison. Qualify focused/native/full
  and hosted checks, then protected merge and clean topic pruning. No analytical
  selection, currency, denominator, rights or join approval is implied.
  [M-04, M-05, M-06, M-07, M-10; AC-03, AC-05, AC-11, AC-12, AC-16]

- [x] Integrate independently verified common context-operation packages into
  source-separated canonical and Gold consumption. Reuse existing canonical
  transformations, preserve original fixed-cohort native readers and pins, bind
  new operation manifests and full provenance explicitly, and demonstrate
  canonical value/lineage parity plus downstream repeat-build recovery. No
  denominator, currency, rights or analytical join admission is implied.
  [M-05, M-07, M-10, M-12; AC-05, AC-08, AC-10, AC-12]

  Canonical consumer progress: all five operation profiles now project 615 facts
  and 4,190 fully validated lineage rows, with explicit source-backed completion
  of QES legacy metadata and retained historical representations. PR #703 merged
  after all required checks passed. Source-separated Gold consumption now also
  retains all canonical products/common evidence, observes actual source status,
  and supports typed CLI/read-only MCP. Two Bronze-driven20file rebuilds match;
  all7867 tests and full local gates passed at7143a86a. PR #704 merged3545f270
  after finalheadab156c16 passed all required checks.
  Fetched ancestry/identical tree/zero unique changes preceded topic pruning.
  The five-profile canonical/Gold integration item is complete; broader phases
  stay open.


- [x] Resolve PR #704 output-directory substitution race. Reproduce swaps before
  first write and between writes, then bind all output writes to the reserved
  directory object. Qualify native protected Windows writes as well as
  POSIX dir_fd writes; preserve no-overwrite behavior, exact bytes and closure
  on failure. Reconcile focused/native/full/hosted evidence before resolving the
  review, protected merge and topic pruning. [M-03, M-07, M-10, M-18; AC-02,
  AC-05, AC-12, AC-16]

  Windows qualification correction completed: the4a3 attribute-only handle
  admitted rename; ab156c16 adds list-directory access and passes the unchanged
  native replacement/cleanup assertions plus full Windows assurance. All final
  platform gates passed; review resolved before protected merge and pruning.


- [x] Extend the existing Gold metadata projector to independently verified
  operation-context Gold inputs. Retain canonical/direct/common provenance and
  exact inventories for all13 Parquet tables plus report/plots; preserve nullable
  publisher status counts and record kinds without invented statuses or period
  continuity. Reuse existing catalogue/schema/DCAT/PROV/card/citation/changelog/
  drill-through projections, version the new profile, and keep historical
  metadata bytes unchanged. Compose metadata into two Bronze-driven recovery
  repeats; qualify focused/native/full/hosted delivery before closure. No rights,
  citation authority, federation or analytical join is inferred. [M-10, M-14,
  M-16, M-18; AC-08, AC-12, AC-14, AC-16]


  Delivered PR #705 at0a534f13 after all required platform/analyze/lint gates,
  CodeQL and patch coverage passed on3f86e6fe. Source-regenerated native repeats
  and historical metadata parity passed; full2's receipt-only entropy failure
  and successful unchanged-scan/SBOM continuation retain exact scope. Fetched
  main contains checked head/merge with identical tree and zero unique changes;
  clean topic refs pruned, primary and originals retained.

- [x] Reconcile exact CPI source-metadata and period/rights census evidence with
  the existing June2017 reference qualification and fiscal CPI benchmark.
  Verify immutable current/versioned metadata, release-to-source links and
  response bindings; record source period-label coverage separately from the
  publisher's missing values. Reuse the approved fiscal policy and retain
  generic projection flags; do not create another benchmark or infer rights,
  a health-input deflator, fiscal alignment or analytical admission. Complete
  a bounded offline source-evidence contract, census reconciliation and repeat
  evidence before focused/full/hosted delivery. [M-02, M-04, M-06, M-12, M-16;
  AC-03, AC-04, AC-09, AC-10, AC-12, AC-16]


  The read-only contract and two actual-source offline repeats are qualified on
  38bc5158; current census now cites report0716432e and retains its prior snapshot.
  All14 originals/WARCs are retained in a permanent bounded CAS.82 focused checks,
  typing, Ruff, schemas and Conductor/hygiene pass. Full harness and hosted PR
  delivery remain pending under the existing serialized launch owner.

  Delivered PR #706 at4cf8d808 after all required platform/analyze/lint gates,
  CodeQL and patch coverage passed on730e12e8. Fetched merge and checked head
  share tree734e2f60; zero unique changes and clean topic refs pruned. The initial
  historical-review binding failure, focused recovery and remaining assurance
  remain scoped evidence; final hosted gates passed on the exact final tree.

- [x] Adopt independently regenerated CPI source-period evidence in the existing
  source-health producer and build tool through an explicit v2 profile. Preserve
  v1 bytes and other source/vintage states. Report449 represented quarter labels,
  422 numeric and27 publisherNA separately; retain exact source/body/vintage
  lineage and all rights, numeric-continuity and analytical boundaries. Qualify
  focused contracts, actual-source repeats and full/hosted delivery. [M-02,
  M-12, M-13, M-18; AC-09, AC-11, AC-12, AC-16]

  Delivered PR #707 at28e48f52 after all required platform/analyze/lint gates,
  CodeQL and patch coverage passed on27e79f3c. Native2 and exact-head full2 passed;
  native1 failure/partial evidence retained. Main ancestry and identical tree
  13f421b4 verified, zero unique changes, clean topic refs pruned.

- [x] Expose the existing source-regenerated operation-context metadata v5 profile
  through typed build/verify CLI commands and read-only MCP verification. Reuse
  the closed operation input spec, independent Gold/metadata pins, projector,
  verifier and output guard; dry-run must execute full source verification.
  Preserve v3/v4 envelopes, immutable-output refusal, source/Gold/output
  separation, rights and no-publication boundaries. Qualify focused/native/full/
  hosted delivery. [M-14, M-15, M-16, M-18; AC-12, AC-13, AC-14, AC-16]

  Native proof and63-file readback pass on e876eaf3. Full1's900-second timeout
  and unidentified F remain preserved; full2's7901tests and prior stages passed
  but a redundant receipt status label blocked the credential scan before SBOM.
  Label-only correction retains the result/log pins and all scanner rules;
  affected-stage recovery and hosted delivery remain pending.


  Delivered PR #708 at31ba7ee6 after seven named hosted checks succeeded on
  f0291547 and no review threads remained. Fetched main contains checked head
  and merge with identical cbaeb167 tree and zero unique changes. Primary checkout
  retained clean; local/remote/tracking topic refs absent. Local full1/full2 and
  docs-only affected-stage recovery remain separately scoped in the external
  reconciled receipt; the historical pending checkpoint is superseded by
  operation-metadata-operations-delivery-20261018.json.

- [x] Qualify exact publisher-generated health component-index exports for the
  source census. Retain native TQX separately from numeric CSV, verify actual
  capture response bindings and exact table/dimension/vintage/period identities,
  preserve missing observations and unflagged status, and bind rights observations
  to retained source evidence. Add the smallest offline evidence contract for
  qualified source cohorts and reconcile census gaps; do not select a health-cost
  deflator, infer full series identifiers, analytically admit values or change
  generic host rights policy. [M-02, M-04, M-06, M-12, M-16; AC-03, AC-04,
  AC-09, AC-10, AC-12, AC-16]


  Source-cohort qualification passes on c3e87580: two network-denied14-object
  repeats, reportbbd251a4, unchanged originals and independently reconciled counts.
  Exact full harness7916PASS/12skip and all downstream gates pass; native1 parser
  failure remains preserved. See component-index-source-assurance-20261018.json
  and component-index-source-evidence-20261018.md. Result-only documentation and
  hosted delivery remain pending; broader series admission/policy/rights gates
  are not closed by this census evidence.


  Corrected readable-summary producer and regenerated report fccc3850 pass native3
  and full2 on69afe04b (7916tests/12skips/all downstream gates). Source/query bytes
  unchanged, no scanner-policy exceptions. Initial proof/scan/full scopes remain
  separately recorded; see component-index-source-assurance-final-20261018.json.
  Final documentation checks and hosted delivery remain pending.


  Delivered PR #709 at6b8c2ee0 after seven named gates passed on7ada6fec,
  all review threads resolved and no current CodeQL alerts. Fetched merge and
  checked head share tree8d5fcaf1; zero unique changes; clean topic refs pruned.
  Native4 report equality and exact-head full3 (7917tests) retained; no scanner
  or branch-rule exceptions. See component-index-source-delivery-20261018.json.

- [x] Register the existing 2024/25 and2025/26 Supplementary Estimates summary
  profiles through common Bronze dispatch. Reuse exact source/vintage/locator,
  page and parser controls; share pure native extraction with the standalone
  normalizers, preserving their schemas, IDs, literal tokens, capital-injection
  flags, dash nulls and byte-identical existing outputs. Account for unselected
  pages/content explicitly; retain unknown/mismatched inputs as preserved-only.
  Qualify record/lineage equivalence, exact selection/refusal, repeat outputs and
  native old/new comparisons before full/hosted delivery. No currency inference,
  crosswalk, added totals, rights or analytical-policy change. [M-05, M-06,
  M-07, M-10, M-18; AC-03, AC-05, AC-08, AC-11, AC-16]


  Delivered PR #710 at02926da7 after all seven named checks passed onb1e00485,
  resolved review threads, fetched ancestry and identicald940tree. Zero unique
  changes; clean topic refs pruned; primary retained. Native2 baseline equality
  and full7922-test assurance retained, including native1 representation failure.

- [x] Register the pinned donor SQLite snapshot through common Bronze dispatch.
  Reuse the bounded in-memory SQLite admission and existing Silver construction;
  preserve all five table values, IDs, native lineage and standalone bytes.
  Reject altered bytes/schema drift and retain unsupported sources; do not
  reinterpret donor currency, periods, rights or historical differences. Verify
  fixtures, actual312-row pre-change equivalence and repeated products before
  full/hosted delivery. [M-05, M-07, M-10, M-18; AC-03, AC-05, AC-08, AC-16]


  Delivered PR #711 ate79c9089 after seven named checks passed on af9ec80e,
  all review threads resolved, fetched checked/merge ancestry and identical64b6
  tree. Zero unique commits; clean topic refs pruned; primary retained. Native
  312/1699 equivalence, full7926 and fixture-close affected10tests remain scoped.

- [x] Reconstruct the retained donor12stage evidence through the existing pinned
  replay recipe into two new exclusive permanent runs. Pin donor/candidate/Crown
  metadata and preserve all original Bronze bytes; verify739facts/50files,
  compare historical hashes honestly and recover exact per-stage receipts where
  reproducible. Retain missing historical outputs or differences explicitly;
  qualify only supported area bindings, with no global152worksheet semantic
  closure, historical value replacement or rights/publication change. [M-07,
  M-10, M-16, M-18, M-19; AC-05, AC-08, AC-12, AC-16]


  Delivered PR #712 at93c154cf after seven named hosted checks passed on3c77f691,
  all review threads resolved and fetched checked/merge commits share1a2564f6
  tree. Zero unique changes; clean topic refs pruned; primary retained. Exact
  reconstruction matches50oldfiles/12stagepins; qualified9stage partialbindings
  cover613facts while all158global units and rights/semantic gates stay open.

- [x] Expose the seven existing literal admissions through five exact-source
  common adapters. Compose chart/residual profiles sharing physical bytes into
  one closed source bundle, avoiding ambiguous registrations or partial profile
  omission. Share pure bounded admission/projection with existing standalone
  packages; preserve all329facts,5543lineage rows,606area dispositions, native
  output bytes and Crown observation context. Retain profile-scoped excluded
  formulas and whole-sheet remainders, unknown-source fallback, deterministic
  selection and provenance. No source acquisition, currency/period/rights or
  analytical mapping change. [M-05, M-07, M-10, M-18; AC-03, AC-05, AC-08,
  AC-16]


  Literal bundle native2 passes two runs with329facts/5543lineage/606complete
  areas and28historically identical native files per run. Full7951tests and
  all original gates pass on0c378f4e; hosted delivery remains pending. Preserve
  the initial dependency-initialization instrumentation failure and explicit
  verified UTC warmup boundary; no producer, rights or semantic change.


  Delivered PR #713 at9b5941e2 after all seven named checks passed on83adddd5,
  threads resolved and fetched checked/merge ancestry with identical893ca0f3
  tree. Zero unique commits; clean topic refs pruned; primary retained. Native
  parity and full7951 evidence remain scoped; no whole-unit/rights approval.

- [x] Expose the retained Fiscal2024 historical Health/GDP workbook through
  one exact-source common adapter using the existing bounded native parser.
  Preserve106facts,1143lineage rows,1503complete cell dispositions and six
  excluded sheets, exact lexical decimals/annotations/periods and standalone
  output bytes. Add pure snapshot extraction shared by the path writer; keep
  unknown bytes preserved-only and context explicit. This source is physically
  distinct from the Fiscal2025 Crown bundle; do not create competing handlers
  or infer currency, fiscal joins, cross-basis comparability or rights. Verify
  fixtures and two actual historical-pin replays before full/hosted delivery.
  [M-05, M-07, M-10, M-18; AC-03, AC-05, AC-08, AC-16]


  Native two-run parity passes106facts/1143lineage/1503cells/six excluded
  sheets and all four historical files exactly. Original full2 passes7954tests
  and all32gates on780f3040 after preserving/reconciling the one current census
  code pin. Failed full1 remains retained; hosted delivery remains pending.


  Delivered PR #714 at6ad51f9e after all seven named checks passed on a1ff0c71,
  review threads resolved and fetched checked/merge ancestry with equal2cb2da9b
  tree. Zero unique commits; clean topic refs pruned; primary retained. Native
  parity, preserved census history and successful full2 remain scoped evidence.

- [x] Compose the retained legacy BEFU2025/HYEFU2024 forecast summaries and
  detail profiles behind one selector per physical workbook using an explicit
  typed compound-result variant. Preserve separate native schemas, profile
  identities and complete lineage/disposition/excluded-sheet evidence; retain
  all existing v1 single results and standalone bytes. Reject unsupported
  consumers, ambiguous selectors, incomplete siblings and schema/profile drift.
  Verify four native profiles (180facts,1784lineage,4833profile dispositions,
  four forecast excluded-sheet entries), all16standalone files, two independent
  dispatch builds and original full/hosted gates. Counts are profile-specific
  interpretations, not unique physical cell coverage. No canonical, currency,
  period, mapping or rights promotion. See compound-native-recordsets-20261018.md.
  [M-05, M-07, M-10, M-18; AC-03, AC-05, AC-08, AC-16]


  Native composition now passes two actual-source replays with all 16 native
  files per run identical to the retained oracle. Original full validation on
  e596ccd2 passed all 32 stages and 7,993 tests (12 skipped). Native producers,
  source bytes and reference files are unchanged. Hosted delivery remains
  pending; the broader common-adapter and semantic tasks stay in progress.


  The final review found an unbound native metadata envelope after the earlier
  hosted checks passed. The guard stopped before merge. The corrected identity/
  schema/context checks now pass native2 and all 32 full stages on 1bbd8577:
  8,012 tests passed (12 skipped), with every native output byte unchanged.
  Fresh exact-head hosted assurance and protected delivery remain pending.


  Delivered PR #715 at 02ca851b after seven exact-head successes on 6de7028d,
  resolved metadata provenance review, strict protected merge and fetched
  ancestry/equal-tree/zero-unique/clean verification. Topic refs pruned; primary
  worktree retained. See compound-native-delivery-20261018.json.

- [x] Expose closed, read-only native workbook inspection through the existing
  CLI/MCP operation architecture. Resolve the two reviewed expense workbook
  identities from CAS; preserve compound/profile/schema/selection/count/hash/
  excluded-sheet/hold evidence in a bounded typed response without raw rows or
  caller paths. Preserve the existing single-profile HTTPS operation contract.
  Reuse strengthened compound admission; validate actual CLI/JSON-RPC parity,
  read-only behavior, bad inputs/fixity and sibling hold. Native/full and hosted
  qualification remain separate delivery gates. [M-05, M-07, M-15, M-18;
  AC-03, AC-05, AC-08, AC-13, AC-16]


  Native inspection now passes two actual-source, three-route replays with all
  16 original native files unchanged. Original full2 on 2aef585c passed all 32
  stages and 8,027 tests (12 skipped); full1 timing failures and bounded diagnosis
  remain retained, with no code or deadline changes. Owner terminal/kernel release
  verified. Exact-head hosted checks, review and protected delivery remain pending.
  See native-workbook-inspection-20261018.json for pinned evidence.


  PR #716 review found a Windows junction path bypass before merge. Preserve the
  earlier green evidence, keep this task in progress, and require a new qualified
  head after rejecting junctions as well as symlinks before the source read.
  Two regression controls fail on the prior guard; the focused suite now passes
  17 cases with two real NTFS cases pending Windows. Updated native/full and
  exact-head hosted qualification, review resolution and delivery remain open.


  Corrected source e1379ed3 now passes fresh native2 and all 32 original full3
  stages: 8,029 tests, 14 skipped, with unchanged native bytes and runtime limits.
  Preserve the exact overlapping-process chronology and owner terminal release.
  Local skips do not qualify the two real Windows junction cases; final hosted
  Windows, seven exact-head checks, review resolution and delivery remain pending.


  Delivered PR #716 at76bbc660 after seven successes on0d446471, resolved
  junction review and actual native Windows suite. Fetched checked/merge ancestry,
  equal1f1c4e29tree, zero unique commits and clean-main guards pass; topic refs
  pruned, primary retained. See native-workbook-inspection-delivery-20261018.json.

- [~] Reconcile Budget2024 expenditure/revenue release identity, periods,
  original-byte preservation and item-level rights evidence. Reuse the existing
  two locators and retained inventories; preserve edition/caveat distinctions.
  Capture only through the existing bounded preservation core without inheriting
  host-level licence eligibility as item adjudication. Native units/layout and
  canonical/analytical admission remain separately gated. [M-02, M-04, M-11,
  M-18; AC-03, AC-04, AC-09, AC-16]


  Exact Budget2024 expenditure/revenue originals are now privately preserved
  with HTTP200 and independently verified CAS/WARC/receipt bindings. Source
  workbooks admitted remain zero; native Explanation/layout/units and item-level
  rights review are the next bounded step. See budget-2024-capture-20261018.json.


Budget 2024 native inspection1 completed on f83c09e9: root35584 exit0,
lease released; both inventories repeat identically and both source hashes
remain unchanged. No canonical facts or rights admitted. Record structural
counts and private report hashes in budget-2024-layout-20261018.json. Next
read exact Raw Data headers, Intro notices and lower Explanation definitions;
resolve the actual revenue1005-row envelope against the existing1000-data-row
profile without truncation, vintage substitution or silently changing limits.


- [x] Add the hash-bound Budget 2024 revenue edition using the observed native
  definitions and June-year amount types, preserving all 1,004 occupied source
  rows. Keep the existing 2025/2026 1,000-row bounds unchanged; the reviewed
  2024 bound is edition-specific and no row is truncated. Retain literal $000,
  unknown ISO currency, source-row losses and original OOXML numeric tokens.
  Item notices/media evidence and canonical/publication claims stay separate.
  [M-03, M-04, M-06, M-11, M-18; AC-03, AC-04, AC-05, AC-16]


Local qualification passes on 64d40613: actual-source repeat/common parity
(66 facts, all 1,004 rows) and all 32 original harness stages. See
`budget-2024-revenue-qualification-20261018.json`. Exact-head hosted checks
and protected delivery remain pending; wider phase/rights/Gold gates stay open.


- [x] Review fix: expose budget-revenue-2024/v1 through the existing closed
  source-operation registry/vintage validation/result schema and CLI/MCP routes.
  Preserve source hash/locator binding, read-only MCP and explicit local writes.
  Verify actual-source entry paths and corrected original full harness before
  PR717 delivery. [M-04, M-07, M-15, M-18; AC-03, AC-04, AC-13, AC-16]


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


PR #717 delivered at bde4f721 after seven exact-head successes on f4c2b833,
resolved source-entry review and normal protected merge. Fetched head/merge
ancestry, equal fde19483 tree, zero unique commits and clean-main checks pass;
topic refs pruned and primary retained. See budget-2024-revenue-delivery-20261018.json.
The broader Budget2024 census remains in progress.

- [x] Add a pinned Budget2024 expenditure source profile through the existing
  adapter and CLI/MCP source-operation architecture. Preserve all 17 source
  columns, original OOXML amount tokens, parent/category/group/periodicity
  qualifiers, literal $000 and unknown ISO currency. Account for all 6,645
  occupied source rows and inventory-only sheets; do not aggregate parent and
  category rows or change legacy2025/2026 package contracts. Demonstrate actual
  source repeat stability and CLI/MCP preflight parity, then original full
  validation and protected delivery. [M-04, M-06, M-07, M-11, M-15, M-18;
  AC-03, AC-04, AC-05, AC-09, AC-13, AC-16]


Expenditure actual-source qualification passes on101af09/tree88a18dc:244facts,
6100lineage,6645rowdispositions, zero rejects. Actual CLI/MCP preflight and
explicit CLI write match the direct package; common facts/lineage/losses agree.
Three local originalfull runs are not qualified: timing checks(4/2workers) or
the original900s cap(1worker). Preserve failed evidence; no quality setting is
weakened. Qualify the same fullchecker through existing exact-head hosted lanes,
then seven successes/resolved reviews/protected delivery. Task remains[~].


PR #718 delivered at `d95a76a8` after seven exact-head successes on
`9d882d46`. All 32 hosted stages pass on three platforms. Local timing failures
are preserved. Fresh fetched ancestry, equal `7d6b0fea` tree, zero unique
commits and clean-main checks pass; topic refs pruned, primary retained.
See `budget-2024-expenditure-delivery-20261018.json`.

- [x] Reconcile the registered Budget 2023 expenditure/revenue release and
  retained captures. Record exact identity, periods, units, definitions, rights
  notices and layout; preserve eligible originals through the existing capture
  core only where reuse evidence does not identify them. Admit native source
  profiles only after edition-specific contracts and repeat-build evidence.
  Keep currency, period starts, joins and publication unqualified where source
  evidence is absent. [M-02, M-04, M-06, M-07, M-11; AC-03, AC-04, AC-05, AC-09]


Budget 2023 expenditure/revenue are privately preserved with HTTP200 and
independent CAS/WARC/receipt verification. See budget-2023-capture-20261018.json.
The exact working census is retained at3ca17fe4; no source-layout or numeric
admission follows from transport. Native definitions/layout have been inspected for both originals. Revenue now
qualifies65Health facts/1,040lineage with full1,013-row accounting, repeat and
CLI/MCP parity; see budget-2023-revenue-native-20261018.json. Full assurance
and protected delivery remain pending. Expenditure normalization, source rights
eligibility, and broader semantic/analytical gates remain open.


- [x] Deliver the pinned2023revenue profile through protectedPR719 and prune
  its proven-integrated topic refs; retain the primary and original evidence.
- [x] Admit pinned Budget2023expenditure through the shared literal source
  contract, retaining2024byte parity. Qualify native repeats and common/CLI/MCP
  parity, run the full harness and deliver a focused protectedPR.
  [M-02, M-04, M-06, M-07, M-11; AC-03, AC-04, AC-05, AC-09]


Budget2023native source profiles delivered throughPR719/720. This closes the
bounded Budget-family census/normalization slice; other2023source families,
rights eligibility, joins and wider phase gates remain unqualified.

- [x] Diagnose the three retained encrypted-PDF layout exclusions using the
  default reader without credentials. Repair false exclusions only where normal
  page access is evidenced; preserve genuine password-required exclusions and
  original bytes. Reuse existing baselines and verify unchanged previously
  parsed descriptors. [M-02, M-04, M-11, M-18; AC-03, AC-04, AC-09, AC-16]

The PDF parser fix qualifies all59retained layouts with two byte-identical
builds, all56prior rows unchanged and zero unavailable. See
readable-pdf-layout-qualification-20261018.json. Original local/hosted32stage
assurance and protectedPR721 delivery passed; the bounded PDF task is complete,
while broader workbook and source-health coverage remain open.

Local original32stage assurance and v1/v2 source-health integration pass;
see readable-pdf-layout-assurance-20261018.json and
readable-pdf-source-health-qualification-20261018.json. Both report modes
repeat with only3PDFstate changes against the current-context control;
CPI449label evidence is retained. Exact-head hosted/protected delivery passed
throughPR721; see readable-pdf-layout-delivery-20261018.json.


- [~] Reconcile the registered Budget2022 expenditure/revenue source pair
  against its exact official release, preserved source bytes, periods, native
  definitions/layout and item-level rights evidence. Reuse existing retained
  captures where verified; preserve new eligible bytes only through the bounded
  capture core with CAS/WARC/readback. Keep source observation, literal Silver
  eligibility and analytical/rights admission separate.
  [M-02, M-04, M-06, M-11, M-18; AC-03, AC-04, AC-09, AC-16]

Budget2022 pair preservation and native structure/definitions are verified;
17/8headers and6568/1015occupied rows. The page transport403 is retained and
Conductor consulted. Next add dedicated hash-bound2022profiles through the
existing parsers, keeping previous profiles/output bytes unchanged; qualify
actual repeats/common/CLI/MCP, run the harness and deliver a focusedPR before
closing this bounded slice. No rights, currency or period-start inference.

Budget2022 actual profiles qualify307expenditure/64revenue observations with
all6568/1015source rows accounted, no rejected rows, two byte-identical builds
and CLI/MCP/common parity. Prior2024expenditure/2023revenue packages reproduce
all four files. See budget-2022-native-qualification-20261018.json. Native page
HTTP403 remains a precise route-specific gap; full and protected delivery
remain pending before closing this bounded slice.

The required original local harness ran onf479a3bd and reached99% before
the unchanged900s test cap. No local full pass/coverage claim; all6newcases
passed with0observedfailures. Native/repeat/prior/source/code pins remain
unchanged. See budget-2022-assurance-20261018.json. Deliver a focusedPR with
explicit disclosure; require original all32stages on3clean hosted platforms,
7exact-head checks and resolved review before protected merge/prune.


- [x] Deliver both pinned Budget2022 source-native profiles and repaired public
  routing with all32original hosted stages on3platforms,7exact-head checks,
  resolved review and normal protected merge/clean topic pruning. PR722 merge
  95f9f638; see budget-2022-delivery-20261018.json. Keep broader census [~]:
  native page403, rights, canonical/Gold and analytical holds remain explicit.
  Both original local timeouts are retained; second attempt had2FAILED entries.
  Both affected modules pass140tests with original seed/two workers; this is
  no local full-pass claim and earlier timeout location remains unproven.
  [M-05, M-07, M-15, M-18; AC-03, AC-05, AC-13, AC-16]

- [~] Keep Context Gold input-spec inspection independent of plotting/product
  reconstruction startup. Reuse existing reader, source-path guards and native
  products; retain the original FIFO10s and full900s/80% gates. Establish a
  reader-only dependency boundary, verify actual regular/FIFO paths and prove
  supported Gold outputs unchanged before focused protected delivery. This
  scoped Phase8 repair does not complete the broader operations checklist.
  [M-15, M-18; AC-13, AC-16]


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

- [ ] Diagnose full-source Context Gold CLI/MCP preflight timing against the
  retained5-input/615-observation package. Distinguish import, source
  regeneration and rendering cost; preserve no-write semantics, complete
  controls, source facts and the existing probe/test/full limits. Reader-only
  dependency isolation does not close this broader operational item.
  [M-15, M-18; AC-13, AC-16]


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

- [x] Qualify retained five-input Context Gold original console and initialized read-only stdio MCP replay with unchanged30s response bounds; preserve earlier timeout receipts (context-reader-startup-replay-20261019-v1.json). Broader Phase8 remains open.

- [x] Route hash-bound Budget2023/2024 expenditure through existing shared registry and legacy normalizer; require fact/four-file parity with already-qualified profiles and retained native packages. [M-05, M-06, M-07, M-15; AC-05, AC-11, AC-13]

- [~] Reconcile the40 registered annual Budget2007–2026 workbook resources as a source-separated census cohort; verify retained capture/CAS/WARC/native evidence before bounded missing-source capture, record exact periods/units/rights and reason-coded gaps without rewriting producer checkpoints or whole-edition completion. [M-02, M-03, M-04, M-06, M-11; AC-03, AC-04, AC-09, AC-16]

- [x] Unblock the annual Budget cohort with explicit rights-unassessed preservation-only capture, mode-bound resume/orphan recovery and opaque legacy Excel transport; enforce the existing WARC read bound before allocation. Preserve legacy defaults and all provenance/admission gates. [M-03, M-04, M-11, M-15; AC-03, AC-04, AC-13, AC-16]

  Assurance refinement: exact proof-root candidate/document adjudication, retaining original qualification bytes and fail-closed unknown-candidate checks; three-platform hosted requalification remains required.

- [~] Reconcile retained bindings for four official Budget2007/2012/2016/2017 publication pages and nine linked workbook candidates; capture only missing preservation evidence, retain original404 observations and record the additional departmental-statements variant and definition/rights gaps. [M-02, M-03, M-04, M-06, M-11; AC-03, AC-04, AC-09, AC-16]

- [~] Reconcile the next19official locator candidates for Budget2008–2011/2013–2014, preserving eight intended expenditure/revenue gaps and five additional departmental-statements variants; reuse retained bytes/bindings, record page/definition/rights gaps and capture only missing eligible originals. [M-02, M-03, M-04, M-06, M-11; AC-03, AC-04, AC-09, AC-16]

- [x] Adjudicate the exact immutable archive-verification boolean-field entropy candidate using document/candidate pins and the existing negative guard; preserve producer bytes and all scanner scope/thresholds before full assurance. [M-11, M-15; AC-13, AC-16]


- [x] Qualify a separate hash-bound read-only legacy XLS inspector for the32 preserved OLE workbook candidates. Record the reader decision before adoption; preserve source bytes and existing XLSX contracts, bound traversal/previews, expose stored-value and structural-loss limitations, and repeat the native inspection without numerical/rights admission. [M-02, M-06, M-11, M-15; AC-03, AC-09, AC-13, AC-16]

- [x] Reject a decoded legacy worksheet with an empty title before emitting inventory, matching the declared nonempty-title schema; preserve source bytes and valid-source outputs, qualify the correction, then require fresh exact-head assurance before protected delivery. [M-06, M-11, M-15; AC-09, AC-13, AC-16]

- [x] Promote the preserved Budget2021 expenditure/revenue pair through hash-pinned source-native Silver profiles, retaining edition-specific definition coordinates, exact numeric tokens, full row accounting and CLI/MCP/common-dispatch parity. Preserve rights/currency/comparability holds and qualify repeat builds without altering later-edition outputs. [M-02, M-05, M-06, M-07, M-11, M-15; AC-03, AC-04, AC-09, AC-13, AC-16]

- [x] Remove repeated workbook decoding within one verified Budget extraction operation using a SHA-bound scoped inspection context; preserve all member/expansion/scan/formula-cache checks and selection receipts, no persistent/path-keyed cache. Reuse the loaded formula workbook and computed inventory only for identical bytes; verify refusal/cleanup/output parity and actual30s preflight. [M-03, M-06, M-07, M-15; AC-03, AC-09, AC-13, AC-16]

- [x] Retain full formula/structure inventory while reading the cached-value pass with streaming cells bounded by the already checked worksheet extents; skip cached sheets without formula coordinates and preserve cache state/type/order and all prior output bytes. Qualify actual30s entry points after native2/3 CLI timeouts. [M-06, M-15; AC-09, AC-13, AC-16]

- [x] Invalidate completed inspection owners across copied Python contexts before protected delivery; retain current-operation reuse and close/reset behavior. Extend the existing scope regression without extra cases, repeat native compatibility/timing and original full assurance, and require new-head hosted checks. [M-03, M-06, M-15; AC-03, AC-09, AC-13, AC-16]

- [x] Promote the preserved Budget2020 expenditure/revenue pair through exact hash/locator/vintage profiles, using the completed two-repeat metadata preflight and edition-specific definition coordinates. Preserve source periods, labels, units, literal numeric tokens, every row and lineage; verify prior profiles, operations and repeat-build parity with rights/currency/start-date/join holds unchanged. [M-02, M-05, M-06, M-07, M-11, M-15; AC-03, AC-04, AC-09, AC-13, AC-16]


- [x] Reconcile complete Explanation-sheet observations for all32 preserved Budget2007–2019 BIFF8 candidates, reusing earlier qualified windows; record exact source/edition/period/definition coordinates,23 explicit amount-scale statements,nine unit gaps and the Budget2014 revenue edition conflict. Verify all cell/digest/reference and raw-header evidence without numeric/formula/rights/currency/start-date/join admission; run original validation and deliver a focused census PR. [M-02, M-04, M-06, M-11; AC-03, AC-04, AC-09, AC-16]


- [x] Implement a separately versioned BIFF8 stored-integer evidence contract and the exact Budget2019 expenditure/revenue source pair. Retain original encoded bytes, stream/record/cell identity and deterministic witnesses; preserve OOXML literal-token contracts and all rights/unit/currency/period/edition/join holds. Supply typed facts plus complete companion evidence/lineage/dispositions through the existing native multi-recordset boundary, source operations and CLI/MCP; specify and test the witness-aware downstream mapping boundary without impersonating source text tokens. Qualify real encoding/refusal fixtures, complete row accounting, repeat/source-operation/native parity, unchanged prior packages, actual30s preflights and original/full protected delivery. [M-05, M-06, M-07, M-10, M-11, M-15; AC-03, AC-04, AC-05, AC-09, AC-11, AC-13, AC-16]


- [x] Integrate the admitted Budget2019 BIFF8 pair into canonical v3 and existing Gold export/query contracts, replaying the complete pinned Silver package against Bronze and retaining all numeric witnesses and source field lineage. Keep lexical tokens null, preserve source-separated identity rows without aggregation/netting, qualify repeat builds and tamper refusal, run original validation and protected PR/merge/prune. [M-05, M-06, M-07, M-10, M-11, M-13, M-16; AC-05, AC-09, AC-11, AC-16]


- [x] Rebuild the admitted Budget2019 BIFF8 pair from Bronze into fresh source-native Silver, witness-aware canonical and existing Gold/metadata recovery. Add an explicit versioned seven-source canonical recovery cohort while preserving the five-source v1 route and its byte contracts; wire the complete recovery harness to the expanded cohort, retain exact observation tokens/witnesses/lineage and require two empty-derivative repeat builds without retained Silver consumption. Reconcile bounded native evidence, required original validation and protected PR delivery. [M-05, M-07, M-10, M-13, M-16, M-18; AC-08, AC-11, AC-12, AC-16]

  Native unblocker: the original Budget2025 legacy source build exceeds120s
  during repeated workbook decoding in selection/inventory/extraction. Reuse
  the existing exact-byte operation-local inspection across legacy expenditure
  and revenue paths; retain all guards, output bytes and scope invalidation.
  Qualify parser decode counts and actual source/output parity before advancing.


- [x] Qualify the next eligible Budget2018 expenditure/revenue BIFF8 pair from the existing complete definition/header census. Verify retained originals, exact source/edition/period/unit bindings and every selected Health numeric field with the existing stored-integer evidence contract before promotion. Add edition-specific source-native profiles and native/operation contracts only for admissible rows; preserve all2019 package bytes and existing rights/currency/start-date/aggregation/join holds. Run focused and original assurance and protected PR delivery. [M-02, M-05, M-06, M-07, M-11, M-15; AC-03, AC-04, AC-05, AC-09, AC-11, AC-13, AC-16]


- [x] Integrate the admitted Budget2018 pair into witness-aware canonical, source-separated multi-vintage Gold and complete Bronze recovery/metadata builds. Resolve only exact trusted source profiles, retain per-edition transformation identity and every numeric/field link; reject duplicate kind/vintage packages. Keep all2019 canonical/Gold and default five-/seven-source recovery bytes unchanged. Add an explicit versioned nine-source cohort, demonstrate repeated full products/query/metadata recovery, preserve reader/source/interface/stage limits and run original validation plus protected delivery. [M-05, M-06, M-07, M-10, M-11, M-13, M-16, M-18; AC-05, AC-08, AC-09, AC-11, AC-12, AC-16]

  Native downstream qualification passed on46ef125d:83 input/61 Gold files repeat,
  ten exact queries, three metadata packages/15 recordsets/1,948 rows, all prior
  47/65/60-file byte contracts unchanged. Reader failure resolved with complete
  hashed drillthrough companion. Original final-tree harness and protected PR
  delivery remain pending; whole Health track remains in progress.

  Protected delivery736 is verified on origin/main asf16a9bab: local original32
  stages pass (8,181 tests), all32 stages pass on all three hosted platforms,
  all seven checks green, review has no findings, strict rules unchanged;
  clean topic pruned with zero unique commits/patches. See the736 receipt.

- [x] Qualify the preserved Budget2017 expenditure/revenue pair against the existing full definition/header census and stored-integer evidence contract. If admissible, add exact edition-specific profiles and full source/operation/native/CLI/MCP parity; carry admitted facts, witnesses and lineage through canonical, multi-vintage Gold and explicit eleven-source recovery/metadata. Preserve default five-/seven-/nine-source output bytes, source-separated semantics, original observation tokens and all time/size/rights/period/currency/donor holds. Require repeated fresh builds, original validation and protected delivery. [M-02, M-05, M-06, M-07, M-10, M-11, M-13, M-15, M-16, M-18; AC-03, AC-04, AC-05, AC-08, AC-09, AC-11, AC-12, AC-13, AC-16]

  Source/native qualification and complete11-source product recovery passed
  on6b6c2cba:101 input/61 Gold files repeat, ten exact query readbacks, three
  metadata packages/15 recordsets/2,328 rows; all prior47/65/83 input and60/61
  Gold byte contracts unchanged. Source/reader/interface/stage bounds intact.
  See budget-2017-biff8-native-qualification-20261021.json and
  biff8-2017-products-native-20261021.json. Original final-tree assurance and
  protected delivery remain pending; the wider Health track remains in progress.

- [x] PR737 review fix: give recovery v4 its distinct canonical schema URI and verify v3/v4 registry resolution and cross-version refusal. Preserve every native/source/product byte and all policy bounds; repeat original exact-tree validation and hosted checks before protected delivery. [M-06, M-13, M-16; AC-09, AC-12, AC-16]

  Delivery737 is verified on origin/main ascabd5b70: exact corrected head
  dc1afb5f passed local original32 stages (8,189 tests) and all32 on all three
  hosted platforms; seven checks green, strict rules unchanged, historical P2
  registry finding resolved and self-reviewed with actual native readback.
  No new cloud pass claimed. Clean topic pruned, zero unique commits/patches;
  primary checkout, runtime and49-file mirrored delivery proof retained.

- [x] Qualify preserved Budget2016 expenditure/revenue against complete retained source/header/definition evidence and the closed stored-integer contract. For eligible originals, add exact source profiles and full native/operation/CLI/MCP parity; extend canonical/Gold and explicit thirteen-source recovery/metadata while preserving all prior cohort/source/product bytes. Require distinct schema identity, independent multi-version registry resolution, complete witness/row accounting, repeated fresh builds, original final-tree validation and protected delivery. Keep all120s/30s/900s/4MiB/128MiB bounds,80percent floor and source/rights/period/currency/donor/comparability holds. [M-02, M-05, M-06, M-07, M-10, M-11, M-13, M-15, M-16, M-18; AC-03, AC-04, AC-05, AC-08, AC-09, AC-11, AC-12, AC-13, AC-16]

  Complete native13-source qualification passed on cd912dfc:119 input/61
  Gold files repeat, ten exact queries, full metadata15 recordsets/2,705 rows.
  Prior47/65/83/101 input and60/61/61 Gold file bytes unchanged; all five actual
  schemas independently resolve with cross-version refusal. Source/size/time
  bounds and holds remain. Original final-tree harness and protected delivery
  pending; see biff8-2016-products-native-20261021.json.

- [x] PR738: enforce the complete2016–2019 v5 cohort before reads and in schema; verify fresh original recovery and exact-head protected delivery.

  Delivery738 is verified on origin/main as5ad4f654: all32 local stages
  (8,198 tests) and all32 stages on all three hosted platforms, seven green
  checks, strict rules unchanged, review finding resolved after actual repeated
  Bronze recovery.119 input/61 Gold files repeat; all1,037 earlier native proof
  files unchanged. Clean topic pruned and46-file mirrored proof retained.

- [~] Qualify preserved Budget2015 expenditure/revenue from the completed census. Verify every Health numeric field, complete row/definition/header accounting and exact edition/period/unit evidence. Admit only source-backed profiles, explicitly retaining absent expenditure minister/portfolio dimensions as null without invented lineage. Carry eligible facts and complete witnesses through native/operations/CLI/MCP, canonical/Gold and explicit complete fifteen-source v6 recovery/metadata. Preserve prior v1–v5 selection and byte contracts, enforce complete new cohorts, repeat fresh builds, run original final-tree validation and protected delivery before pruning. Keep all source/interface/stage/size/coverage/rights/currency/period/donor/comparability holds. [M-02, M-05, M-06, M-07, M-10, M-11, M-13, M-15, M-16, M-18; AC-03, AC-04, AC-05, AC-08, AC-09, AC-11, AC-12, AC-13, AC-16]

- [~] Budget2015 bounded review: preserve the existing profile positional constructor and require all fifteen named v6 source/profile bindings; qualify fresh Bronze replay, all six schemas and exact-tree protected delivery.

- [~] Resolve the newly published certifi advisory GHSA-6q48-6c7w-9gw2 that blocks the original harness: pin the patched2026.10.19 release, preserve TLS verification/audit/branch protections and all prior evidence, verify a one-package lock diff, run fresh native recovery against all qualified output hashes and repeat original final-tree/hosted assurance.

- [~] Diagnose the Windows-only nine-finding audit failure from actual retained package/advisory data. Preserve the failed job and all earlier passing gates, add bounded diagnostic receipt retention, resolve the real dependency/runtime cause and remove temporary duplicate audit work. Keep original validation, audit, TLS and branch protections unchanged; require final exact-head green checks before merge/prune.

- [~] Resolve the nine actual Pillow12.3.0 findings identified by the retained Windows receipt using fixed13.0.0. Keep all gates/TLS unchanged, remove the temporary duplicate audit, retain per-platform receipts, verify a targeted lock delta and full fresh native data/PNG/metadata/prior-cohort byte parity under the updated image runtime before original final-tree and hosted assurance.

- [x] Pillow13 native full20-stage requalification: all137 input/61 Gold files including34 PNGs identical; prior original evidence and runtime pins verified. Final original harness and hosted delivery remain pending.
