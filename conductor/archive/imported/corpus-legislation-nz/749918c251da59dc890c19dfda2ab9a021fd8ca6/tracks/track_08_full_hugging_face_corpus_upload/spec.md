# Spec - Full Hugging Face Corpus Upload

## Status
ready

## Goal
publish the full validated corpus to Hugging Face as the live operational dataset.

## Acceptance Criteria
- Full corpus upload completes.
- Re-downloaded manifest matches the uploaded manifest.
- Dataset card and README do not overclaim completeness.

## Evidence to Record
- Hugging Face revision or commit hash.
- Uploaded size.
- Manifest hash.
- Re-download verification result.

## Evidence Recorded

- 2026-06-21 repo-side publication guard:
  - `.github/workflows/full_corpus_hf_upload.yml` downloads the Track 07
    `full-corpus-bootstrap-download` artifact into the workspace root when
    `bootstrap_run_id` is supplied, preserving the artifact's `data/` tree.
  - Confirmed full upload fails closed when `bootstrap_run_id` is empty.
  - The workflow runs `nzlc review-full-corpus-bootstrap --artifact-root data`
    before `uv run nzlc hf-upload`; a failed Track 07 review blocks confirmed
    publication.
  - The pre-publish review artifact includes
    `generated/full-corpus-bootstrap/review_report.json`.
- Local environment presence check on 2026-06-07:
  - `HF_TOKEN`: absent.
  - `HF_REPO_ID`: absent.
  - `HF_XET_HIGH_PERFORMANCE`: absent.
  - `NZ_LEGISLATION_API_KEY`: absent.
  - `NZLC_OUTPUT_DIR`: absent.
- Local data check on 2026-06-07:
  - `data/`: absent.
  - `data/manifests/latest_manifest.json`: absent.
  - `data/parquet/`: absent.
- Local doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `output_dir`: `data`.
- Upload code path:
  - `uv run nzlc hf-upload` requires `HF_REPO_ID` and `HF_TOKEN`.
  - `upload_large_folder` sets `HF_XET_HIGH_PERFORMANCE=1` by default for the subprocess environment when it is not already set.
  - No full upload was attempted because credentials and full corpus data are absent.

## Blocked Items

- Cannot run `uv run nzlc hf-upload` until the full validated corpus exists under `data/` and `HF_TOKEN`/`HF_REPO_ID` are configured.
- Cannot verify remote root layout, re-download, compare manifest hashes, or inspect uploaded size until upload completes.
- Cannot confirm dataset card/readme against the live Hugging Face state until the target dataset repository exists and is reachable.
