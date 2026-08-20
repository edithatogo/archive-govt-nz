# Requirements: Operational Continuity Cycles and Clean Workspace Recovery Drill

Track: `legislation_corrective_shadow_operation_cutover_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#139](https://github.com/edithatogo/archive-govt-nz/issues/139), [#140](https://github.com/edithatogo/archive-govt-nz/issues/140)

## MoSCoW Requirements

### Must
1. **Target Operational Cycles Verification**:
   - Record at least two genuine target cycles using the real pipeline, including at least one scheduled weekly run (`scheduled-legislation-harvest`) and one reconciliation cycle.
   - For each cycle record:
     - Workflow run ID;
     - Target commit;
     - Input and output checkpoints;
     - Changed/no-change status;
     - Works, expressions, and manifestations counts;
     - Failures list;
     - Manifest SHA-256 hash;
     - Retained artefact IDs;
     - Publication state (`prepared_locally_not_published`).
2. **Clean Workspace Recovery Drill**:
   - In an isolated clean workspace:
     - Restore verified checkpoint and manifest;
     - Reconstruct bounded corpus;
     - Verify raw CAS hashes;
     - Regenerate derivatives (Parquet, JSONL);
     - Compare manifest root hashes;
     - Measure exact recovery duration in milliseconds;
     - List mismatches (must be 0);
     - Prohibit remote publication.
3. **Receipt and Anti-Simulation**:
   - Save execution receipt to `evidence/migrations/corpus-legislation-nz/operational-continuity-recovery-receipt.json`.
   - If cycles or inputs are missing, return `BLOCKED_OBSERVATION` with non-zero exit code.
