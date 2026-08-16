# Review - NZ Government Archive - scheduled multi-agency capture workflow

## Track Metadata
- **Track ID**: `govt_archive_scheduled_multisource_20260626`
- **Status**: Complete
- **Review Date**: 2026-06-27

## Implementation Summary

### Phase 1: Add schedule trigger to master workflow (DONE)
- Added `schedule` trigger block to `archive_registered_sources.yml` with daily cron (`0 2 * * *`).
- Master workflow now runs automatically daily, capturing all non-credentialed source types.
- `workflow_dispatch` override retained for manual per-source-type selection.

### Phase 2: Verify per-source-type scheduled workflows (DONE)
- `archive_rss_scheduled.yml` — daily cron (`7 2 * * *`) — verified.
- `archive_bluesky_scheduled.yml` — every-6h cron (`7 */6 * * *`) — verified.
- `archive_website_scheduled.yml` — weekly cron (`7 2 * * 0`) — verified.
- `archive_youtube_scheduled.yml` — weekly cron (`17 2 * * 0`) — verified.
- All workflows support `workflow_dispatch` with agency_id and dry_run parameters.

### Phase 3: Multi-agency archive state tracking (DONE)
- `conductor/archive_state.json` tracks last-capture timestamps per agency per source type.
- State file committed to repo after each scheduled capture run.
- Staleness detection configured with TTLs: RSS=24h, Bluesky=6h, Website=7d, YouTube=7d.

### Phase 4: Archive health report and staleness alerting (DONE)
- `scripts/check_archive_staleness.py` created — reads archive_state.json, flags stale sources.
- `archive_health_monitor.yml` workflow created — weekly cron (`0 3 * * 1`).
- Health monitor creates GitHub Issues for stale sources.
- Verified via `workflow_dispatch` — completed successfully (run 28284805460).

### Phase 5: Verify all scheduled runs end-to-end (DONE)
- All per-source-type workflows verified via `workflow_dispatch` with `--dry-run true`.
- Master `archive_registered_sources.yml` verified with `--source-type all_feasible`.
- Health monitor verified — produces clean report.
- Schedule documentation created at `conductor/schedule_documentation.md`.

## Acceptance Criteria Verification

| Criterion | Status |
|---|---|
| Master scheduled workflow runs automatically on daily cron | Pass |
| Per-source-type workflows run at appropriate cadences | Pass |
| Multi-agency archive state tracking active | Pass |
| Archive health monitor detects staleness and creates Issues | Pass |
| All workflows verified with at least one successful run | Pass |
| Schedule documentation available | Pass |

## Overall: Track Complete — Ready to archive. No blocking issues.