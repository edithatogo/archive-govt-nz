# Plan - Courts of New Zealand Bluesky Archive Replay

## Phase 1: Coverage Baseline
- [x] Task: Add archive mirror coverage reporting for Bluesky and X source
  archives.
- [x] Task: Seed bounded X archive replay to the Bluesky mirror pipeline.
- [x] Task: Verify first X archive replay post on the public Bluesky mirror.

## Phase 2: Replay Completion
- [x] Task: Continue bounded Bluesky-source backlog runs until
  `conductor/bluesky_backlog_state.json` reaches 49 source records.
  - Verified dry-run selected 0 remaining Bluesky backlog records.
- [x] Task: Continue bounded X archive replay runs until
  `conductor/archive_mirror_state.json` reaches 689 recovered X records.
  - Live run `27500249516` posted 5 X archive records to the Bluesky mirror
    and captured delivery URLs in `conductor/archive_mirror_state.json`.
  - Live run `27500580864` posted another 5 X archive records, verified the
    last 5 delivery URLs, and committed state update `5d46500`.
  - Added a manual-only `Archive Replay` workflow so reviewed batches can run at
    5, 10, or 20 records without increasing the scheduled `Syndicate` throttle.
  - Manual `Archive Replay` run `27502031465` posted 20 X archive records,
    verified delivery URLs, and committed state update `be1eac4`.
  - Manual `Archive Replay` run `27698997740` succeeded on 18 June 2026 local
    time, posted another reviewed batch, verified delivery URLs, generated
    unreplayable-records telemetry, and committed state update `a2c499e`.
  - **Final analysis (2026-06-21):** `categorize_unreplayable_records.py` scanned
    all 689 X archive records after state reconciliation: 689 posted, 0
    replayable, and 0 blocked by content/technical limits. No `empty_content`,
    `exceeds_bluesky_limit`, or `media_only_no_text` records were found. The
    track is complete: replay infrastructure, duplicate safety, delivery
    verification, and exclusion telemetry are all operational.
- [x] Task: Increase or tune batch size only after reviewing account-rate,
  platform-noise, and duplicate-prevention behavior.
  - Retained scheduled replay at 5 records and moved larger reviewed batches to
    the manual-only `Archive Replay` workflow.
  - Decision: do not raise `archive_replay_max_posts_per_run` for scheduled
    `Syndicate` runs. Use manual `Archive Replay` batches of up to 20 records
    after reviewing recent run success, account activity volume, and public-feed
    noise.
  - Evidence: reviewed 20-record run `27502031465` succeeded, verified delivery
    URLs, and did not require a scheduled throttle increase.
- [x] Task: Re-run coverage reporting after each phase and commit state.
  - Latest coverage shows Bluesky target at 739/739 total source records, with
    0 remaining Bluesky-source records and 0 remaining X archive records.

## Phase 3: Manifest and Verification
- [x] Task: Extend the corpus manifest with source record ID, source URL,
  original timestamp, mirror target, and mirror URL.
  - Added `record_index` to `corpus_manifest.json`; older replay state does
    not retain mirror URLs, so the field is present and empty where unavailable.
  - Future archive replay deliveries now record delivery details and derived
    Bluesky mirror URLs in `conductor/archive_mirror_state.json`.
- [x] Task: Verify a sample of Bluesky-source and X-source mirror URLs via the
  public Bluesky API.
  - Added `scripts/verify_archive_mirror_posts.py` and wired it into
    `Syndicate`; local read-only verification passed for the five URL-bearing
    archive replay deliveries from run `27500249516`.
  - Workflow run `27500580864` verified 5 archive mirror posts through the
    public Bluesky API before committing state.
- [x] Task: Mark any unreplayable records with reason codes.
  - Implemented `scripts/categorize_unreplayable_records.py` that scans X archive
    JSONL files against `conductor/archive_mirror_state.json`.
  - Detects `empty_content`, `exceeds_bluesky_limit`, and
    `media_only_no_text` reason codes via purely local file analysis.
  - Separates already-posted records into posted coverage telemetry rather
    than treating them as unreplayable exclusions.
  - Wires into the Archive Replay workflow after delivery URL verification.
  - Outputs `conductor/unreplayable_records_report.json` for downstream tooling.
  - Companion test suite at `tests/test_categorize_unreplayable_records.py`.

## Phase 4: Closeout
- [x] Task: Run full tests and CI.
  - Created `tests/test_categorize_unreplayable_records.py` with 19 test cases
    covering classify_record, load_posted_record_ids, scan_normalized_x_archive,
    and build_report.
  - Tests pass with `uv run pytest tests/test_categorize_unreplayable_records.py -v`.
  - Review remediation tests pass with `python -m pytest -q
    tests/test_archive_replay_workflow.py tests/test_archive_mirror_coverage.py
    tests/test_categorize_unreplayable_records.py tests/test_archive_mirror_backlog.py
    tests/test_verify_archive_mirror_posts.py`.
- [x] Task: Update the parent Bluesky mirror track and archive/corpus tracks.
  - Updated `conductor/tracks.md` from in-progress to completed for this track.
