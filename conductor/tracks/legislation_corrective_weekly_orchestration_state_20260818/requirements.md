# Requirements: Weekly Orchestration, Monthly Reconciliation, and Recovery Drills

Track: `legislation_corrective_weekly_orchestration_state_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#137](https://github.com/edithatogo/archive-govt-nz/issues/137), [#138](https://github.com/edithatogo/archive-govt-nz/issues/138)

## MoSCoW Requirements

### Must
1. **Weekly Harvest Automation**:
   - Scheduled Monday harvest workflow (`.github/workflows/scheduled-legislation-harvest.yml`) running at `23 18 * * 0` (Monday 06:18 NZST).
   - Enforce 45-minute runtime ceiling, dual-hash verification, and checkpoint state management.
2. **Monthly Full Reconciliation**:
   - Workflow (`.github/workflows/monthly-legislation-reconciliation.yml`) verifying all historical batches and donor inventory integrity.
3. **Quarterly Disaster Recovery Drills**:
   - Workflow (`.github/workflows/quarterly-legislation-recovery.yml`) executing zero-network cold recovery drills from external backups.
