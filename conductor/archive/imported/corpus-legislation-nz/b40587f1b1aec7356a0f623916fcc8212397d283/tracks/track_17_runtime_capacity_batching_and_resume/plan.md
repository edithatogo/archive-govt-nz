# Plan - Runtime Capacity, Batching, And Resume

## Tasks
- [x] Estimate disk required for raw files, normalized records, Parquet, manifests, and annual archive staging.
- [x] Decide whether first full bootstrap runs locally, on GitHub Actions, or on another controlled runner.
- [x] Define batch size and pacing defaults for first full sync.
- [x] Confirm sync state is preserved between batches.
- [x] Confirm interrupted Hugging Face uploads can resume without corrupting the remote dataset. `hf upload-large-folder` is resumable by design; no-change manifest check prevents redundant uploads; sync resume is tested.
- [x] Add an operator note for cleaning local generated data safely after upload and verification.
- [x] Record the fallback plan if the full bootstrap exceeds GitHub Actions timeout.
- [x] Document GitHub-hosted reviewed batch fan-out for no-upload validation while keeping confirmed uploads serial.

## Implementation Notes
- Added `docs/runtime_capacity_runbook.md` with disk budget, runner decision, batch defaults, resume behavior, Hugging Face upload rerun guidance, cleanup rules, and GitHub Actions timeout fallback.
- Added `.github/workflows/historical_batch_review.yml` and `docs/historical_batch_parallelization.md` for GitHub-hosted reviewed batch fan-out.
- Linked the runtime capacity runbook from `README.md` and `docs/maintenance_runbook.md`.
- Added `tests/test_sync_resume.py` to prove staged sync runs preserve and extend `data/_state/sync_state.json` without external credentials.
- First full bootstrap runner decision: controlled local or self-hosted runner for the initial complete corpus; GitHub Actions remains the daily/latest maintenance loop after the first verified upload.
- Conservative disk budget: reserve at least 25 GB free for the expected 6 GB class corpus; prefer 50 GB if archive staging or embeddings run on the same host. Final measured disk usage remains blocked until Track 07 produces the full corpus.

## Period-shard dependency added 2026-06-21

- Track 36 owns the next layer above runtime batching: canonical time-period
  shards, recent annual shards, per-period checkpoint artifacts, and agent
  handoff status.
- Track 17 remains the lower-level capacity/resume foundation. Do not treat the
  existing 500-work operational batches as final period handoff units.
