# Plan: Weekly Orchestration, Resumable Archival Service, and State Management

1. **Phase 1: Checkpoint Manager & Atomic State Promotion**
   - Enhance `LegislationCheckpointManager` to support staged checkpoints, atomic promotion, corruption detection, and eliminate fabricated default timestamps.
2. **Phase 2: Canonical Bounded & Resumable Archival Service**
   - Enhance `LegislationArchiveService` in `src/archive_govt_nz/domains/legislation/corpus.py` to execute the full 10-step flow:
     discovery → work/version traversal → conditional acquisition (ETag/CAS) → exact source-byte CAS storage → v2 normalisation → validation → manifest generation → coverage calculation → staged checkpoint → atomic promotion.
   - Implement retry handling, interruption resume, fail-closed validation, and atomic promotion guards.
3. **Phase 3: Comprehensive Unit & End-to-End Fixture Testing**
   - Implement comprehensive tests for first sync, no-change rerun, changed expressions, interruption resume, corrupt checkpoint, failed sync abort without promotion, and multi-expression XML/HTML fixture.
4. **Phase 4: Verification & Conformance Gate**
   - Verify with `uv run python tools/check.py`, patch coverage >= 95%, and clean assurance checks.
