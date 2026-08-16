# Track 5 Plan: Source Adapter Migration Programme

## Phases

### Phase 1: Base Protocol & Feeds Migration
- [ ] Implement `AsyncBaseCaptureAdapter` and common HTTP error classifiers.
- [ ] Migrate RSS/Atom and JSON feed harvester with CAS integration.
- [ ] Build test fixtures and mock transports.

### Phase 2: Social Media Adapters (Bluesky, Threads, X)
- [ ] Implement Bluesky adapter (AT Protocol feed parsing, handle resolution, media downloading).
- [ ] Implement Threads adapter (Meta Graph API & fallback).
- [ ] Implement X/Twitter feed ingestion.

### Phase 3: Video & Newsletter Payloads (YouTube, Email)
- [ ] Implement YouTube channel harvester and transcript extractor.
- [ ] Implement Cloudflare Email Worker webhook payload ingester.

### Phase 4: Assurance & Parity Verification
- [ ] Verify each adapter against 18 quality gates and >95% test coverage.
