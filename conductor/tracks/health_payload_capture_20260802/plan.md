# Implementation plan

- [x] Phase 1: Freeze candidate, rights, sensitivity, and safety contracts.
  - [x] Write failing tests for eligibility and fail-closed states.
  - [x] Define manifest and tombstone schemas.
  - [x] Record 158 decision-required resource classifications.
  - [x] Phase verification checkpoint.
- [x] Phase 2: Implement bounded retrieval and quarantine.
  - [x] Add resumable streaming with byte/time/redirect limits.
  - [x] Add independent type and archive-expansion checks.
  - [x] Phase verification checkpoint: 158 resource decisions evaluated; zero
    resources admitted because resource-level rights remain unknown.
- [x] Phase 3: Preserve and transform.
  - [x] Write immutable originals and checksum receipts where eligible; no
    original payload exists because the eligible set is empty.
  - [x] Add provenance, WARC, Parquet, and JSONL handling where applicable;
    WARC is not material when no HTTP payload transaction occurs.
  - [x] Phase verification checkpoint: source metadata preserved unchanged;
    JSONL, Parquet, tombstones, capture plan, and SHA-256/BLAKE3 receipts prepared.
- [x] Phase 4: Validate and hand off.
  - [x] Add property, contract, metamorphic, deterministic-simulation, and mutation tests.
  - [x] Run clean-environment and security validation.
  - [x] Prepare a publication handoff without publishing.
  - [x] Phase verification checkpoint: package state is
    `prepared-not-published`, with publication authorization false.

GitHub hierarchy: #76 with nested subissues #77, #78, #79, and #80.
