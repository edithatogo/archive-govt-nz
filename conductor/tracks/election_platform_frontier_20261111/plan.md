# Execution plan / ordered acceptance

1. [ ] Unblock #861: reconcile synthetic vote-denominator call sites, fix 120-seat test fixture, pin actions SHAs, use exact-head CI evidence. Pass full repository harness; run browser smoke; merge and verify HF revision.
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
As of 11 November 2026 PR #861 exact head earlier failed with 5 election tests and workflow policy lint; CodeQL passed. The old Space is still published. The source corrections are being reconciled in that same PR.
