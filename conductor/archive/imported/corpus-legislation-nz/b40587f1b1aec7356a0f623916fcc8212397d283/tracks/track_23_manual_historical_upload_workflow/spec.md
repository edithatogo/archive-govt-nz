# Spec - Manual Historical Upload Workflow

## Status

done

## Goal

add a manual-only historical Hugging Face upload workflow that
cannot overwrite the live partial/API-discovery dataset by default.

## Acceptance Criteria

- Historical upload workflow is separate from `hf_sync.yml`.
- Historical upload workflow has `workflow_dispatch` and no `schedule`.
- Historical upload workflow requires `HF_HISTORICAL_REPO_ID`.
- Historical upload workflow fails closed if `HF_HISTORICAL_REPO_ID` is absent.
- Historical upload workflow fails closed if `HF_HISTORICAL_REPO_ID` equals
  `HF_REPO_ID`.
- Historical upload workflow defaults to dry-run/no-upload behavior until an
  explicit manual upload input is provided after review.
- Historical upload workflow does not write to the live `HF_REPO_ID` dataset by
  default.

## Required Guard Checks

The workflow implementation should run these checks before any sync or upload
step:

```bash
if [ -z "${HF_HISTORICAL_REPO_ID:-}" ]; then
  echo "HF_HISTORICAL_REPO_ID is required for historical upload" >&2
  exit 1
fi

if [ "${HF_HISTORICAL_REPO_ID}" = "${HF_REPO_ID:-}" ]; then
  echo "HF_HISTORICAL_REPO_ID must be distinct from HF_REPO_ID" >&2
  exit 1
fi
```

The upload step should map the historical target into the existing CLI upload
interface only after those checks pass:

```bash
export HF_REPO_ID="${HF_HISTORICAL_REPO_ID}"
uv run nzlc hf-upload
```

## Evidence Recorded

- Documentation slice completed on 2026-06-09:
  - `docs/HUGGINGFACE_SETUP.md` documents the manual-only historical workflow
    contract, distinct target variable, dry-run/no-upload proof, and guarded
    fallback upload command.
  - `docs/historical_publication_policy.md` documents fail-closed historical
    publication guardrails.
  - `conductor/tracks.md` records the workflow implementation and remaining
    external proof URLs.
- `.github/workflows/historical_hf_upload.yml` implements the manual-only
  workflow, with no schedule and an upload step gated by
  `upload_confirmed=true`.
- Local validation completed with YAML parsing and `actionlint`.

## Dry-run Evidence

- Dry-run/no-upload Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27194196559`.
- Result: success.
- Upload behavior: upload step skipped because `upload_confirmed=false`; dry-run
  artifacts uploaded.

## Remaining External Evidence

- Reviewed historical upload run URL pending after historical target and batch
  plan approval.
