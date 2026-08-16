# Plan - NZ Government Archive - multi-agency Bluesky account onboarding and capture

## Track Metadata
- **Track ID**: `govt_archive_bluesky_onboarding_20260626`
- **Title**: NZ Government Archive - multi-agency Bluesky account onboarding and capture
- **Description**: Capture and archive Bluesky posts from all discovered NZ government Bluesky accounts.
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
- Use public Bluesky API endpoints (AT Protocol) -- no credentials or tokens required for read-only capture.
- Respect rate limits and pagination (max 100 posts per request).

## Phase 1: (DONE) Identify all Bluesky accounts
- [x] Task 1: Compile the full list of NZ government Bluesky account handles from the registry and readiness matrix.
- [x] Task 2: Confirm 5 accounts: `courtsofnz`, `beehivenz`, `health.govt.nz`, `healthnz.govt.nz`, `independent-childrens-monitor`.
- [x] Task 3: Verify each account is resolvable via the Bluesky API (valid DID, accessible profile).
- [x] Task 4: Document account metadata (display name, description, follower count, creation date).

## Phase 2: (DONE) Create per-agency Bluesky source configurations
- [x] Task 5: Generate per-agency Bluesky source config files alongside agency configs.
- [x] Task 6: Include Bluesky DID, handle, profile endpoint URL, and capture parameters.
- [x] Task 7: Store configs in `config/bluesky/` directory referenced by agency ID.
- [x] Task 8: Validate configs against live Bluesky API responses.

## Phase 3: (DONE) Run Bluesky capture via GitHub Actions
- [x] Task 9: Execute Bluesky capture for `courtsofnz` account (DONE - confirmed working via existing `archive_sources.yml`).
- [x] Task 10: Trigger `archive_registered_sources.yml` via `workflow_dispatch` with `--source-type bluesky --dry-run true` -- confirm 5 accounts selected.
- [x] Task 11: Run Bluesky capture via `archive_registered_sources.yml` with `--source-type bluesky --dry-run false` for all 5 accounts.
- [x] Task 12: Execute Bluesky capture for `beehivenz` account individually via `archive_bluesky_history.py` if needed for verification.
- [x] Task 13: Execute Bluesky capture for `health.govt.nz` account.
- [x] Task 14: Execute Bluesky capture for `healthnz.govt.nz` account.
- [x] Task 15: Execute Bluesky capture for `independent-childrens-monitor` account.
- [x] Task 16: Verify captured posts include full content, timestamp, and metadata.
- [x] Task 17: Generate per-account capture summary with post counts.

## Phase 4: (DONE) Archive Bluesky profiles for all accounts
- [x] Task 18: Capture and store Bluesky profile metadata (avatar, banner, description, links) for each account.
- [x] Task 19: Generate profile archive snapshot with timestamp for provenance.
- [x] Task 20: Store profile archives alongside captured posts in agency archive directories.

## Phase 5: (DONE) Set up ongoing scheduled Bluesky capture via GitHub Actions
- [x] Task 21: Create `.github/workflows/archive_bluesky_scheduled.yml` for scheduled every-6-hour Bluesky capture (e.g., `cron: "7 */6 * * *"`).
- [x] Task 22: Configure workflow to run `python -m scripts.archive_registered_sources --source-type bluesky --dry-run false` and commit state updates.
- [x] Task 23: Add `workflow_dispatch` trigger with parameters: `agency_id` (optional filter), `dry_run`, `commit_payloads`.
- [x] Task 24: Add profile refresh step to the workflow (weekly cadence via conditional step).
- [x] Task 25: Verify workflow runs successfully via `workflow_dispatch` before enabling cron schedule.
- [x] Task 26: Enable cron schedule and confirm first auto-run completes.

## Acceptance Criteria
- [x] All 5 Bluesky accounts are configured and capturing successfully via GitHub Actions.
- [x] Bluesky posts archived with full content and metadata for each account.
- [x] Profile snapshots stored for identity verification and change tracking.
- [x] `archive_bluesky_scheduled.yml` workflow is active and verified with at least one successful auto-run.

## Commit and Review Protocol
- Commit after each phase with a concise hyphenated message.
- Add `git notes` describing implementation evidence and review status.
- Run `$conductor-review` after each phase and auto-apply review fixes before starting the next phase.
