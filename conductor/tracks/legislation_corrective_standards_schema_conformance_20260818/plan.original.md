# Plan: Standards and Schema Conformance

1. **Phase 1: Contract Validation and Schema Specification (Commit A)**
   - Update track requirements, plan, and validate YAML contracts.

2. **Phase 2: Schema Definition and Migration Fixtures (Commit B)**
   - Maintain JSON Schema Draft 2020-12 schemas for v1 and v2 legislation records.
   - Provide representative sample fixture documents.

3. **Phase 3: Schema Test Suite & Verification (Commit B)**
   - Verify schema validity using `tools/validate_schemas.py`.
   - Verify zero schema drift with `tools/check.py`.
