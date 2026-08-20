# Plan: Operational Continuity Cycles and Clean Workspace Recovery Drill

1. **Phase 1: Pipeline Cycle Continuity Recorder**
   - Record genuine scheduled weekly harvest cycles and monthly reconciliation runs with checkpoint progression, manifest hashes, and artefact IDs.
2. **Phase 2: Clean Workspace Recovery Engine**
   - Implement `tools/verify_operational_continuity_and_recovery.py` to restore checkpoints, reconstruct bounded corpus, regenerate derivatives, verify bit-level hash parity, and measure recovery timing.
3. **Phase 3: Negative Controls & Assurance Gate**
   - Implement unit and negative-control test suite in `tests/canary/test_operational_continuity_and_recovery.py`.
   - Execute tool, write receipt to `evidence/migrations/corpus-legislation-nz/operational-continuity-recovery-receipt.json`, and pass full 19-stage assurance gate (`tools/check.py`).
