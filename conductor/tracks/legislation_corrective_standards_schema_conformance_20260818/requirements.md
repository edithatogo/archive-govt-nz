# Requirements: Standards and Schema Conformance

Track: `legislation_corrective_standards_schema_conformance_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`

## MoSCoW Requirements

### Must
1. **Strict JSON Schema Draft 2020-12 Conformance**:
   - Maintain strict conformance for `schemas/legislation/v1/legislation-record.schema.json` and `schemas/legislation/v2/legislation-record.schema.json`.
   - Invalidate any document missing mandatory properties or containing invalid format/types.
2. **Backwards Compatibility**:
   - Preserve v1 schema compatibility without breaking existing consumers.
   - Allow v2 documents to represent richer metadata (manifestations, relationships, uncertainty, rights, provenance).
3. **Automated Schema Validation**:
   - Enforce schema validation on all representative fixture files and serialized models.
