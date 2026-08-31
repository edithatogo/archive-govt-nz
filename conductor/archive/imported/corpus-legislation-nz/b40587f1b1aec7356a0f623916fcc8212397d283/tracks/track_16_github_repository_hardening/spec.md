# Spec - GitHub Repository Hardening

## Status
done

## Goal
make the GitHub repository safe to operate as the automation controller for the live Hugging Face corpus.

## Acceptance Criteria
- Default branch is protected.
- Tests are required for code changes.
- Secret scanning and dependency alerts are enabled or explicitly documented as unavailable.
- Repository remains code-only.

## Evidence to Record
- GitHub repository URL.
- Branch protection summary.
- Enabled security settings.
- First passing CI run URL.

## Evidence Recorded

- GitHub repository URL: `https://github.com/edithatogo/corpus-legislation-nz`.
- Branch protection on `main`: requires strict `tests`, one approving review,
  admin enforcement, linear history, no force pushes, and no deletions.
- Enabled security settings: Dependabot security updates, secret scanning, and
  push protection.
- First passing CI run: baseline `Tests` run `27087158077` and `CodeQL` run
  `27087158073` passed on 2026-06-07.


## Current Evidence
- GitHub repository URL: `https://github.com/edithatogo/corpus-legislation-nz`.
- Branch protection summary: `main` requires strict `tests`, one approving review, admin enforcement, linear history, no force pushes, and no deletions.
- Enabled security settings: Dependabot security updates, secret scanning, and push protection.
- First passing CI run: baseline `Tests` run `27087158077` and `CodeQL` run `27087158073` passed on 2026-06-07.
- Remaining blocker: Scorecard workflow fix must be merged through branch protection before the next Scorecard run can pass.
- Local hardening helper `scripts/configure_github_hardening.sh` now attempts repo defaults, Dependabot vulnerability alerts, secret scanning, push protection, Dependabot security updates, branch protection, and a required tests status check.
- Local repository remains code-only: generated corpus/archive/cache paths are ignored and no tracked files exist under `data/`, `dist/`, `archive/`, `.tmp/`, `.hf_cache/`, `.pytest-tmp/`, `test-tmp/`, or `.track15-smoke/`.
- Local public-repo support files and minimum workflow permissions were reviewed.
