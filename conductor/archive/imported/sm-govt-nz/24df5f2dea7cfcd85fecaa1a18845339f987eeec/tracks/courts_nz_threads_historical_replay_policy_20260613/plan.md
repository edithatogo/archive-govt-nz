# Plan - Courts of New Zealand Threads Historical Replay Policy

## Phase 1: Platform Constraints
- [x] Task: Confirm current Threads API posting limits and unsupported
  backdating behavior from official documentation.
- [x] Task: Estimate replay duration and daily volume for 738 archive records.
- [x] Task: Identify whether media or link handling changes replay risk.

## Phase 2: User-Facing Risk Review
- [x] Task: Assess how archival posts would appear in a current Threads feed.
- [x] Task: Compare alternatives: profile link to corpus, pinned explainer,
  sampled replay, or no replay.
- [x] Task: Define account trust and moderation guardrails.

## Phase 3: Decision
- [x] Task: Write the recommended replay policy.
- [x] Task: Update Threads adapter launch requirements based on the decision.
- [x] Task: Create a follow-up implementation track only if replay is approved.
- [x] Task: Keep `archive_replay_enabled` false for Threads and test that
  enabling it blocks the posting command before any post is sent.
