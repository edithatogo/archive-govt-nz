# Implementation Plan: Conductor Claim Drift Detection

### Phase 1: Claim inventory [COMPLETED]
- [x] Task: Enumerate machine-checkable claims in conductor records and receipts (repo archival flags, workflow activity, issue counts); define the claim schema.

### Phase 2: Checker [COMPLETED]
- [x] Task: Implement tools/check_claim_drift.py with fail-closed exit codes and a JSON receipt under build/.
- [x] Task: Add focused tests including a synthetic divergence fixture.

### Phase 3: Scheduling and wire-in [COMPLETED]
- [x] Task: Add a weekly scheduled lane and register the stage in the assurance harness behind its own gate.
- [x] Task: Conductor review and phase gate verification.

