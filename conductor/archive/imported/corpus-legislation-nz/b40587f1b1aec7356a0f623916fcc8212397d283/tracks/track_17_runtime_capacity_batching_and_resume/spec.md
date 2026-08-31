# Spec - Runtime Capacity, Batching, And Resume

## Status
ready

## Goal
make the full corpus bootstrap and recurring sync practical under local disk, GitHub Actions runtime, API rate limits, and upload interruption constraints.

## Acceptance Criteria
- Bootstrap runner and disk budget are documented.
- Batch/resume procedure is written and tested with a non-trivial batch.
- Generated local data cleanup is documented and does not affect Git-tracked files.

## Evidence to Record
- Disk estimate.
- Chosen runner.
- Batch size and pacing values.
- Resume test result.

## Current Evidence
- Disk estimate documented in `docs/runtime_capacity_runbook.md`: reserve at least 25 GB free for the expected 6 GB class corpus, preferably 50 GB when archive staging or embeddings share the runner.
- Chosen runner documented: controlled local or self-hosted first bootstrap, then GitHub Actions for daily/latest maintenance after first verified upload.
- GitHub-hosted reviewed batch fan-out documented: `.github/workflows/historical_batch_review.yml` parallelizes reviewed batch validation while keeping confirmed uploads serial.
- Batch defaults documented: 5-work smoke at 1.0 seconds pacing, 50-work pilot at 1.0 seconds, 250-work seed chunks at 0.5 seconds, and 500-1000 work chunks at 0.2 seconds only after throttle-free earlier batches.
- Sync resume behavior verified: `tests/test_sync_resume.py` (2 tests) pass on 2026-06-11.
- Hugging Face upload resume: `nzlc hf-upload` uses `hf upload-large-folder` (resumable by design) with fallback to `HfApi.upload_folder` (idempotent). No-change manifest check prevents re-upload when manifest hashes match. Procedure documented in `docs/runtime_capacity_runbook.md`.
