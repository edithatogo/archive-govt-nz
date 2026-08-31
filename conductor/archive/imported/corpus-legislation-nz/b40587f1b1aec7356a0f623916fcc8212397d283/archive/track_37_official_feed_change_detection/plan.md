# Plan - Official Feed Change Detection

## Phase 1 - Source Discovery and Contract

- [x] Task: Document official feed/API update sources and caveats.
    - [x] Capture feed URL patterns, API/search parameters, and timestamp fields.
    - [x] Record rights, rate-limit, and completeness caveats.
- [x] Task: Define feed-state and refresh-queue schemas.
    - [x] Specify feed item identity, source URL, timestamps, content hash, and
      mapping status fields.
    - [x] Specify refresh queue fields for work IDs, version IDs, and unmapped
      review candidates.
- [x] Task: Conductor - User Manual Verification 'Source Discovery and Contract' (Protocol in workflow.md)

## Phase 2 - Polling and Mapping

- [x] Task: Add tests for feed polling and mapping behaviour.
    - [x] Cover duplicate feed entries and repeated polling.
    - [x] Cover mapped work/version IDs and unmapped candidate reporting.
- [x] Task: Implement feed polling and state persistence.
    - [x] Use structured XML/feed parsing instead of ad hoc text matching.
    - [x] Preserve retrieval provenance and source hashes.
- [x] Task: Implement refresh queue generation.
    - [x] Enqueue canonical API refreshes for mapped items.
    - [x] Emit review candidates for unmapped items.
- [x] Task: Conductor - User Manual Verification 'Polling and Mapping' (Protocol in workflow.md)

## Phase 3 - Workflow Integration and Evidence

- [x] Task: Add a conservative scheduled/manual workflow entry point.
    - [x] Keep it advisory and separate from full bootstrap writes.
    - [x] Upload feed-state and refresh-queue artifacts.
- [x] Task: Update documentation and Track 07 handoff notes.
    - [x] Explain how feed signals complement the full archive scheduler.
    - [x] Record validation commands and example artifact paths.
- [x] Task: Conductor - User Manual Verification 'Workflow Integration and Evidence' (Protocol in workflow.md)

## Verification Evidence

- 2026-07-01: Source-discovery evidence recorded in
  `docs/feed_change_detection.md`, including search-based RSS feeds,
  `https://api.legislation.govt.nz/api/rss/search/`, and the API `works/`
  search parameters used by the existing discovery client.
- 2026-07-01: `nzlc feed-change-detect` produced deterministic
  `feed_state.jsonl`, `refresh_queue.jsonl`, `review_candidates.jsonl`, and
  `feed_change_report.json` artifacts from a fixture feed with one mapped
  official item and one unmapped review candidate.
- 2026-07-01: Validation passed:
  `uv run python -m pytest -q -p no:cacheprovider tests\test_feed_change.py tests\test_official_feed_change_detection_workflow.py tests\smoke\test_cli_smoke.py -q`;
  `uv run ruff check --no-cache src\nz_legislation_corpus\feed_change.py src\nz_legislation_corpus\cli.py tests\test_feed_change.py tests\test_official_feed_change_detection_workflow.py`;
  `uv run ruff format --check src\nz_legislation_corpus\feed_change.py src\nz_legislation_corpus\cli.py tests\test_feed_change.py tests\test_official_feed_change_detection_workflow.py`;
  `uv run ty check src tests`; `git diff --check`.

## Phase: Review Fixes

- [x] Task: Apply review suggestions.
    - [x] Tightened feed URL host mapping so suffix-lookalike hosts do not map
      as official legislation URLs.
    - [x] Made `api.legislation.govt.nz` explicit in the workflow allowlist.
    - [x] Added optional `X-Api-Key` header support for official API RSS feeds.
    - [x] Added regression tests for lookalike hosts and API RSS workflow
      support.
