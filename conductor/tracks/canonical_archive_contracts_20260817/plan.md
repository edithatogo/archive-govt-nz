# Track 4 Plan: Canonical Archive Contracts

## Phases

### Phase 1: Universal Identifier & Schema Architecture
- [ ] Specify universal identifier grammar and regex validators.
- [ ] Draft JSON Schema definitions for manifests, capture events, and publication receipts.

### Phase 2: Python Data Model & Serialization Engine
- [ ] Implement frozen dataclasses with slots in `src/archive_govt_nz/core/identity.py` and `manifests.py`.
- [ ] Implement deterministic JSON-LD canonical serialization.

### Phase 3: Contract Verification & Schema Suite Integration
- [ ] Add representative fixtures and validate against schemas in `tools/validate_schemas.py`.
- [ ] Run full 18-stage assurance check.
