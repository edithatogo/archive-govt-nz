# Track 5 Specification: Source Adapter Migration Programme

## Purpose
Staged, evidence-backed migration of donor capture capabilities into standard target source adapters.

## Context & Scope
Migrate donor capture capabilities across discrete source families:
1. Feeds (`RSS/Atom`, `JSON Feed`)
2. Bluesky (`AT Protocol`)
3. Threads (`Meta Graph API` & Playwright fallback)
4. X / Twitter (`Feed` & operator sessions)
5. YouTube (`Channel RSS`, transcripts, video metadata)
6. Newsletters / Email (`Cloudflare Email Worker` payloads)
7. Website / Browser single-page snapshots (`ArchiveBox` container runner)

## Per-Adapter 8-Stage Migration Protocol
Every source adapter must pass the following 8 stages before promotion:
1. Fixture baseline construction
2. Target adapter contract implementation (`AsyncBaseCaptureAdapter`)
3. Compatibility test suite
4. Source-vs-target parity verification
5. Canary execution in staging
6. Live read-only verification
7. Target promotion to scheduled pipeline
8. Donor adapter deprecation

## Deliverables
- `src/archive_govt_nz/capture/base.py`
- `src/archive_govt_nz/capture/feeds/`
- `src/archive_govt_nz/capture/social/`
- `src/archive_govt_nz/capture/video/`
- `src/archive_govt_nz/capture/newsletters/`
- Comprehensive unit, integration, and contract test suites
