# Plan - NZ Government Archive - per-agency source inventory and RSS feed configuration

## Track Metadata
- **Track ID**: `govt_archive_per_agency_configs_20260626`
- **Title**: NZ Government Archive - per-agency source inventory config files and RSS feed config files
- **Description**: Generate and maintain per-agency source inventory config files and RSS feed config files for all agencies with discovered RSS feeds, Bluesky accounts, and website pages.
- **Date Created**: 2026-06-26
- **Status**: Complete

## Dependencies
- Depends on `govt_archive_readiness_matrix_20260625` (completed)
- Depends on `govt_archive_noncredential_adapters_20260625` (completed)
- **Is dependency gate for**: `govt_archive_rss_onboarding_20260626`, `govt_archive_bluesky_onboarding_20260626`, `govt_archive_website_onboarding_20260626`, `govt_archive_youtube_onboarding_20260626`, `govt_archive_scheduled_multisource_20260626`

## Implementation Rules for Less-Capable Agents
- Work phases in order; do not skip dependency gates.
- After each phase, run `$conductor-review`, apply findings, rerun focused tests, then commit.
- Add a git note to every phase commit summarizing scope, tests, residual blockers, and next action.
- Configs must use stable agency IDs consistent with the registry and readiness matrix.

## Phase 1: Generate agency configs locally (DONE)
- [x] Task 1: Execute `python scripts/generate_agency_configs.py` to produce per-agency source inventory config files under `config/` directory.
- [x] Task 2: Verify that configs are generated for all agencies with discovered non-credentialed sources (RSS feeds, Bluesky accounts, website pages).
- [x] Task 3: Confirm 16+ source configs are generated as expected from the script.
- [x] Task 4: Review each config file for correct source-type fields, agency identifiers, and URL references.
- [x] Task 5: Ensure config files follow the consistent naming pattern `config/{agency_id}_sources.json` and `config/{agency_id}_rss_feeds.json`.

## Phase 2: Validate configs against existing archival data (DONE)
- [x] Task 6: Cross-reference generated configs with existing captured archival data for each agency.
- [x] Task 7: Verify RSS feed URLs in configs match discovered feeds from the readiness matrix.
- [x] Task 8: Verify Bluesky account handles in configs match registry entries.
- [x] Task 9: Verify website homepage URLs in configs match the 247 homepages manifest.
- [x] Task 10: Run `python scripts/validate_agency_configs.py` and confirm zero errors.
- [x] Task 11: Flag any discrepancies between configs and registry data for resolution.

## Phase 3: Verify via GitHub Actions remote archiving workflow (DONE)
- [x] Task 12: Trigger `archive_registered_sources.yml` on GitHub via `workflow_dispatch` with `--dry-run true --source-type all_feasible` and confirm it reads the generated configs from `config/` directory.
- [x] Task 13: Verify the workflow output report lists all non-credentialed source types (rss, bluesky, website_page, youtube) as selected with healthy counts.
- [x] Task 14: Commit config files and updated reports. Confirm CI quality gate (`ci.yml`) passes.

## Phase 4: Create agency-specific workflow patterns (DONE)
- [x] Task 15: Define per-agency capture workflow patterns based on available source types.
- [x] Task 16: Document agencies that have RSS-only, Bluesky-only, website-only, or multi-source profiles.
- [x] Task 17: Add metadata fields for capture priority, archival cadence, and source-type mix.
- [x] Task 18: Generate an agency config index file (`config/agencies_index.json`) for quick lookup.

## Acceptance Criteria
- [x] All agencies with discovered sources have valid, validated config files in `config/` directory.
- [x] Configs are consistent with registry agency IDs and readiness matrix source records.
- [x] Agency workflow patterns are documented and indexable for scheduled capture workflows.
- [x] 16+ agency configs are confirmed generated and validated.
- [x] GitHub Actions `archive_registered_sources.yml` runs successfully in dry-run mode consuming the generated configs.

## Commit and Review Protocol
- Commit after each phase with a concise hyphenated message.
- Add `git notes` describing implementation evidence and review status.
- Run `$conductor-review` after each phase and auto-apply review fixes before starting the next phase.
