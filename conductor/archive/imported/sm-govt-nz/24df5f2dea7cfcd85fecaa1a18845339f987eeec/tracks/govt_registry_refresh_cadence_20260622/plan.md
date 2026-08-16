# Plan - Registry Verification Refresh Cadence

## Phase 1: Metadata Model
- [x] Task: Decide whether refresh metadata lives inline on profile records or in a companion report file.
- [x] Task: Add `last_checked_at`, `last_seen_at`, and `verification_status` support where needed.
- [x] Task: Add schema tests for refresh metadata.

Decision: refresh metadata is optional inline JSON on profile records, while
`conductor/registry_refresh_report.json` is the companion operational artifact.
Compiled SQLite registry output remains a source-registry compilation artifact and
does not persist refresh metadata in this track.

## Phase 2: Refresh Report
- [x] Task: Implement a non-mutating report command for stale and due-for-review records.
- [x] Task: Group report output by agencies, parties, MPs, public sector leaders, and historical figures.
- [x] Task: Add tests for monthly, event-triggered, and annual cadence calculations.

## Phase 3: Conductor Operations
- [x] Task: Document refresh cadence in the active registry expansion track.
- [x] Task: Add report artifact path under `conductor/`.
- [x] Task: Add CI or manual workflow guidance after the report command is stable.

## Verification
- [x] Task: Run focused refresh report tests.
- [x] Task: Run registry schema tests.
- [x] Task: Update `conductor/tracks.md` and `conductor/setup_state.json`.

## Output
- Command: `python scripts/report_refresh_cadence.py --as-of 2026-06-22 --output conductor/registry_refresh_report.json`
- Initial report: 610 profiles due across 276 records because existing profile
  records have not yet populated `last_checked_at`; manual-review count is 0.
- Next refresh cohort: agencies first (`483` profiles due across `218` records),
  followed by MPs, parties, then historical figures.
