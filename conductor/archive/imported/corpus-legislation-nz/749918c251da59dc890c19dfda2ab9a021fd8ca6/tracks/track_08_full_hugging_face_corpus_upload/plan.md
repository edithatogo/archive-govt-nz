# Plan - Full Hugging Face Corpus Upload

## Tasks
- [x] Confirm upload helper defaults `HF_XET_HIGH_PERFORMANCE=1`.
- [ ] Run `uv run nzlc hf-upload` for the full validated corpus.
- [ ] Use resumable upload behavior if the upload is interrupted.
- [ ] Verify Hugging Face contains `parquet/`, `raw_xml`, `records.jsonl`,
  `manifests/`, and `_state/` as expected for the full corpus.
- [ ] Re-download the dataset into a clean location and compare manifest hashes.
- [ ] Confirm the dataset card states the discovery and coverage status
  accurately.

## Current blocker

- A live partial/API-discovery Hugging Face dataset exists, but no full
  validated corpus has been produced.
- Track 07 must complete first to produce the full local corpus and manifest.
- Full publication must not overwrite the partial/live scope with an
  unreviewed or unreconciled search-derived corpus.


## Implementation automation added 2026-06-12

- Added `.github/workflows/full_corpus_hf_upload.yml` as the full live upload workflow.
- The workflow defaults to `upload_confirmed=false` review mode and only calls `uv run nzlc hf-upload` when explicitly confirmed.
- The post-upload verification step downloads the remote manifest and compares it with the local manifest.
- See `docs/full_corpus_operations.md` for the operator inputs and review
  sequence for this workflow.
- Track is `ready` but still requires a real full-corpus artifact from Track 07 before confirmed publication.

## Publication guard hardened 2026-06-21

- `full_corpus_hf_upload.yml` now downloads a Track 07
  `full-corpus-bootstrap-download` artifact into the workspace root, preserving
  its `data/` layout instead of nesting it under `data/data/`.
- Confirmed full upload now fails closed unless `bootstrap_run_id` is supplied,
  preventing the current live partial/API-discovery dataset from being
  republished as the full-corpus upload path.
- The workflow runs `nzlc review-full-corpus-bootstrap --artifact-root data`
  after validation/manifest/coverage generation and before any confirmed
  Hugging Face upload.
- The upload review artifact now includes
  `generated/full-corpus-bootstrap/review_report.json`.
- Focused validation passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_full_corpus_hf_upload_workflow.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py -q`
  reported 23 passed.
- Lint and workflow validation passed:
  `.venv\Scripts\python.exe -m ruff check --no-cache tests\test_full_corpus_hf_upload_workflow.py tests\test_bootstrap_review.py src\nz_legislation_corpus\bootstrap_review.py src\nz_legislation_corpus\cli.py`
  and `actionlint .github\workflows\full_corpus_hf_upload.yml`.
- Remaining live tasks still depend on Track 07 run `27898963687` completing
  and producing a reviewed full-corpus artifact.

## Period-shard dependency added 2026-06-21

- Track 36 defines period-sharded review and agent handoff. Full Hugging Face
  publication must still use a reviewed full-corpus artifact, not isolated
  period artifacts, unless a future publication track explicitly defines
  period-level releases.
- Before confirmed full upload, verify that any Track 36 period review reports
  do not identify unresolved failed versions, missing-text blockers, or
  unknown-year shards that would undermine the dataset-card coverage wording.
