# Review - NZ Government Archive - per-agency source inventory and RSS feed configuration

## Track Metadata
- **Track ID**: `govt_archive_per_agency_configs_20260626`
- **Status**: Complete
- **Review Date**: 2026-06-27
- **Commits**: `0df7973`, `2cc083e`, `a102651`, `02e67b8`

## Implementation Summary

### Phase 1: Generate agency configs locally (DONE)
- Executed `python scripts/generate_agency_configs.py` successfully.
- Generated 16 per-agency source config files under `config/` directory.
- Config files follow consistent naming pattern `config/{agency_id}_sources.json` and `config/{agency_id}_rss_feeds.json`.
- Fixed generator to skip Bluesky contracts with empty account handles (independent-childrens-monitor had unresolved Bluesky handle).
- Removed stale `courts_nz_*` (underscore) duplicate files, standardized on `courts-of-nz_*` (hyphen) canonical naming.

### Phase 2: Validate configs against existing archival data (DONE)
- Ran `python scripts/validate_agency_configs.py` — ALL CONFIGS VALID with zero errors.
- 16 sources files and 12 rss_feeds files validated.
- Cross-checked agency IDs between sources and rss_feeds configs — no mismatches.
- courts-of-nz config verified to have both Bluesky + RSS contracts.

### Phase 3: Verify via GitHub Actions remote archiving workflow (DONE)
- Triggered `archive_registered_sources.yml` via `workflow_dispatch` with `--dry-run true --source-type all_feasible`.
- Workflow completed successfully (run ID: 28284003116, conclusion: success).
- Updated all code references from `courts_nz_sources.json` to canonical `courts-of-nz_sources.json` across 7 files (src/source_inventory.py, scripts/archive_rss_history.py, scripts/archive_current_sources.py, scripts/discover_courts_rss.py, src/rss_discovery.py, SETUP_GUIDE.md, docs/courts-nz-adapter-contracts.md).
- Updated test assertions to match canonical agency ID `courts-of-nz` and non-credentialed contract set (bluesky + rss).
- CI quality gate passes: 439 tests passed, Ruff checks passed.

### Phase 4: Create agency-specific workflow patterns (DONE)
- Generated `config/agencies_index.json` with per-agency metadata.
- Documented workflow patterns: 4 multi-source, 11 RSS-only, 1 website-only.
- Added metadata fields: capture_priority, archival_cadence, source_types, workflow_pattern.
- Summary: 16 total agencies, 12 with RSS feeds, 4 with Bluesky accounts.

## Acceptance Criteria Verification

| Criterion | Status |
|---|---|
| All agencies with discovered sources have valid, validated config files | Pass |
| Configs are consistent with registry agency IDs and readiness matrix | Pass |
| Agency workflow patterns are documented and indexable | Pass |
| 16+ agency configs confirmed generated and validated | Pass (16) |
| GitHub Actions archive_registered_sources.yml runs successfully in dry-run | Pass |

## Test Results
- **pytest**: 439 passed, 0 failed
- **Ruff**: All checks passed
- **CI**: conclusion=success (commit 02e67b8)

## Residual Notes
- `independent-childrens-monitor` Bluesky handle is unresolved (empty account in manifest). The agency has a website-only config until the Bluesky handle is manually resolved.
- The `courts_nz_sources.json` (underscore) legacy filename has been fully replaced by `courts-of-nz_sources.json` (hyphen) across all code, tests, and documentation.

## Overall: Track Complete — Ready to archive. No blocking issues.