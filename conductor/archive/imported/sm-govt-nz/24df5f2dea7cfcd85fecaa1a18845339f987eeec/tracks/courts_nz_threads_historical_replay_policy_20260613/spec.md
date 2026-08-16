# Specification - Courts of New Zealand Threads Historical Replay Policy

## Overview
Decide whether historical Courts of New Zealand archive records should be
published to Threads even though Threads cannot be treated as a backdated
historical import target. This is a policy and guardrail track, not a posting
track.

## Requirements
1. Treat Threads historical replay as current publication of archival records.
2. Preserve original source timestamps in post text and corpus metadata if
   replay is approved.
3. Estimate user-facing noise, API quota impact, account trust risk, and
   moderation risk.
4. Define approval criteria before any historical Threads replay job is built.
5. Keep Threads historical replay disabled until this track is reviewed.

## Acceptance Criteria
- A written decision recommends `do not replay`, `limited sample replay`, or
  `bounded full replay`.
- The decision cites platform limits, account-risk considerations, and corpus
  preservation alternatives.
- If replay is approved, a later implementation track defines state, batch
  size, payload format, and verification.
- If replay is rejected, the corpus remains available through GitHub Pages,
  Hugging Face, Zenodo, and Bluesky mirror replay.

## Decision
Historical Threads replay is deferred and must remain disabled. Threads live
and ongoing posting may continue, but archive records must not be replayed to
Threads because the platform cannot backdate them and they would appear as new
current posts. Historical access is handled through the repository corpus,
GitHub Pages, Hugging Face, Zenodo, and any platform that can preserve or
clearly label archive context without flooding the current feed.
