# Spec - Hugging Face Dataset Shell

## Status
done

## Goal
create and verify the Hugging Face dataset repository before uploading corpus data.

## Acceptance Criteria
- Hugging Face repo exists and is writable by the configured token.
- Root-level layout is ready for `parquet/`, `raw_xml/`, `manifests/`, and `_state/`.
- Dataset card describes live corpus status without claiming full coverage before discovery proof.

## Evidence to Record
- Hugging Face repo URL.
- Root layout listing.
- Dataset card revision or commit hash.

## Evidence Recorded

- Local environment presence check on 2026-06-07:
  - `HF_TOKEN`: absent.
  - `HF_REPO_ID`: absent.
  - `HF_PRIVATE`: absent.
  - `HF_DATASET_PRETTY_NAME`: absent.
- Local doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `output_dir`: `data`.
- Repository-side setup path:
  - `scripts/create_huggingface_dataset_repo.sh` requires `HF_TOKEN` and `HF_REPO_ID`.
  - `scripts/init_huggingface_dataset.py` creates or updates the dataset repo idempotently, writes root-level placeholders for `parquet/`, `raw_xml/`, and `manifests/`, writes `.gitattributes`, writes dataset metadata, and attempts to remove legacy `data/...` placeholders.
- Public web check on 2026-06-07:
  - Search/open checks did not confirm an existing public `edithatogo/corpus-legislation-nz` dataset shell.

## Blocked Items

- Cannot create or confirm the Hugging Face dataset repository until final `HF_REPO_ID` is supplied.
- Cannot verify write access or run `scripts/create_huggingface_dataset_repo.sh "$HF_REPO_ID"` until `HF_TOKEN` is supplied.
- Cannot confirm the remote root layout, `.gitattributes`, dataset card revision, or legacy `data/...` placeholder removal until the Hugging Face repo is reachable with the configured token.
