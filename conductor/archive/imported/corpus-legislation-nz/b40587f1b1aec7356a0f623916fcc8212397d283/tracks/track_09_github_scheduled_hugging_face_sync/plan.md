# Plan - GitHub Scheduled Hugging Face Sync

## Tasks
- [x] Confirm `.github/workflows/hf_sync.yml` exists on the default branch.
- [x] Configure GitHub secrets and variables from Track 02.
- [x] Run workflow manually with conservative inputs for the approved partial
  launch.
- [x] Confirm workflow uploads only changed content for the partial launch.
- [ ] Run workflow manually without `max_works` only after Track 07 and Track 08
  are proven.
- [ ] Confirm scheduled daily runs restore Hugging Face state before syncing.
- [ ] Confirm GitHub Actions summary includes sync state and latest changes over
  routine maintenance runs.

## Current blocker

- Manual live sync and no-change upload proof passed for the approved
  partial/API-discovery launch.
- The scheduled-run launch gate was explicitly waived by the repository owner on
  2026-06-09 after the first post-fix scheduled event did not dispatch.
- Full and recurring maintenance proof remains blocked until Tracks 04, 07, and
  08 establish a full seed and full validated corpus.


## Implementation automation added 2026-06-12

- `.github/workflows/hf_sync.yml` now verifies that the remote manifest matches the local manifest after upload.
- Full manual bootstrap and upload are now covered by `full_corpus_bootstrap.yml` and `full_corpus_hf_upload.yml`.
- See `docs/full_corpus_operations.md` for the operator sequence and review
  inputs that feed the bootstrap and upload workflows.
- Track is `ready` for routine scheduled maintenance, with full recurring proof still dependent on completed Tracks 07 and 08.

## Scheduled maintenance guard hardened 2026-06-21

- `hf_sync.yml` now fails closed if restore from the live Hugging Face dataset
  fails, preventing a scheduled maintenance run from uploading an empty or
  partial local state after a restore error.
- Routine runs upload `hf-sync-maintenance-evidence` with `sync_state.json`,
  `latest_changes.json`, `latest_manifest.json`, and `coverage_report.json` so
  scheduled-run evidence can be reviewed after the job completes.
- Focused validation passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_hf_sync_workflow.py -q`
  reported 2 passed.
- Lint and workflow validation passed:
  `.venv\Scripts\python.exe -m ruff check --no-cache tests\test_hf_sync_workflow.py`
  and `actionlint .github\workflows\hf_sync.yml`.
- Broader adjacent publication-gate validation passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_hf_sync_workflow.py tests\test_full_corpus_hf_upload_workflow.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py -q`
  reported 25 passed, with Ruff and `actionlint` also passing across the
  touched workflow surfaces.
- Remaining live proof still depends on scheduled/manual runs completing after
  Track 07 and Track 08 produce and publish the reviewed full corpus.

## Period-shard dependency added 2026-06-21

- Track 36 period shards are a bootstrap/review handoff mechanism, not a
  replacement for the live scheduled sync loop.
- After Track 36 is implemented, scheduled maintenance evidence should preserve
  enough year/period coverage context to identify whether a recent annual shard
  needs targeted rerun or review.
