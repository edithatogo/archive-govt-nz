# Plan - NZ Government Archive - multi-agency RSS feed onboarding and capture

## Track Metadata
- **Track ID**: `govt_archive_rss_onboarding_20260626`
- **Title**: NZ Government Archive - multi-agency RSS feed onboarding and capture
- **Description**: Capture and archive RSS/Atom feeds from all discovered government agencies with active feeds.
- **Date Created**: 2026-06-26
- **Status**: Complete

## Dependencies
- **Depends on**: `govt_archive_per_agency_configs_20260626` (per-agency configs must exist)
- Depends on `govt_archive_readiness_matrix_20260625` (completed)
- Depends on `govt_archive_noncredential_adapters_20260625` (completed)
- **Is dependency gate for**: `govt_archive_scheduled_multisource_20260626`

## Implementation Rules for Less-Capable Agents
- Work phases in order; do not skip dependency gates.
- After each phase, run `$conductor-review`, apply findings, rerun focused tests, then commit.
- Add a git note to every phase commit summarizing scope, tests, residual blockers, and next action.
- Use `feedparser` for RSS/Atom parsing as evaluated in non-credential adapters track.
- Respect rate limits and use `httpx` with retry/backoff for feed fetching.
- All RSS capture uses public feeds -- no credentials or tokens required.

## Phase 1: Identify all RSS feed URLs per agency (DONE)
- [x] Task 1: Compile the full list of RSS feed URLs from the readiness matrix across all agencies.
- [x] Task 2: Confirm 70 RSS sources identified across all government agencies.
- [x] Task 3: Map feeds to agencies using agency configs from `govt_archive_per_agency_configs_20260626`.
- [x] Task 4: Verify 12 agencies with captured content have correct feed URLs assigned.
- [x] Task 5: Document any feed URLs that failed resolution or returned errors.

## Phase 2: Create per-agency RSS feed configs (DONE)
- [x] Task 6: Generate per-agency RSS feed configuration files referencing discovered feed URLs.
- [x] Task 7: Include feed metadata (feed type, update frequency, content type, last-modified headers).
- [x] Task 8: Store configs alongside agency source configs in `config/rss/` directory referenced by agency ID.
- [x] Task 9: Validate feed configs against live feed endpoints (HTTP 200, valid XML/JSON).

## Phase 3: Run RSS capture via GitHub Actions (DONE)
- [x] Task 10: Trigger `archive_registered_sources.yml` via `workflow_dispatch` with `--source-type rss --dry-run true` and confirm all 70 RSS feed URLs are selected.
- [x] Task 11: Run RSS capture via `archive_registered_sources.yml` with `--source-type rss --dry-run false` to capture live feed data.
- [x] Task 12: Confirm 421+ entries captured across all agencies.
- [x] Task 13: Verify captured entries include title, published date, URL, and content/summary in normalized JSONL format.
- [x] Task 14: Check for duplicate entries across capture runs and apply deduplication.
- [x] Task 15: Validate captured data against original feed content for sampling of feeds.
- [x] Task 16: Generate capture summary report with per-agency entry counts.

## Phase 4: Set up ongoing scheduled RSS capture via GitHub Actions (DONE)
- [x] Task 17: Create `.github/workflows/archive_rss_scheduled.yml` for scheduled daily RSS capture (e.g., `cron: "7 2 * * *"`).
- [x] Task 18: Configure workflow to run `python -m scripts.archive_registered_sources --source-type rss --dry-run false` and commit state updates.
- [x] Task 19: Add `workflow_dispatch` trigger with parameters: `agency_id` (optional filter), `dry_run` (default: false), `commit_payloads`.
- [x] Task 20: Verify scheduled workflow runs successfully via `workflow_dispatch` before enabling the cron schedule.
- [x] Task 21: Enable cron schedule and confirm first auto-run completes successfully.

## Acceptance Criteria
- [x] All 70 discovered RSS feeds are configured and captured via GitHub Actions.
- [x] 421+ RSS entries archived with full metadata in normalized format.
- [x] Per-agency capture manifests available for downstream publication.
- [x] `archive_rss_scheduled.yml` workflow is active and verified with at least one successful auto-run.

## Commit and Review Protocol
- Commit after each phase with a concise hyphenated message.
- Add `git notes` describing implementation evidence and review status.
- Run `$conductor-review` after each phase and auto-apply review fixes before starting the next phase.
