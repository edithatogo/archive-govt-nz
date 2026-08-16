# Spec - NZ Government Archive - scheduled multi-agency capture workflow

## Problem
Individual per-source-type capture scripts exist but there is no integrated scheduled workflow that runs multi-agency archival capture for all source types (RSS, Bluesky, website, YouTube) on a recurring basis.

## Scope
- Update `archive_registered_sources.yml` with schedule trigger
- Create per-source-type scheduled workflows (RSS daily, Bluesky every 6h, website weekly, YouTube weekly)
- Set up multi-agency archive state tracking with last-capture timestamps
- Add notification/alerting on workflow failure
- Verify all workflows run successfully

## Dependencies
This track is the final integration step and depends on all per-source-type onboarding tracks completing first.

## Acceptance Criteria
- Master scheduled workflow runs automatically on cron schedule
- Per-source-type scheduled workflows run at appropriate cadences
- Multi-agency archive state tracking is active and captures are recorded
- All workflows verified with at least one successful run
- Schedule documentation available in conductor directory
