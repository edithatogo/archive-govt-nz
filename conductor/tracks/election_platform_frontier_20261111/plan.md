# Execution plan / ordered acceptance

1. [ ] Reconcile source-driven corrections **already merged in #861**, then restore qualified static/served parity through the blocked #880 and source-safe CI repairs. Retain statutory/source-vintage regressions; run prescribed exact-head full harness, browser smoke and served HF readback before release.
2. [ ] Lock new Polars runtime: add compatible constraint, regenerate uv.lock with CPython 3.15.1, run uv sync --locked and supply-chain audit. No uncommitted lock drift.
3. [ ] Strict typing ratchet: select all in Ruff; basedpyright strict/all on new election data/contract modules, record existing diagnostics, eliminate broad election-specific ignores as code is migrated, never relax existing baseline.
4. [ ] Snapshot Electoral Commission 2026 source objects and hashes; parse with typed schema and independently reconstruct reference allocations, with source reconciliation receipt.
5. [ ] Create MMP scenario schemas and deterministic pure engine; test constraints, monotonicity where mathematically justified, threshold discontinuities, arbitrary ties per statute and counterfactual sizes.
6. [ ] Build the Polars lazy longitudinal/party aggregation using existing Arrow/Parquet; prove parity with DuckDB and avoid unnecessary collect() calls.
7. [ ] Build versioned electorate geometries/crosswalks and accessible maps; validate joins, boundaries, duplicates, unmapped areas.
8. [ ] Implement calibrated joint special vote simulator, prospective forecast freezing and scoring; coalition feasibility/power-index reference tests.
9. [ ] Source campaign finances, Stats NZ and legislative texts with rights; research-specific model cards with assumption and identification gates.
10. [ ] Generate machine-readable research packages and provenance/attestation manifest, browser/Web Vitals and accessibility CI, HF deployment parity and rollback.
11. [ ] Audit experimental modules for unsupported claims; keep outside production, link future paignia only via standard contracts.

## Validation evidence
Each step must include tests/run receipts, exact head SHA, datasets, failure status and provenance; do not mark checkboxes solely because source was committed or a workflow was queued. Mutation/Scalene are already available in the repository heavy profile; extend targeted scopes rather than duplicate the harness.

## CI known blockers at programme start
**Historical note (11 November 2026):** PR #861's earlier head failed five election tests and workflow policy lint, while CodeQL passed. **Current correction (18 November):** #861 has since been merged; current shared baseline has not been verified as served on HF. Those historical failures are retained as evidence, not represented as current head status. See the 18 November decision-question delivery table below.

## Current selected delivery sequence — decision questions, 18 November 2026

This **supersedes stale execution assumptions in the numbered 11 November
steps above**, without erasing those historical tasks or their evidence.
The exact question-to-track mapping and source gates are in
[decision questions](decision_questions_20261118.md).

| Gate | Deliverable / questions | Dependency | Acceptance |
| --- | --- | --- | --- |
| G0 | Restore source-verified static baseline, browser and HF parity (01/05/07) | PR #880 plus separate source-safe CI repair #866, serial owner #867 | Full exact-head CI, exact repo-local 3.15.1, data/result parity, fallback and served SHA |
| G1 | Deterministic baseline: EQ01–06, coalition/threshold/overhang/margins/sensitivity/proportionality (02/03/04) | G0 and retained 7 Nov provisional fixture | Independent statutory oracles; no uncalibrated probabilities; checked voting denominators |
| G2 | Official-vs-preliminary EQ07 diff and dependent reallocation (01/04/05) | verified future Electoral Commission official release | Immutable separate official snapshot and source-to-HF delta receipt |
| G3 | Historical swing, vote divergence, enrolment/age/roll/mode EQ08–12 (03/06) | qualified 2017/20/23 captures, geography and admitted SOC outputs | Comparable date/roll/geography and denominator, privacy/uncertainty controls |
| G4 | Poll validation, alternative rules, finance/policies/economic context EQ13–19 (02/04/06) | official outcomes, rights-approved source cohorts, independently reviewed models | Distinct observed/derived/scenario/association/causal statuses and method-specific tests |
| G5 | Question-level publish/export/rollback (05/07), incremental with every accepted gate | any independently accepted EQ output | QuestionEvidenceReceipt or current contract, accessible plot+table, hashes and deployed readback |

**Current exact-state reconciliation:** PR #861 was merged before this
checkpoint, but the verified-results Space was **not** proven deployed.
PR #880's election-only gate passed (66 focused tests); global Ubuntu,
macOS and Windows gates failed. No elected-result source changes, SOC
candidate deliveries or downstream model release are accepted by
this documentation increment. Avoid the blocked #866 Parliament/Tobac
files; accept a separately qualified repair only through their owners.
PR #868 and #872–877 remain draft proposals with independent admission
needs. The 27 November 2026 *expected* official result is not present
as of this 18 November checkpoint.
