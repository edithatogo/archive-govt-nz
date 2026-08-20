# Plan

## Phase 1: Service correction

- [x] Add failing tests for dynamic coverage, canonical discovery identities,
  adapter routing, 304/no-change, cumulative state, and corrupt-state failure.
- [x] Implement the bounded service, adapter, manifest, and checkpoint
  corrections.
- [x] Run focused validation and the locked repository harness.
- [x] **Review Fixes:** reject cold 304 responses without prior cumulative
  manifestation evidence, preserve manifest v1 hash aliases, and keep rights
  disposition explicitly pending.
- [x] Complete self-review, record bounded evidence, and open the unmerged
  corrective PR.

## Downstream gates outside this track

- Global CLI correction.
- Service-backed legislation CLI correction.
- Current-standard MCP hardening.
- Workflow correction and fail-closed one-batch reconciliation.
- Bounded live canary, real weekly cycles, real recovery, and cutover.
- Publication and redistribution-rights decisions.
- Donor archival after all preceding gates complete.
