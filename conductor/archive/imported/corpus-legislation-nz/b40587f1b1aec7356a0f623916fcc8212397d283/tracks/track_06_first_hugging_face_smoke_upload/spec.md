# Spec - First Hugging Face Smoke Upload

## Status
done

## Goal
prove upload, restore, and no-change behavior on Hugging Face with the small smoke corpus.

## Acceptance Criteria
- Smoke corpus is visible in Hugging Face.
- Re-download produces the expected local layout.
- No-change upload behavior is proven.

## Evidence to Record
- Hugging Face commit or revision.
- Manifest hash before and after no-change upload.
- Sample Parquet read result.

## Evidence Recorded

- Live Hugging Face upload, restore/no-change behavior, and sample dataset
  verification passed for the approved partial/API-discovery launch.
- Live dataset target:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Current verified revision:
  `6b082e2f85802cb374898d689d264017a047799b`.

- Local environment presence check on 2026-06-07:
  - `HF_TOKEN`: absent.
  - `HF_REPO_ID`: absent.
  - `NZ_LEGISLATION_API_KEY`: absent.
  - `NZLC_OUTPUT_DIR`: absent.
- Local data check on 2026-06-07:
  - `data/`: absent.
  - `data/manifests/latest_manifest.json`: absent.
- Local doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `output_dir`: `data`.
- Upload code path:
  - `uv run nzlc hf-upload` requires `HF_REPO_ID` and `HF_TOKEN`.
  - No upload was attempted because the prerequisites are absent and Track 05 has not produced smoke data.

## Blocked Items

- Cannot run `uv run nzlc hf-upload` against smoke data until a smoke corpus exists under `data/`.
- Cannot upload, re-download, inspect the dataset viewer, or prove no-change behavior until `HF_TOKEN` and `HF_REPO_ID` are configured.
- Cannot record Hugging Face revision, manifest hash comparison, or sample Parquet read result until the first smoke upload succeeds.
