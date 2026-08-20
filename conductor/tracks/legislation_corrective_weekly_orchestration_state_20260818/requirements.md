# Requirements: Weekly Orchestration, Resumable Archival Service, and State Management

Track: `legislation_corrective_weekly_orchestration_state_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#137](https://github.com/edithatogo/archive-govt-nz/issues/137), [#138](https://github.com/edithatogo/archive-govt-nz/issues/138)

## MoSCoW Requirements

### Must
1. **Real, Bounded, Resumable Legislation Archival Service**:
   - Single canonical orchestration service in `LegislationArchiveService` (no parallel services or V2 classes).
   - Strict 10-step synchronization pipeline:
     `discovery` → `work/version traversal` → `conditional source acquisition` → `exact source-byte preservation in CAS` → `v2 normalisation` → `validation` → `manifest generation` → `coverage calculation` → `staged checkpoint` → `atomic checkpoint promotion`.
2. **Resilience & State Management**:
   - First sync cold start.
   - Repeated no-change sync (idempotency, conditional ETag/304 caching).
   - New and modified expression detection and preservation.
   - Resumable sync across interruptions using persisted checkpoint state.
   - Strict fail-closed validation on corrupt or invalid payloads.
   - Staged checkpoint creation with atomic rename promotion on success only.
   - Failures must prevent checkpoint promotion.
   - Zero fabricated default timestamps.
3. **Weekly Harvest & Recovery Automation**:
   - Scheduled Monday harvest workflow (`.github/workflows/scheduled-legislation-harvest.yml`) running at `23 18 * * 0`.
   - Monthly reconciliation and quarterly recovery drills.
4. **End-to-End Multi-Expression Fixture**:
   - End-to-end verification of one work with two distinct expressions and XML/HTML manifestations through full CAS, normalisation, manifest, and checkpoint promotion, followed by an idempotent no-change rerun.
