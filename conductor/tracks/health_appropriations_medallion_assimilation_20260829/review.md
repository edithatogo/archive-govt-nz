# Self-Review

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
