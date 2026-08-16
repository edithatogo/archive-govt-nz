# Specification - Courts of New Zealand Bluesky Archive Replay

## Overview
Finish mirroring the Courts of New Zealand archive corpus to
`mirnzcourts.bsky.social` through bounded, duplicate-safe batches. The active
coverage scope is the current Bluesky source archive plus recovered historical X
records.

## Requirements
1. Source coverage:
   - Mirror all archived `courtsofnz.bsky.social` records tracked in
     `historical_archive/`.
   - Mirror all recovered historical X records tracked in
     `historical_archive_normalized/x/`.
   - Preserve original source URLs and original dates in mirror content or
     archive metadata.
2. State separation:
   - Use `conductor/bluesky_backlog_state.json` for Bluesky-source archive
     backlog.
   - Use `conductor/archive_mirror_state.json` for recovered X archive replay.
   - Use `conductor/archive_mirror_coverage.json` as the reporting surface.
3. Safety:
   - Keep batch sizes bounded until the replay can be reviewed safely.
   - Do not treat Bluesky publication time as historical backdating.
   - Do not replay LinkedIn, RSS, email, or website records until separate
     tracks approve those sources for outbound posting.

## Acceptance Criteria
- Coverage reaches `49/49` for Bluesky-source records on the Bluesky mirror.
- Coverage reaches `689/689` for recovered X records on the Bluesky mirror, or
  any exclusions are listed with reasons.
- Every mirror replay post is reflected in git-backed state.
- The corpus manifest can map source record IDs to mirror URLs.
