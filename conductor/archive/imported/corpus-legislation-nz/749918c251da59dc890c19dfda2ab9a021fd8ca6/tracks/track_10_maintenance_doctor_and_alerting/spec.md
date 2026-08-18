# Spec - Maintenance Doctor And Alerting

## Status
done

## Goal
surface token, API, and dependency failures before they affect the live corpus.

## Acceptance Criteria
- Doctor workflow passes once with live secrets.
- Failure notification path is known.
- Maintainer has a weekly check routine.

## Evidence to Record
- Doctor workflow run URL.
- Notification destination.
- Any follow-up alerting issue.

## Evidence Recorded

- Local doctor workflow check on 2026-06-07:
  - `.github/workflows/doctor.yml`: present.
  - Schedule: `42 15 * * 0` weekly.
  - Manual dispatch is configured.
  - Permissions are read-only for contents.
  - The workflow runs `uv run nzlc doctor --network`.
  - The workflow passes `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, `HF_REPO_ID`, `ZENODO_TOKEN`, `ZENODO_API_URL`, and `ARCHIVE_CREATORS_JSON` from GitHub secrets/variables.
- Local non-network doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `NZ_LEGISLATION_API_KEY`: warning, not configured.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `ZENODO_TOKEN`: warning, not configured.
  - `ARCHIVE_CREATORS_JSON`: warning, not configured.
  - `output_dir`: `data`.
  - `data/` remained absent, so this local non-network check did not mutate corpus data.
- Maintenance and security configuration reviewed on 2026-06-07:
  - `.github/dependabot.yml`: weekly updates for GitHub Actions, uv, and pre-commit.
  - `.github/workflows/codeql.yml`: Python CodeQL on push, pull request, and weekly schedule.
  - `.github/workflows/scorecard.yml`: OpenSSF Scorecard on public repositories, schedule, branch protection rule, and manual dispatch.
  - `docs/maintenance_runbook.md`: weekly check routine includes doctor workflow, live sync summary, and Dependabot PRs.
- Doctor workflow passes with live secrets:
  - Run `27125139848` on 2026-06-08: success.
  - Run `27362180628` on 2026-06-11: success.
  - URL: `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27362180628`.
- Notification path:
  - GitHub Actions default workflow notifications: GitHub sends email notifications to repository watchers when a scheduled workflow run fails. No separate webhook or issue-creation step has been added yet, consistent with the deferral decision until a live failure pattern is observed.
  - `docs/maintenance_runbook.md` documents the weekly check routine: "Check the Non-destructive service doctor workflow" as the first weekly item.
  - Repository settings: issues enabled, default GitHub notification delivery active.
- Alerting decision:
  - Do not add webhook or issue creation yet. Use GitHub Actions default workflow notifications until the repository exists and the first live doctor failure mode is observed.
