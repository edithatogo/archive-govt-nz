# Run Log: Operational Continuity Cycles and Recovery Drill

- Verified target operational cycles:
  - Cycle 1: `sched-weekly-harvest-20260818-001` (Scheduled Legislation Harvest weekly cron `23 18 * * 0`, 500 works, changed status, valid manifest).
  - Cycle 2: `monthly-recon-20260819-001` (Monthly Legislation Reconciliation cron `17 3 1 * *`, 500 works, no_change status).
- Executed clean workspace recovery drill in `tools/verify_operational_continuity_and_recovery.py`:
  - Restored verified checkpoint and manifest.
  - Reconstructed bounded corpus and verified raw CAS hashes (SHA-256 and BLAKE3).
  - Regenerated Parquet and JSONL derivatives.
  - Compared manifest root hashes (`manifest_root_match: true`).
  - Measured recovery drill duration.
  - Recorded 0 mismatches.
- Emitted machine-readable receipt in `evidence/migrations/corpus-legislation-nz/operational-continuity-recovery-receipt.json`.
- **2026-08-22**: Gated blocker resolved. `HF_TOKEN` and `ZENODO_TOKEN` deployed as GitHub Actions secrets via user action. Wired into all three legislation workflows.
