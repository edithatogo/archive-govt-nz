# Phase 2 Review - Archive Schema and Deduplication

## Status
Phase 2 is complete.

## Completed Tasks
- Added `src/archive_schema.py` with normalized archive record validation and
  stable content hashing.
- Added source-specific raw archive roots under `historical_archive_raw/`.
- Added normalized JSONL shard roots under `historical_archive_normalized/`.
- Added `src/archive_dedupe.py` for canonical URL dedupe with content-hash
  fallback.
- Added `src/archive_state.py` and `conductor/archive_state.json` so archive
  backfills cannot advance outbound syndication state.

## Review Findings
- No blocking issues found.
- Archive state is isolated from `conductor/state.json`.
- Raw and normalized archive paths are checked against the source contracts.
- Dedupe preserves source records and groups related records without deleting
  provenance.
- The schema is ready for source-specific historical backfill adapters.

## Validation
- `python -m pytest`
- `ruff check --no-cache src tests scripts`
- JSON validation for conductor metadata, config files, and archive state
- GitHub CI and Pages checks on preceding Phase 2 task commits

## Phase 3 Entry Criteria
Phase 3 can start. The next boundary is historical backfill execution:

- Re-run Bluesky history capture idempotently and write a gap report.
- Build historical X backfill from public CDX metadata first.
- Add LinkedIn historical capture only after access is available.
- Archive RSS histories from discovered feeds.
- Keep all historical records out of live posting targets.
