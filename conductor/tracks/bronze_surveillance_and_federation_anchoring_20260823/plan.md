# Implementation Plan: Surveillance Heartbeat Ledger & Cross-Repository Federation Protocol

### Phase 1: Compact Surveillance Heartbeat Ledger (Strata B0)
- [ ] Task: Implement `src/archive_govt_nz/bronze/heartbeat.py` managing append-only surveillance logs.
- [ ] Task: Integrate HTTP 304 / ETag conditional checking in domain adapters.
- [ ] Task: Add test cases verifying surveillance continuity without CAS write amplification.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Canonical URN Protocol & Federation Encoders
- [ ] Task: Implement `src/archive_govt_nz/core/urn.py` for canonical URN parsing, formatting, and validation.
- [ ] Task: Inject canonical URNs into Silver and Gold Arrow/Parquet record schemas.
- [ ] Task: Add tests for URN bidirectionality and formatting invariants.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Zero-Copy Cross-Repository Federated SQL Views
- [ ] Task: Extend `GoldAnalyticsEngine` with pre-defined zero-copy views joining GMA and FYI datasets.
- [ ] Task: Add integration tests verifying cross-repository query resolution.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 4: Asynchronous OpenTimestamps Proof-of-Existence Batcher
- [ ] Task: Implement `tools/ots_batch_anchoring.py` computing Merkle trees over B1 manifests and submitting to OTS calendars out-of-band.
- [ ] Task: Store verified `.ots` proof blocks alongside publication receipts.
- [ ] Task: Add offline OTS verification tests.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 5: Quality Gates & Final Federation Certification
- [ ] Task: Add federation mutation testing gates.
- [ ] Task: Validate full 20-stage gate harness.
- [ ] Task: Conductor Track Review & Final Certification.
