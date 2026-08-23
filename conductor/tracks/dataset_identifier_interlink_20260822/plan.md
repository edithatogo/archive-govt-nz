# Plan: Dataset Identifier Interlinking

## Phases

### Phase 1: Source Audit
- [x] Audit available identifier sources (legislation checkpoint, health
      snapshot, publication readback receipt).

### Phase 2: Interlink Engine (TDD)
- [x] Implement `tools/build_identifier_interlink.py` with per-domain shape
      validation, collision detection, and v1 receipt.
- [x] Test suite (14 tests) covering loaders, validation, collisions, assembly.

### Phase 3: Baseline Manifest
- [x] Generate baseline interlink manifest from committed evidence.

### Phase 4: Assurance Gate
- [x] Run full `tools/check.py`; record result.

> **Status: COMPLETED** — All phases verified. Reviewed and closed 2026-08-22.
> Gazette IDs join the manifest automatically once the first gazette harvest
> produces its checkpoint/manifest artefacts.