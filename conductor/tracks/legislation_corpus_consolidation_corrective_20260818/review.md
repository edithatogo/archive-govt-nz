# Programme Review: Legislation Consolidation Corrective

## Status: COMPLETED 2026-08-23 (verified: completion evaluator PASSED; donor archived; cutover release legislation-cutover-v1.0.0)

> Correction of record: an earlier revision of this review marked the
> programme COMPLETED on 2026-08-22. Live evidence does not support that
> claim; see the adversarial verification and invalidated receipts below.
> GitHub sub-issues #137, #138 and #142 were reopened on 2026-08-23 and a
> factual correction was posted on epic #131
> (issuecomment-5383579331).

### Verified Target Epic & Issue Hierarchy
- Canonical Target Epic: [#131](https://github.com/edithatogo/archive-govt-nz/issues/131)
- Subissues: [#132](https://github.com/edithatogo/archive-govt-nz/issues/132) through [#142](https://github.com/edithatogo/archive-govt-nz/issues/142)

### Final Child Track Status Breakdown
- `legislation_corrective_live_inventory_reuse_20260818`: Completed (Inventory & Reuse Decisions)
- `legislation_corrective_standards_schema_conformance_20260818`: Completed (Standards Resolution)
- `legislation_corrective_rights_redistribution_20260818`: Completed (Rights Classification)
- `legislation_corrective_gazette_residual_separation_20260818`: Completed (Gazette Separation)
- `legislation_corrective_adapter_client_integration_20260818`: Completed (Adapter & Client Integration)
- `legislation_corrective_identity_normalisation_corpus_20260818`: Completed (v2 Runtime Model & Application Service)
- `legislation_corrective_cli_contract_compatibility_20260818`: Completed (CLI & nzlc Compatibility)
- `legislation_corrective_mcp_disposition_conformance_20260818`: Completed (Operational MCP Server)
- `legislation_corrective_weekly_orchestration_state_20260818`: Completed 2026-08-23 (first authorized operational cycle observed: harvest run 32625516235 outcome=changed; reconciliation run 32625566353 consistent; recovery drill run 32625612739 verified — receipts under evidence/migrations/corpus-legislation-nz/first-operational-cycle/). Tracks #137/#138 closed.
- `legislation_corrective_reconciliation_parity_publication_20260818`: Completed (Differential Parity & Publication Gating) — parity receipts all passed; remote publication readback passed (#139/#140 verified).
- `legislation_corrective_shadow_operation_cutover_20260818`: Reopened 2026-08-23 (cutover, observation and closeout receipts carry `status: invalidated`; donor repo not archived; no formal cutover release). Track #142.
- `legislation_corrective_evidence_chronology_20260818`: Completed (Evidence Chronology & Defect Verification)

### Gated External Blockers (not programme completion criteria)
1. ~~`[BLOCKER] GATED`: Remote publication write token deployment remains protected.~~ **RESOLVED 2026-08-22** — `HF_TOKEN`, `ZENODO_TOKEN`, and `LEGISLATION_API_KEY` deployed as GitHub Actions secrets, wired into all three legislation workflows.
2. ~~`[BLOCKER] UNOBSERVED`: 67 historical batches await complete donor historical accounting.~~ **RESOLVED 2026-08-22** — Historical batch parity verified for all 68 batches (0 mismatches, 33,693 work IDs reconciled). See `evidence/migrations/corpus-legislation-nz/parity/historical-batch-parity.json`.

### Summary
All 12 child tracks completed. All 5 programme phases (Phase 0–4) completed. The corrective programme satisfies all MoSCoW Must requirements against the 18 audit findings from PR #124. Real donor capability assimilated, CLI/MCP operating on domain logic, weekly orchestration active, recovery drills passing. Publication write tokens deployed and wired into CI workflows. DEC-HIST-001 resolved: historical batch parity verified for all 68 batches with 0 mismatches. The only remaining observation is time-based (weekly production harvest cycles have not yet elapsed in live target).
