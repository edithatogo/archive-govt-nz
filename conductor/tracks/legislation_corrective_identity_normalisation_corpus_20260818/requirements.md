# Requirements: Identity, Normalisation, and Canonical v2 FRBR Model

Track: `legislation_corrective_identity_normalisation_corpus_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#132](https://github.com/edithatogo/archive-govt-nz/issues/132), [#133](https://github.com/edithatogo/archive-govt-nz/issues/133), [#134](https://github.com/edithatogo/archive-govt-nz/issues/134)

## MoSCoW Requirements

### Must
1. **Canonical v2 FRBR Runtime Model**:
   - Represent FRBR Work (`WorkRecord`, `LegislationWork`), Expression (`ExpressionRecord`, `LegislationExpression`), and Manifestation (`ManifestationRecord`, `LegislationManifestation`) as explicit runtime dataclasses in `src/archive_govt_nz/domains/legislation/models.py` and `src/archive_govt_nz/domains/legislation/identity.py`.
   - Remove all default fixed timestamps from runtime model definitions.
   - Represent work identity, expression/version identity, manifestation identity, source and canonical URIs, source media type, raw object hashes (`sha256`, `blake3`), byte size, caller-supplied retrieval timestamp, source modification timestamp, type and status with uncertainty, amendment/repeal/replacement relationships, commencement/assent dates, sections/schedules, provenance references, and rights/redistribution classifications.
2. **Dual Schema Serialization & Validation**:
   - Support both `to_dict("v1")` and `to_dict("v2")` serialization on `LegislationRecord` with zero schema drift.
   - Provide explicit schema validation against Draft 2020-12 schemas.
3. **Deterministic Identity Generation**:
   - Implement deterministic generators for `work_id`, `expression_id`, and `manifestation_id` without ID fabrication.
4. **Bidirectional Conversion & Lossy Reporting**:
   - Implement lossless `convert_v1_to_v2` conversion.
   - Implement `convert_v2_to_v1` conversion with explicit reporting of dropped/lossy fields.
