# Plan - Mirror Account Follow Sync

## Phase 1: Relationship Mapping & Read Probes
- [x] Task: Write tests in `tests/test_follow_matrix.py` to verify follow matrix generation and loop prevention.
- [x] Task: Implement read-only follow-checking probes in `scripts/check_follow_status.py` for platforms with supported public/API visibility.
- [x] Task: Mark unsupported or auth-restricted follow checks as manual review items rather than browser automation tasks.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Relationship Mapping & Read Probes' (Protocol in workflow.md)

## Phase 2: Archiving & Follow State Cache
- [x] Task: Define the schema and initialize `conductor/follow_sync_state.json`.
- [x] Task: Persist only non-secret follow status evidence, timestamps, platform identifiers, and manual-review notes.
- [x] Task: Add test suite coverage for follow state updates and caching logic.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Archiving & Follow State Cache' (Protocol in workflow.md)

## Phase 3: Core Group Follow Sync Execution
- [x] Task: Implement write-follow operations only for platforms with supported official APIs and explicit repository secrets.
- [x] Task: Keep Threads, Instagram, Facebook, and any other unsupported follow paths as manual checklists unless an official API route is confirmed.
- [x] Task: Add an opt-in manual workflow for dry-run reporting before any live follow execution.
- [x] Task: Perform a dry-run and controlled live execution test for the supported API path.
  - [x] Dry-run verified for `mirnzcourts.bsky.social` with resolved target DIDs.
  - [x] Controlled live execution completed in GitHub Actions run `27499153549`.
  - [x] Post-execution verification completed in GitHub Actions run `27499492262`; dry-run reported no missing follows.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Core Group Follow Sync Execution' (Protocol in workflow.md)
