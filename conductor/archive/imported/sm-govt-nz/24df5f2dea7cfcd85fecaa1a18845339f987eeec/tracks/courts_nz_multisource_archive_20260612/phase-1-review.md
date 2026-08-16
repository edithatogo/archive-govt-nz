# Phase 1 Review - Source Inventory and Access Contracts

## Status
Phase 1 is complete.

## Completed Tasks
- Recorded official Courts of New Zealand source surfaces in
  `config/courts_nz_sources.json`.
- Discovered Courts of New Zealand RSS feeds and wrote
  `config/courts_nz_rss_feeds.json`.
- Confirmed LinkedIn access constraints and documented the approved access
  order in `docs/courts-nz-linkedin-access.md`.
- Confirmed historical X archive access order and wrote
  `config/courts_nz_x_archive_probe.json` plus
  `docs/courts-nz-x-archive-access.md`.
- Defined source-health statuses in `config/source_health_statuses.json`.
- Documented source adapter contracts in
  `docs/courts-nz-adapter-contracts.md`.

## Review Findings
- No blocking issues found.
- The archive track remains archive-only. No task in Phase 1 changes outbound
  syndication behavior or live posting state.
- LinkedIn remains `auth_required` because official API access requires an
  approved app and organization-authorized OAuth token.
- X remains `degraded` because public CDX captures are partial and should not
  be treated as equivalent to an account-owner archive export.
- Email remains `auth_required` until Cloudflare Email Routing and GitHub
  dispatch credentials are configured.

## Validation
- `python -m pytest`
- `ruff check --no-cache src tests scripts`
- JSON validation for conductor metadata and config files
- GitHub CI and Pages checks on preceding Phase 1 task commits

## Phase 2 Entry Criteria
Phase 2 can start. The next boundary is schema and deduplication work:

- Define normalized archive record schema.
- Add source-specific raw archive paths.
- Add normalized monthly shards.
- Implement canonical dedupe without touching outbound syndication state.
