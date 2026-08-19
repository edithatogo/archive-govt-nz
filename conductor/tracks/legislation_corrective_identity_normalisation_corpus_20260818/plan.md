# Plan: Identity, Normalisation, and Corpus Application Service

1. **Phase 1: v2 FRBR Model Implementation**
   - Define `WorkRecord`, `ExpressionRecord`, `ManifestationRecord`.
   - Implement v1 and v2 serialization on `LegislationRecord`.
2. **Phase 2: Normalisation Enhancement**
   - Safe XML ElementTree and HTML parsing.
   - Dual-hash binding and structural extraction of sections/schedules.
3. **Phase 3: LegislationArchiveService Integration**
   - Single application service coordinating adapter, client, CAS, manifest, export, and coverage.
4. **Phase 4: Test & Quality Gate Verification**
   - Unit and lifecycle tests under `tests/domains/test_legislation_corpus_service.py`.
   - Quality check suite pass under `tools/check.py`.
