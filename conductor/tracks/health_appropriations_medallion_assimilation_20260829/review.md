# Self-Review

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
