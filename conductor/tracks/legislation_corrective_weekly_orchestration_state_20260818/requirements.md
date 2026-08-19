# Requirements: Weekly Legislation Orchestration and State Management

Track: `legislation_corrective_weekly_orchestration_state_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issue: [#137](https://github.com/edithatogo/archive-govt-nz/issues/137)

## MoSCoW Requirements

### Must
1. **Source-Set Configuration & Workflow Safety**:
   - Dedicated configuration file `config/source-sets/legislation.yml`.
   - Workflow `.github/workflows/scheduled-legislation-harvest.yml` pinned with immutable action commit SHAs.
2. **Deterministic Harvest Orchestrator**:
   - Implement `tools/run_legislation_harvest.py` executing incremental legislation sync via CLI/service.
   - Support credential check, checkpoint restore/promote, validation, and structured outcome classification (`changed`, `no_change`, `partial_retryable`, `failed`).
3. **Monthly Reconciliation & Quarterly Recovery Workflows**:
   - `.github/workflows/monthly-legislation-reconciliation.yml` for inventory and manifest reconciliation.
   - `.github/workflows/quarterly-legislation-recovery.yml` for clean restoration and disaster recovery drill.
4. **Zero Silent Failures**:
   - All workflow failures propagated explicitly to exit codes and JSON receipts.
