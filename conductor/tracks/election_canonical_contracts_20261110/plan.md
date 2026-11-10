# Implementation Plan: Election Canonical Contracts

- [x] Create `schemas/election/election-results-raw-v1.schema.json` and validate against sample 2017–2023 CSV captures.
- [x] Create `schemas/election/sainte-lague-allocation-v1.schema.json` and `overhang-analysis-v1.schema.json`.
- [x] Create `schemas/election/special-votes-sensitivity-v1.schema.json`.
- [x] Implement Pydantic / dataclass serializers in `src/archive_govt_nz/domains/elections/contracts.py`.
- [x] Add pytest validation suite verifying existing CAS evidence JSON files against schemas (`tests/test_elections_contracts.py`).
