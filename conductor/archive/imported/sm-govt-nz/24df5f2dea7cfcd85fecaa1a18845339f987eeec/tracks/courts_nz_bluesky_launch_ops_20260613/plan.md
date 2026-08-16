# Plan - Courts of New Zealand Bluesky Launch Operations

## Phase 1: Workflow Health
- [x] Task: Fix the Vale path warning or document why the fallback is retained.
- [x] Task: Update GitHub Actions versions or runner settings for the Node.js
  20 deprecation warning.
- [x] Task: Confirm scheduled `Syndicate` runs use the intended branch and
  secrets.

## Phase 2: Operational Smoke Checks
- [x] Task: Add a non-posting smoke script that reads state and public Bluesky
  feed records.
- [x] Task: Add tests for smoke-check parsing and failure modes.
- [x] Task: Wire smoke checks into CI or a manual workflow gate.

## Phase 3: Runbook
- [x] Task: Document pause/resume steps for `Syndicate`.
- [x] Task: Document how to inspect replay coverage and latest public posts.
- [x] Task: Document rollback boundaries for state files versus public posts.
