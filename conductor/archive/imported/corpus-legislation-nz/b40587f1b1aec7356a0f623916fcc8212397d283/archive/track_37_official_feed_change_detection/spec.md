# Specification - Official Feed Change Detection

## Overview

Add an official-feed change-detection path that watches NZ Legislation update
feeds and API/search metadata to identify new or changed legislation records.
This track is a redundancy and freshness layer; it must not replace the
canonical full-corpus bootstrap or claim historical completeness.

## Functional Requirements

- Discover and document the supported official update-feed mechanisms, including
  search-result RSS feeds and API-driven update queries where available.
- Implement or specify a poller that records feed item IDs, URLs, titles,
  publication/update timestamps, content hashes, and retrieval timestamps.
- Map feed/API items to known `work_id` and `version_id` values where possible.
- Emit a targeted refresh queue for work IDs or source URLs that should be
  checked by the canonical API-first downloader.
- Persist feed state so repeated polling is idempotent and auditable.
- Report unmapped feed items as coverage-review candidates rather than silently
  dropping them.

## Non-Functional Requirements

- Respect official site/API rate limits and existing project pacing defaults.
- Preserve provenance for every feed item and mapping decision.
- Keep the feed layer advisory until reconciled with official API records.
- Avoid overstating coverage; feeds are freshness signals, not full inventory.

## Acceptance Criteria

- Feed/API update discovery is documented with source URLs and caveats.
- A machine-readable feed-state artifact and refresh queue format are defined.
- Tests cover idempotent polling, duplicate feed entries, unmapped entries, and
  work/version mapping.
- Track evidence explains how feed-derived work is reconciled with the
  canonical API downloader.

## Out of Scope

- Full historical archive construction from feeds alone.
- Bypassing API limits or official site access controls.
- Treating feed text as canonical legislation content.
