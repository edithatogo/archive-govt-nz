# Spec - NZ Government Archive - multi-agency RSS feed onboarding and capture

## Problem
70 RSS sources have been identified across 12 government agencies with 421 entries already captured in initial probes. However, there is no automated scheduled capture pipeline or per-agency RSS config management.

## Scope
- Compile all RSS feed URLs from readiness matrix across agencies
- Create per-agency RSS feed configuration files
- Run initial capture for all configured agency feeds
- Set up scheduled daily RSS capture via GitHub Actions

## Technical Approach
- Use `feedparser` for RSS/Atom parsing (as evaluated in non-credential adapters track)
- Use `httpx` with retry/backoff for feed fetching
- Respect rate limits on agency servers
- Store raw payloads under `historical_archive_raw/rss/` and normalized under `historical_archive_normalized/rss/`

## Acceptance Criteria
- All 70 discovered RSS feeds are configured and captured
- 421+ RSS entries archived with full metadata (title, published date, URL, content/summary)
- Per-agency capture manifests available for downstream publication
- Scheduled daily capture workflow is active and verified
