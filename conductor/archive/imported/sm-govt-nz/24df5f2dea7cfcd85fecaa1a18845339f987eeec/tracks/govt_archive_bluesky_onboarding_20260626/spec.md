# Spec - NZ Government Archive - multi-agency Bluesky account onboarding and capture

## Problem
5 NZ government Bluesky accounts have been identified (courtsofnz, beehivenz, health.govt.nz, healthnz.govt.nz, independent-childrens-monitor) but only courtsofnz has active archive capture configured. The remaining 4 accounts need onboarding.

## Scope
- Compile all NZ government Bluesky account handles from registry and readiness matrix
- Verify each account is resolvable via Bluesky API (valid DID, accessible profile)
- Create per-agency Bluesky source configurations
- Execute Bluesky post capture for all 5 accounts
- Archive Bluesky profile metadata for all accounts

## Technical Approach
- Use public Bluesky API endpoints (AT Protocol) - no credentials required for read-only capture
- Respect rate limits and pagination (max 100 posts per request)
- Store raw payloads under `historical_archive_raw/bluesky/` and normalized under `historical_archive_normalized/bluesky/`
- Capture profile metadata (avatar, banner, description, links) for identity verification

## Acceptance Criteria
- All 5 Bluesky accounts are configured and capturing successfully
- Bluesky posts archived with full content and metadata for each account
- Profile snapshots stored for identity verification and change tracking
- Per-account capture manifests available for downstream publication
