# Spec - GitHub Scheduled Hugging Face Sync

## Status
ready

## Goal
make GitHub Actions the normal maintenance loop for the Hugging Face live corpus.

## Acceptance Criteria
- Manual smoke workflow passes.
- Full manual workflow passes.
- Daily scheduled workflow is enabled and uses the Hugging Face repo as the live data hub.

## Evidence to Record
- GitHub Actions run URLs.
- Workflow inputs used.
- Latest successful scheduled run URL.

## Evidence Recorded

- `.github/workflows/hf_sync.yml` exists on the default branch.
- GitHub secrets and variables required for live sync exist.
- 2026-06-21 repo-side scheduled maintenance guard:
  - Restore from the live Hugging Face dataset now fails closed instead of
    continuing after restore errors.
  - Routine runs upload `hf-sync-maintenance-evidence` containing sync state,
    latest changes, latest manifest, and coverage report artifacts for review.
- Manual live sync and no-change upload proof passed for the approved
  partial/API-discovery launch.
- The scheduled-run launch gate was explicitly waived by the repository owner on
  2026-06-09 after the first post-fix scheduled event did not dispatch.

## Blocked Items

- Full manual workflow proof remains blocked until Tracks 04, 07, and 08 produce
  a full seed, full validated corpus, and full Hugging Face upload.
- Routine scheduled-run evidence still needs to be accumulated after launch.
