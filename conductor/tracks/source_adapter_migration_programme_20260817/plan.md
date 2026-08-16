# Track 5 Plan: Source Adapter Migration Programme

## Phases

### Phase 1: Async Base Adapter Architecture
- [x] Implement `AsyncBaseCaptureAdapter` and `AdapterCaptureResult` in `src/archive_govt_nz/capture/base.py`.
- [x] Standardize retry logic, backoff, and CAS streaming writes.

### Phase 2: Family-by-Family Adapter Migration
- [x] Migrate Feeds adapter (`RSS`, `Atom`, `JSON Feed`) in `src/archive_govt_nz/capture/feeds/`.
- [x] Migrate Bluesky/ATProto adapter in `src/archive_govt_nz/capture/social/bluesky.py`.
- [x] Migrate Threads, X, YouTube, and Email newsletter adapters.

### Phase 3: Unit Testing & Fixture Replay
- [x] Create comprehensive transport mock test suites in `tests/capture/`.
- [x] Verify >95% branch coverage across all adapter modules.

### Phase 4: Assurance & Parity Verification
- [x] Verify each adapter against 18 quality gates and >95% test coverage.
