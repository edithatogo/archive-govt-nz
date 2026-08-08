# Implementation plan

- [x] Phase 1: Freeze candidate, rights, sensitivity, and safety contracts.
  - [x] Write failing tests for eligibility and fail-closed states.
  - [x] Define manifest and tombstone schemas.
  - [x] Record 158 decision-required resource classifications.
  - [x] Phase verification checkpoint.
- [ ] Phase 2: Implement bounded retrieval and quarantine.
  - [ ] Add resumable streaming with byte/time/redirect limits.
  - [ ] Add independent type and archive-expansion checks.
  - [ ] Phase verification checkpoint.
- [ ] Phase 3: Preserve and transform.
  - [ ] Write immutable originals and checksum receipts.
  - [ ] Add provenance, WARC, Parquet, and JSONL handling where applicable.
  - [ ] Phase verification checkpoint.
- [ ] Phase 4: Validate and hand off.
  - [ ] Add property, contract, metamorphic, deterministic-simulation, and mutation tests.
  - [ ] Run clean-environment and security validation.
  - [ ] Prepare a publication handoff without publishing.
  - [ ] Phase verification checkpoint.
