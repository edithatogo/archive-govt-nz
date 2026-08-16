# Specification - Courts of New Zealand Threads Adapter Launch

## Overview
Implement the Threads outbound adapter and launch it through the same controlled
mirror-account guardrails used for Bluesky. This track must not begin until the
Threads API credential track is complete.

## Requirements
1. Use the dedicated Threads mirror account `mirnzcourts`, not a personal
   Threads or Instagram identity.
2. Implement posting behind an explicit `config.json` enable flag.
3. Preserve source text and attribution without commentary.
4. Use duplicate-prevention state separate from Bluesky, X, archive, and
   Threads historical replay review state.
5. Start with new forward posts only; historical replay is governed by a
   separate policy track.

## Acceptance Criteria
- The adapter has unit tests for text formatting, attribution, API payloads,
  errors, and duplicate state.
- A dry run maps the latest Courts of New Zealand source post to the intended
  Threads payload without publishing.
- A controlled live test publishes one post only after credentials validate.
- The live Threads URL is recorded in state and conductor notes.

## Current Launch State
- Forward-only Threads mirroring is enabled for new Courts of New Zealand
  Bluesky posts.
- Threads historical replay remains disabled under the separate historical
  replay policy.
- The first Threads-enabled `Syndicate` workflow run passed credential
  validation and probing but found zero new source posts, so public Threads URL
  verification remains pending.
- `scripts/threads_dry_run_latest.py` provides the non-posting launch review
  payload for the latest source post.
