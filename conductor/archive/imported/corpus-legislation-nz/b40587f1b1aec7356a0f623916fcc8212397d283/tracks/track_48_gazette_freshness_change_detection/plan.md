# Plan - Gazette Freshness And Change Detection

## Phase 1 - Freshness Source Contract

- [ ] Task: Define freshness inputs.
    - [ ] Identify official Gazette issue/search/feed surfaces allowed by the
      source registry.
    - [ ] Identify DigitalNZ Gazette delta query support through `dnz` or the
      documented API.
- [ ] Task: Define freshness state.
    - [ ] Include item IDs, source URLs, first/last seen timestamps,
      ETag/Last-Modified where available, content hash where available, and
      enqueue decisions.
    - [ ] Include new, changed, unchanged, duplicate, withdrawn/deleted, and
      blocked states.
- [ ] Task: Conductor - User Manual Verification 'Freshness Source Contract' (Protocol in workflow.md)

## Phase 2 - Polling And Queue Generation

- [ ] Task: Add freshness detection tests.
    - [ ] Cover official and DigitalNZ item discovery.
    - [ ] Cover deterministic state updates and refresh-queue generation.
- [ ] Task: Implement bounded freshness polling.
    - [ ] Poll conservatively with source-specific pacing.
    - [ ] Store state and emit source refresh queues without broad re-harvests.
- [ ] Task: Conductor - User Manual Verification 'Polling And Queue Generation' (Protocol in workflow.md)

## Phase 3 - Workflow And Review Integration

- [ ] Task: Integrate freshness queues with archive workflows.
    - [ ] Feed targeted refreshes into Tracks 42, 43, 44, and 45 where the
      source is enabled.
    - [ ] Trigger Track 46 canonical rebuilds only for affected records or
      bounded windows.
- [ ] Task: Document freshness operation.
    - [ ] Include manual and scheduled run guidance.
    - [ ] Explain how freshness evidence updates the coverage matrix and
      workflow artifacts.
- [ ] Task: Conductor - User Manual Verification 'Workflow And Review Integration' (Protocol in workflow.md)
