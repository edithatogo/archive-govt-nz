# Plan - Hugging Face Dataset Shell

## Tasks
- [x] Create or confirm the Hugging Face dataset repository named by `HF_REPO_ID`.
- [x] Confirm the remote layout is root-based, not nested under `data/`.
- [x] Confirm dataset card metadata and root publication artifacts are present.
- [x] Remove or redirect legacy dataset naming where possible.

## Completion evidence

- Live dataset: `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Current verified revision:
  `6b082e2f85802cb374898d689d264017a047799b`.
- Repository variable:
  `HF_REPO_ID=edithatogo/corpus-legislation-nz`.
- Legacy DOI-bound dataset `edithatogo/nz-legislation-corpus` remains as a
  compatibility shell pointing to the renamed dataset.
