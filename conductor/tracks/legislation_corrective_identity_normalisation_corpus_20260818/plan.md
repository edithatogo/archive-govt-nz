# Plan: Canonical v2 FRBR Runtime Model and Compatibility

1. **Phase 1: Contract and Track Specifications (Commit A)**
   - Update MoSCoW requirements and execution plan.
   - Validate YAML contracts using `tools/validate_contracts.py`.

2. **Phase 2: Canonical v2 Model Implementation (Commit B)**
   - Implement `LegislationWork`, `LegislationExpression`, `LegislationManifestation` and deterministic ID generators in `src/archive_govt_nz/domains/legislation/identity.py`.
   - Implement `WorkRecord`, `ExpressionRecord`, `ManifestationRecord`, `RelationshipRecord`, `ProvenanceReference`, and `LegislationRecord` with no default fixed timestamps in `src/archive_govt_nz/domains/legislation/models.py`.
   - Update `schemas/legislation/v2/legislation-record.schema.json` to include v2 fields.
   - Implement `convert_v1_to_v2`, `convert_v2_to_v1`, and `validate_legislation_record` crosswalk and validation helpers.

3. **Phase 3: Verification & 100% Patch Coverage (Commit B)**
   - Write comprehensive unit tests for v2 models, deterministic identity generation, serialization, schema validation, and lossy conversion reporting.
   - Verify with `tools/check.py`.
