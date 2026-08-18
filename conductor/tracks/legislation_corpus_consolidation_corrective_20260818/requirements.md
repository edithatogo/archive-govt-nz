# Requirements: Corrective Legislation Corpus Consolidation

## 1. Operating Mode & Non-Negotiable Contract
- **Contract-First & Evidence-First**: No claim of completion, capability, or parity may be made without executable contracts and cryptographic evidence ledgers.
- **Reuse-Before-Create**: Upgrade `NZLegislationAdapter` and `NZLegislationApiClient` in place. Do not create `NZLegislationAdapterV2` or parallel adapter classes.
- **Standalone Product Boundary**: `edithatogo/legislation` is a distinct outward-facing tool (`nz-legislation-tool`, `nzlegislation` CLI/MCP) and must not be merged, renamed, replaced, or archived.

---

## 2. MoSCoW Requirements

### Must Have
1. **Invalidation of Unsupported PR #124 Claims**:
   - Explicitly invalidate PR #124's closeout receipts that claimed completion without live evidence.
   - Retain prior receipts in historical audit state with `status: "invalidated"` and required metadata (`invalidated_reason`, `superseded_by`, `invalidated_at`, `audited_target_commit`, `audited_donor_commit`).
   - Chronology integrity: no evidence timestamp may be in the future.

2. **Donor Live Inventory & Pre-Acquisition Audit**:
   - Produce a programmatically derived live component inventory of `edithatogo/corpus-legislation-nz` at baseline commit `749918c251da59dc890c19dfda2ab9a021fd8ca6`.
   - Inventory all 33,693 candidate seeds, 68 historical batches, workflow route tables, donor issues, and publication targets.

3. **Donor Conductor Lineage Preservation**:
   - Ingest donor Conductor tracks immutably under `conductor/archive/imported/corpus-legislation-nz/`.
   - Preserve original donor track IDs, runlogs, decisions, and evidence references.

4. **Real Donor Capability Assimilation**:
   - Upgrade existing `NZLegislationAdapter` in place in `src/archive_govt_nz/adapters/nz_legislation.py`.
   - Wire adapter to use `NZLegislationApiClient` for all transport (rate limiting, pacing, `Retry-After`, 429 backoff, 403 burst handling, conditional ETag requests).

5. **Legal Identity, FRBR Normalisation & Schema Conformance**:
   - Model Work, Expression, and Manifestation distinctly.
   - Preserve `schemas/legislation/v1/legislation-record.schema.json` compatibility while establishing `schemas/legislation/v2/legislation-record.schema.json` as canonical target schema.
   - Safe parsing: use structured ElementTree XML parsing and HTML parsers (no regex stripping).

6. **Real CLI and MCP Runtime Operation**:
   - CLI commands (`archive-govt-nz legislation`) must execute real domain service logic with documented 0–5 exit codes.
   - MCP tools must integrate with an operational Model Context Protocol runtime and return structured domain entity references.
   - Compatibility entrypoint `nzlc` must route to the canonical application service.

7. **Real Source-Set Weekly Orchestration**:
   - Legislation source-set schedule must be once-weekly (`23 18 * * 0` - Monday 06:23 NZST).
   - Dedicated weekly harvest workflow `.github/workflows/scheduled-legislation-harvest.yml`.
   - Monthly reconciliation workflow `.github/workflows/monthly-legislation-reconciliation.yml`.
   - Quarterly recovery drill `.github/workflows/quarterly-legislation-recovery.yml`.
   - Remove legislation from the generic 6-hour harvesting matrix.

8. **Historical Reconciliation & Multi-Batch Ingestion**:
   - Reconcile 68 period-sharded batches from donor repository against target CAS and registry.
   - Distinctly track candidate works, attempted works, expressions, manifestations, and published rows without conflation.

9. **Differential Parity & Fixity Receipts**:
   - Real bitstream fixity checks comparing source payloads with donor CAS.
   - Normalised derivative semantic parity checks with explicit mismatch tracking.

10. **Donor Issue & PR Reconciliation**:
    - Programmatically audit all 65 donor issues (including 21 open issues and 9 open PRs = 30 open items on GitHub).
    - Track unresolved donor work honestly under target corrective issue #125.

11. **Rights, Redistribution & Licensing Classification**:
    - Classify statutory text (Crown Copyright / NZGOAL CC-BY 4.0) vs third-party incorporated material (omitted from public bundles, retained in internal CAS).

12. **Quality Gates & Supply Chain Assurance**:
    - 100% branch test coverage on domain integrity logic, 95% repo-wide.
    - 100% mutation testing kill rate across all mutation suites.
    - Zero security vulnerabilities, zero secrets, valid CycloneDX SBOM.

13. **Gazette Residual Separation**:
    - Official & DigitalNZ gazette sources assimilated into target; historical Victoria/LexisNexis remain separate under Track 12.

14. **Anti-Simulation & Honest Contract Execution**:
    - Rejection of fixed counts (33,693, 68, 100%, 350 entities, 19 checks).
    - Rejection of unconditional affirmative responses (`healthy`, `ready`, `synced`, `verified`).
    - Evaluator must exit non-zero reporting `INCOMPLETE` until all defects and open gates are resolved.

### Should Have
- Automated weekly Slack/webhook health reporting for legislation harvests.
- Parquet derivative compaction for multi-version expression diffs.

### Could Have
- Semantic vector indexing for legislative provisions.

### Won't Have (This Programme)
- Remote production credential injection during offline testing.
- Archiving donor repository before target cutover is proven in live weekly observation.
