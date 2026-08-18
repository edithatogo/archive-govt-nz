# Architecture Reuse Decisions: Legislation Consolidation

## 1. Zero Duplicate Adapters
- `NZLegislationAdapter` in `src/archive_govt_nz/adapters/nz_legislation.py` is upgraded in place.
- No `NZLegislationAdapterV2` or parallel adapter classes are created.

## 2. Donor Client Porting
- Pacing algorithms and HTTP error handling from `NZLegislationClient` are integrated into domain services and shared HTTP client abstractions.

## 3. Standalone Product Boundary
- `edithatogo/legislation` is strictly retained external without merging or deprecating.
