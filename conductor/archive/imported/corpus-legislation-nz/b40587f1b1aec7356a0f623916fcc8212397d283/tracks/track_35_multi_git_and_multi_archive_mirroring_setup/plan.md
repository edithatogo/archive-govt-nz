# Plan - Multi-Git and Multi-Archive Mirroring

## Phase 1: Git Remote Mirror Setup

- [x] Task: Write `.github/workflows/mirror_sync.yml` to support automated SSH mirroring to secondary Git remotes (GitLab/Codeberg).
- [x] Task: Add fail-closed local guardrails so the workflow skips when mirror secrets are absent and rejects non-SSH mirror URLs.
- [x] Task: Support multiple newline-separated secondary Git remotes via `GIT_MIRROR_URLS`, with backward compatibility for `GIT_MIRROR_URL`.
- [x] Task: Add maintainer runbook for mirror secret setup and live workflow verification.
- [ ] Gated task: Configure repository secrets `GIT_MIRROR_URLS` and `GIT_MIRROR_SSH_PRIVATE_KEY` on GitHub.
- [ ] Gated task: Verify successful manual and push triggers for mirror sync.

## Phase 2: Multi-Archive Integration & OSF Policy

- [x] Task: Create `docs/osf-optional-mirror-policy.md` matching sister `corpus-nz-hansard` repository.
- [x] Task: Validate the OSF policy using a Python validator script.
- [x] Task: Conductor manual verification for Phase 2 confirms OSF remains policy-only and inactive pending future activation criteria.

## Local Evidence - 2026-06-14

- Chrome/browser-profile/account work: not approved for this lane, so no Chrome or browser-profile action was taken.
- Local mirror workflow review: `.github/workflows/mirror_sync.yml` now skips when `GIT_MIRROR_URL` or `GIT_MIRROR_SSH_PRIVATE_KEY` is absent and fails closed for non-SSH mirror URLs.
- OSF policy surface: `docs/osf-optional-mirror-policy.md` exists and keeps OSF inactive pending full bootstrap, full Hugging Face upload, OSF project creation, and a future Conductor implementation track.
- Validation commands passed:
  - `python scripts/check_osf_optional_policy.py`
  - `pytest -q tests/test_osf_optional.py`
  - `pytest -q -p no:cacheprovider tests/test_osf_optional.py`
  - `python -m ruff check scripts/check_osf_optional_policy.py tests/test_osf_optional.py src/nz_legislation_corpus/osf_optional.py`
  - `actionlint .github/workflows/mirror_sync.yml`
- `uv run ruff ...` was not usable in this Windows/OneDrive sandbox because uv cache initialization failed with access denied; direct `python -m ruff` passed.

## Local Evidence - 2026-06-21

- Mirror workflow now accepts `GIT_MIRROR_URLS` for multiple newline-separated
  SSH mirror remotes, while retaining `GIT_MIRROR_URL` for existing single
  mirror secret setups.
- Mirror workflow still skips when mirror URL(s) or SSH key secrets are absent
  and fails closed for any non-SSH mirror URL.
- Review fix: mirror workflow now runs under `set -euo pipefail` and iterates
  mirror URLs without a pipeline-fed loop, so any failed `ssh-keyscan`,
  `git remote add`, or `git push` fails the workflow instead of being masked by
  a later mirror.
- OSF policy validation command now points to the repository's actual validator:
  `python scripts/check_osf_optional_policy.py`.
- Validation commands passed:
  - `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_mirror_sync_workflow.py tests\test_osf_optional.py -q`
  - `.venv\Scripts\python.exe scripts\check_osf_optional_policy.py`
  - `.venv\Scripts\python.exe -m ruff check --no-cache tests\test_mirror_sync_workflow.py tests\test_osf_optional.py scripts\check_osf_optional_policy.py src\nz_legislation_corpus\osf_optional.py`
  - `actionlint .github\workflows\mirror_sync.yml`
- External gates remain open until GitHub repository secrets are configured and
  a live manual/push mirror run is verified.

## Live Evidence - 2026-06-21

- GitHub secret-name check passed without exposing values:
  `gh secret list --repo edithatogo/corpus-legislation-nz`.
- Existing secrets include `OSF_TOKEN`, confirming OSF credential storage exists
  for future activation, but OSF remains inactive under
  `docs/osf-optional-mirror-policy.md` until the activation criteria are met.
- Mirror secrets are not configured yet: no `GIT_MIRROR_URLS`,
  `GIT_MIRROR_URL`, or `GIT_MIRROR_SSH_PRIVATE_KEY` appeared in the GitHub
  secret-name list, and matching local environment variables were absent.
- GitHub workflow-name check passed:
  `gh workflow list --repo edithatogo/corpus-legislation-nz`.
- `Mirror Sync` is not visible on the default branch yet, so live manual/push
  mirror verification cannot run until `.github/workflows/mirror_sync.yml` is
  pushed to GitHub.
- Maintainer setup and verification commands are documented in
  `docs/mirror-sync-setup.md`.
- Validation commands passed:
  - `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_mirror_sync_workflow.py tests\test_osf_optional.py -q`
  - `.venv\Scripts\python.exe scripts\check_osf_optional_policy.py`
  - `.venv\Scripts\python.exe -m ruff check --no-cache tests\test_mirror_sync_workflow.py tests\test_osf_optional.py scripts\check_osf_optional_policy.py src\nz_legislation_corpus\osf_optional.py`
  - `actionlint .github\workflows\mirror_sync.yml`

## Live Evidence - 2026-07-02

- `Mirror Sync` is now visible and active on the default branch.
- GitHub secret-name check still shows no `GIT_MIRROR_URLS`,
  `GIT_MIRROR_URL`, or `GIT_MIRROR_SSH_PRIVATE_KEY`; only unrelated publication
  secrets such as `HF_TOKEN`, `NZ_LEGISLATION_API_KEY`, `OSF_TOKEN`, and Zenodo
  tokens are configured.
- Manual run `28581284768` completed successfully on `main` and exercised the
  intended no-secret guard path. The job log reported:
  `GIT_MIRROR_URLS/GIT_MIRROR_URL is not set, skipping mirror.`
- Track 35 is therefore implementation-complete through workflow publication
  and guarded manual-run proof, but remains blocked on external mirror remote
  and SSH-key secret configuration before a real mirror push can be verified.
