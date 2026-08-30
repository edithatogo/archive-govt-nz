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

- [x] Freeze the donor tree as the seed inventory, including code, documents,
  SQLite, plots and all eight source originals. [M-01, M-02; AC-01, AC-03]
- [x] Enumerate the Treasury historical Vote Health index and all retrievable
  Estimates/Supplementary Estimates across its observed 1998–2026 span; record
  exact edition, URL, media type, rights evidence and gap disposition. [M-02,
  M-11; AC-03, AC-09]
- [ ] Enumerate annual Budget expenditure/revenue workbooks, BEFU/HYEFU
  charts/core Crown expense/forecast files, the current Fiscal Time Series,
  Ministry of Health Vote Health series and Pharmac CPB series. Include Budget
  2025 seed inputs and Budget 2026 successors without assuming identical
  schemas. [M-02, M-11; AC-03, AC-09]
- [ ] Enumerate the exact official CPI, QES wage, population, GDP and Crown
  expense series needed for approved derived measures; reject discovery leads
  that lack a stable definition or join. [M-02, M-12; AC-03, AC-10]
- [ ] Evaluate published aggregate Health Survey indicators as a non-blocking
  Should item; include only if a documented analytical question, stable
  time/geography contract and public rights evidence exist. [S-05; AC-10]

### 1.3 Characterize every donor binary and derivative

- [ ] Add fixtures/contracts for safe ZIP/workbook inventory, archive-bomb and
  path controls, sheet/range discovery, formulas/cached values, hidden content,
  named ranges, tables, charts, external links, macros and unsupported parts.
  [M-07, M-18, S-03; AC-03, AC-16]
- [x] Produce a machine-readable sheet/table/range census for all seven donor
  workbooks and a page/structure census for the donor PDF, without changing
  their bytes. [M-03, M-07, S-03; AC-02, AC-03]
- [x] Characterize the five-table SQLite schema, row order/keys, types, nulls,
  values and totals as parity fixtures. [M-08; AC-06, AC-11]
- [ ] Characterize the intended behavior and failure behavior of
  `inspect_excel.py`, `process_data.py` and `run_analysis.py`, including the
  known compile failure, swallowed exceptions and positional heuristics.
  [M-09, M-18; AC-07, AC-16]

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

- [ ] Verify every discovered item has exactly one disposition and every donor
  binary/data area has an inventory result; report uncertainty and gaps rather
  than inferring completeness. [M-01, M-02, M-07; AC-01, AC-03, AC-09]
- [ ] Run focused format/security/property checks, self-review and the full
  repository harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 2 — Bronze zero-loss preservation

### 2.1 Bronze integrity contracts first

- [ ] Add failing tests for streaming single-pass ingestion, expected-length
  mismatch, SHA-256/BLAKE3/CID identity, CAS deduplication, atomicity, WARC
  linkage, resume, interruption, unchanged/changed observations, corrupt ZIPs,
  withdrawal, restriction and tombstones. [M-03, M-04, M-18, S-01, S-02;
  AC-01, AC-02, AC-04, AC-16]
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

- [ ] Apply per-resource preflight rights/access/size/type checks and capture
  every eligible census item with HTTP/WARC evidence; retain metadata-only or
  tombstone records for non-eligible and unavailable items. [M-02, M-03, M-04,
  M-11, M-12; AC-02, AC-04, AC-09]
- [ ] Record heartbeats, retries, source replacements and immutable versions;
  never let a current workbook replace a historical edition. [M-02, M-04,
  M-15, S-04; AC-04, AC-09, AC-13]
- [ ] Confirm Git contains manifests/schemas/evidence only, not source payloads
  or large generated derivatives. [M-03, M-18; AC-02, AC-16]

### 2.4 Phase review and checkpoint

- [ ] Run CAS/WARC/manifest validation, property and mutation lanes, donor
  reconstruction, interruption/resume and restriction negative paths. [M-03,
  M-04, M-16, M-18; AC-01, AC-04, AC-12, AC-16]
- [ ] Self-review and run the full repository harness; record which source
  states are observed, captured or still gated. [M-18, M-19; AC-16]

## Phase 3 — Silver schema and extraction foundation

### 3.1 Schema contracts first

- [ ] Add failing JSON Schema/Arrow/Parquet fixtures for the eight required
  `health_appropriations` record sets, versioning, stable IDs, fixed-precision
  money, null reasons, units, vintages, bitemporal fields, rights and lineage.
  [M-05, M-06, M-18; AC-05, AC-16]
- [ ] Add negative fixtures for binary-as-text decoding, unknown layouts,
  ambiguous units, duplicate keys, incompatible periods, missing lineage,
  formula/cached-value ambiguity and unjustified classification mappings.
  [M-05, M-06, M-07, M-18; AC-05, AC-11, AC-16]

### 3.2 Implement the domain and adapter protocol

- [ ] Register the dedicated health-appropriations domain and versioned
  multi-recordset schemas without weakening other domain contracts. [M-05;
  AC-05]
- [ ] Implement safe workbook, CSV, PDF-table and SQLite adapter interfaces
  that consume Bronze objects and emit records plus loss-accounting and field
  lineage. Unknown formats remain `preserved_only`. [M-05, M-07; AC-03, AC-05]
- [ ] Implement stable dimension and mapping contracts for vote,
  appropriation, department, portfolio, amount type, functional/economic
  classification, measure, unit and period. [M-06; AC-05, AC-11]

### 3.3 Determinism and drift hardening

- [ ] Add schema fingerprints, adapter selection evidence, deterministic
  ordering/serialization, source-layout drift reports and fail-closed unknown
  layout handling. [M-05, M-07, M-18, S-04; AC-03, AC-05, AC-16]
- [ ] Demonstrate repeat normalization yields identical manifests and Parquet
  content identity for the same inputs/environment. [M-10, M-16; AC-08,
  AC-12]

### 3.4 Phase review and checkpoint

- [ ] Run schema, golden, property, mutation, archive-safety, typing and focused
  coverage gates; review binary preservation and lineage boundaries. [M-18;
  AC-05, AC-16]
- [ ] Run the full repository harness and record paired evidence. [M-18,
  M-19; AC-16]

## Phase 4 — Donor extraction and functional parity

### 4.1 Donor normalization tests first

- [ ] Create red/golden tests for the donor's fiscal spending, GDP,
  appropriation and HYEFU/BEFU summary extraction using Bronze-derived test
  fixtures; cover headers, footers, blanks, formulas, duplicates, units and
  source-layout failures. [M-07, M-08, M-18; AC-03, AC-06, AC-16]
- [ ] Create a row-level parity oracle for all five SQLite tables/312 rows and
  a repair-ledger schema requiring source coordinates and rationale for every
  deviation. [M-08, M-18; AC-06, AC-11, AC-16]

### 4.2 Build source-faithful donor Silver records

- [ ] Normalize all in-scope donor workbook data areas into the dedicated
  record sets; attach field/cell lineage and reason-coded exclusions. [M-05,
  M-07; AC-03, AC-05]
- [ ] Reconcile against the donor SQLite derivative, preserve the observed
  donor tables, and resolve every difference through a test-backed repair
  ledger. [M-08; AC-06, AC-11]

### 4.3 Replace donor utilities and analyses

- [ ] Implement a typed workbook/source inventory CLI equivalent to
  `inspect_excel.py`, with structured output and bounded failures. [M-09,
  M-15; AC-07, AC-13]
- [ ] Implement the raw-to-Silver pipeline equivalent to `process_data.py`;
  regression-test the compile defect, positional heuristics and swallowed
  exceptions rather than retaining them. [M-09, M-18; AC-07, AC-16]
- [ ] Generate the five-table SQLite compatibility database from canonical
  Parquet and validate schema/row/value parity or approved repairs. [M-08,
  M-09, M-10; AC-06, AC-08]
- [ ] Implement structured equivalents of `run_analysis.py` for long-term
  nominal trends, year-on-year growth, GDP share, recent appropriation
  breakdown and classification trends. [M-09, M-13; AC-07, AC-08]
- [ ] Reproduce all six donor plots with semantic parity contracts covering
  query inputs, filters, series, units, labels and rendering parameters; retain
  donor PNGs unchanged in Bronze. [M-03, M-09, M-13; AC-02, AC-07, AC-08]

### 4.4 Phase review and checkpoint

- [ ] Run the 23-file, 312-row, four-analysis-family and six-plot parity suites,
  plus deterministic rebuild and unsupported-layout tests. [M-01, M-08,
  M-09, M-16; AC-01, AC-06, AC-07, AC-12]
- [ ] Self-review, full harness, and paired evidence; no parity claim may hide
  an unexplained difference. [M-18, M-19; AC-16]

## Phase 5 — Longitudinal Silver expansion and contextual data

### 5.1 Source-family contracts first

- [ ] Add versioned fixtures for each approved Vote Health, Budget,
  BEFU/HYEFU, Treasury fiscal, Ministry Vote Health, Pharmac CPB, CPI, wage and
  population layout before enabling its adapter. [M-06, M-07, M-11, M-12,
  M-18; AC-05, AC-09, AC-10, AC-16]
- [ ] Add gap, revision, supersession, incompatible-classification and
  cross-source variance tests for multi-vintage series. [M-06, M-11, M-12,
  M-18; AC-09, AC-11, AC-16]

### 5.2 Normalize direct official datasets

- [ ] Promote eligible Vote Health Estimates/Supplementary Estimates and
  annual Budget expenditure/revenue data from Bronze to Silver, preserving
  source-specific labels and explicit coverage gaps. [M-05, M-06, M-11;
  AC-05, AC-09]
- [ ] Promote BEFU/HYEFU, historical fiscal indicators and Ministry Vote
  Health series with compatible-but-distinct series definitions and vintage
  relationships. [M-05, M-06, M-11; AC-05, AC-09, AC-11]
- [ ] Promote Pharmac CPB series with its policy scope and time basis. [M-05,
  M-06, M-11; AC-05, AC-09]

### 5.3 Normalize analytical context

- [ ] Promote exact CPI, wage, population, GDP and total/core Crown expense
  observations required by Gold formulas, with base/definition/vintage
  metadata. [M-05, M-06, M-12; AC-05, AC-10]
- [ ] If S-05 passed its scope/rights gate, add the aggregate Health Survey
  adapter and explicit time/geography alignment; otherwise record its deferred
  disposition without blocking the Must scope. [S-05; AC-10]

### 5.4 Phase review and checkpoint

- [ ] Generate source-health, temporal coverage, layout drift, rights and
  reconciliation reports; verify every target vintage has an explicit state.
  [M-02, M-11, M-12, S-04; AC-09, AC-11]
- [ ] Run focused adapters, property/mutation checks, self-review and the full
  repository harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 6 — Gold analytical products

### 6.1 Analytical contracts first

- [ ] Add DuckDB query golden tests for nominal, real, per-capita, GDP share,
  total/core Crown share, budget-versus-actual, revisions, classifications,
  department/portfolio and CPB views. [M-10, M-13, M-18; AC-08, AC-10,
  AC-11, AC-16]
- [ ] Add invariant/property tests for denominator identity, CPI base changes,
  financial-year alignment, additive/non-additive measures, revision isolation,
  rounding and incompatible series. [M-06, M-12, M-13, M-18; AC-10, AC-11,
  AC-16]

### 6.2 Build marts, quality products and reports

- [ ] Build versioned Parquet dimensions/facts and DuckDB views for the
  approved analytical measures, retaining input record IDs and formula
  metadata. [M-10, M-13; AC-08, AC-10]
- [ ] Build coverage, completeness, reconciliation, source-health,
  classification-drift and revision reports with defined thresholds. [M-13,
  S-04; AC-11]
- [ ] Generate deterministic plots, structured summaries and consumer examples
  from the same queries; make source drill-through available. [M-09, M-10,
  M-13, S-06; AC-07, AC-08]

### 6.3 Phase review and checkpoint

- [ ] Reconcile Gold totals against source, donor and cross-source controls;
  inspect classification/coverage caveats and prohibit causal/forecast claims.
  [M-08, M-11, M-12, M-13; AC-06, AC-10, AC-11]
- [ ] Run deterministic query/plot tests, self-review and the full repository
  harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 7 — Platinum metadata, federation and discovery

### 7.1 Metadata and rights contracts first

- [ ] Add failing contracts for schema-as-code, DCAT, Croissant, RO-Crate,
  PROV, estate cards, mixed/per-resource licensing, citations and fail-closed
  release readiness. Include missing, conflicting and incompatible rights
  states. [M-04, M-14, M-17, M-18; AC-04, AC-14, AC-16]
- [ ] Add federation fixtures for namespace, versioned key, mapping method,
  confidence, period and lineage; reject live-runtime or unproven mappings.
  [M-14, M-18; AC-14, AC-16]

### 7.2 Produce governed projections

- [ ] Generate and validate metadata, cards, citations, changelogs, catalogue
  and source drill-through records from actual layer manifests. [M-14, S-06;
  AC-14]
- [ ] Add rebuildable federation tables for approved links to
  `reimbursement-atlas` and `global-medicines-atlas`; preserve unmatched and
  ambiguous mappings. [M-14; AC-14]
- [ ] Evaluate graph/vector projections only as non-authoritative Could work
  after a demonstrated query/discovery benefit and pinned reproducibility
  contract. [C-01, C-02; AC-14]

### 7.3 Phase review and checkpoint

- [ ] Review every metadata-level rights statement against resource evidence;
  reject hard-coded blanket licensing and unsupported federation claims.
  [M-04, M-14; AC-04, AC-14]
- [ ] Run schema/metadata/federation/security gates, self-review and the full
  repository harness; record paired evidence. [M-18, M-19; AC-16]

## Phase 8 — CLI, MCP and scheduled operation

### 8.1 Operational contracts first

- [ ] Add CLI/MCP/scheduler tests for inspect, capture, normalize, reconcile,
  analyze, rebuild, candidate-build and status commands, including JSON output,
  dry-run, idempotency, cancellation, partial state, retry/resume, missing
  credentials and redaction. [M-15, M-18; AC-13, AC-16]
- [ ] Add scheduled-source heartbeat and drift tests that do not equate a
  successful workflow with capture, validation or publication. [M-04, M-15,
  M-19, S-04; AC-04, AC-09, AC-13]

### 8.2 Implement bounded operations

- [ ] Expose typed non-interactive CLI commands and read-only MCP resources
  over stable manifests/queries; return structured state and provenance.
  [M-15; AC-13]
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

- [ ] Add a failing recovery contract for empty derivative state, then rebuild
  Silver, Gold, SQLite, all plots/reports and Platinum metadata from Bronze,
  locked code and parameters. [M-10, M-16, M-18; AC-08, AC-12, AC-16]
- [ ] Compare output manifests/digests and explain permitted rendering-only
  variation; prove original objects were not mutated. [M-03, M-16; AC-02,
  AC-12]

### 9.2 Build a rights-filtered Hugging Face candidate locally

- [ ] Add release-readiness negative tests for missing rights, incomplete
  source disposition, failed parity/recovery, stale evidence, non-pinned
  revisions, restricted content and candidate-manifest mismatch. [M-14, M-17,
  M-18; AC-14, AC-15, AC-16]
- [ ] Build a local candidate for `edithatogo/nz-health-appropriations` with
  rights-eligible originals/derivatives only, schemas, manifests, cards,
  limitations and checksums. Metadata-only/tombstone representations must
  remain explicit. [M-14, M-17; AC-14, AC-15]
- [ ] Record exact candidate manifest hash, byte/file counts, intended splits,
  viewer expectations, collection target and rollback/reconciliation plan.
  [M-17, M-19; AC-15]

### 9.3 Final local assurance and review

- [x] Run focused, property, mutation, recovery, schema, format, lint, strict
  typing, security, vulnerability, licence, SBOM and full repository gates at
  the exact candidate code/tree. [M-18; AC-16]
- [ ] Run automatic Conductor self-review across requirements, design, plan,
  evidence, source coverage, rights, reconstruction and publication claims;
  append and resolve every actionable finding. [M-19; AC-14, AC-16]
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

- [x] Remove scheduler-dependent Hypothesis deadline flakiness from the batch
  eligibility invariant without weakening generated cases or assertions.
  [M-18; AC-16] (`b2bf7b7`)

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
