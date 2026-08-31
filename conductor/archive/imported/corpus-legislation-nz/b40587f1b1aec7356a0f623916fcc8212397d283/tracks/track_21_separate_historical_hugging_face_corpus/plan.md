# Plan - Separate Historical Hugging Face Corpus

## Phase 1 - Historical Target Policy

- [x] Task: Define separate historical target.
    - [x] Record `edithatogo/corpus-legislation-nz-historical` as the
      historical Hugging Face dataset.
    - [x] Record that the live `HF_REPO_ID` remains
      `edithatogo/corpus-legislation-nz`.
- [x] Task: Define guardrails.
    - [x] Require explicit historical target configuration.
    - [x] Prevent historical pilots/uploads from writing to `HF_REPO_ID` by
      default.
- [x] Task: Conductor - User Manual Verification 'Historical Target Policy' (Protocol in workflow.md)

## Phase 2 - Publication Setup

- [x] Task: Confirm or document historical dataset shell.
    - [x] Record root-layout expectations or creation runbook.
    - [x] Record variable names without exposing secret values.
- [x] Task: Update documentation.
    - [x] Document live-versus-historical dataset separation.
    - [x] Preserve conservative coverage wording.
- [x] Task: Conductor - User Manual Verification 'Publication Setup' (Protocol in workflow.md)

## Validation Evidence

- Historical Hugging Face target:
  `edithatogo/corpus-legislation-nz-historical`.
- Live Hugging Face target:
  `edithatogo/corpus-legislation-nz`.
- Configuration contract:
  `HF_HISTORICAL_REPO_ID=edithatogo/corpus-legislation-nz-historical`.
