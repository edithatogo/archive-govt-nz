# Specification - Courts of New Zealand Bluesky Launch Operations

## Overview
Make the Bluesky mirror reliable enough for MVP launch by tightening scheduled
run monitoring, duplicate detection, CI warnings, and operational reporting.

## Requirements
1. Keep manual and scheduled runs bounded and observable.
2. Detect mismatches between intended state and public mirror feed.
3. Resolve non-blocking CI annotations that could become blockers, including
   Node.js action runtime deprecation and invalid Vale path fallback.
4. Preserve a clear rollback/disable procedure for accidental posting.

## Acceptance Criteria
- A runbook documents how to pause the workflow, inspect latest state, and
  verify public posts.
- CI no longer emits known avoidable warnings where the fix is under repo
  control.
- A smoke check can compare recent state entries with public Bluesky feed URLs.
- Launch status is visible in conductor docs.
