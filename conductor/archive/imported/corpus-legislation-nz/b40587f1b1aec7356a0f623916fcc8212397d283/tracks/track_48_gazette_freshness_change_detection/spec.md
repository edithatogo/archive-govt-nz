# Specification - Gazette Freshness And Change Detection

## Overview

Add a freshness layer for the NZ Gazette archive that detects new or changed
Gazette material and enqueues targeted source refreshes. This track complements
the source archives and canonical builder; it is not a replacement for
periodic full source review.

## Functional Requirements

- Poll official Gazette freshness surfaces, including issue listings, search
  result feeds where available, and notice listing/search pages permitted by
  the source registry.
- Poll DigitalNZ Gazette deltas through `dnz` or a documented DigitalNZ API
  query using stable sorting, page state, and date/update filters where
  available.
- Store freshness state with source ID, feed/search URL, item ID, source URL,
  first-seen timestamp, last-seen timestamp, last-modified/ETag where
  available, content hash where available, and enqueue decision.
- Emit targeted refresh queues for Tracks 42, 43, 44, 45, and 46 instead of
  triggering broad re-harvests by default.
- Record deleted, withdrawn, changed, duplicate, blocked, and unchanged states
  explicitly.
- Preserve enough provenance to explain why a source refresh or canonical
  rebuild was triggered.

## Non-Functional Requirements

- Keep polling conservative, identifiable, rate-limited, and safe to run on a
  schedule.
- Keep state deterministic and resumable.
- Avoid treating feed/search metadata as canonical content.
- Make freshness output compatible with Track 41 coverage matrix and Track 47
  workflow artifacts.

## Acceptance Criteria

- A bounded freshness smoke run can detect at least one official Gazette item
  and one DigitalNZ Gazette item without running a full archive.
- Freshness state and refresh queues are deterministic and reviewable.
- Tests cover new, changed, unchanged, duplicate, withdrawn/deleted, and blocked
  item states.
- Documentation explains how freshness queues feed source-specific archives and
  canonical rebuilds.

## Out of Scope

- Full source harvesting.
- Public publication.
- Treating RSS/search/DigitalNZ freshness metadata as canonical Gazette text.
