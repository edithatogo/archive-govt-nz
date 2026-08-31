# Plan - GitHub Repository Hardening

## Tasks
- [x] Create or confirm the final GitHub repository.
- [x] Push the code-only repository without `data/`, `dist/`, cache directories, or generated corpus files.
- [x] Enable branch protection on the default branch.
- [x] Require the tests workflow before merge once CI is stable.
- [x] Enable secret scanning and push protection where available.
- [x] Enable Dependabot alerts and dependency update PRs.
- [x] Confirm `CODEOWNERS`, issue templates, pull request template, security policy, and contribution docs are present if the repo is public.
- [x] Confirm workflows have minimum permissions and do not expose secrets in logs.

## Implementation Notes
- Added branch protection, required status check, Dependabot vulnerability alert, secret scanning, push protection, and Dependabot security update API calls to `scripts/configure_github_hardening.sh`.
- GitHub repository created and baseline pushed: `https://github.com/edithatogo/corpus-legislation-nz`.
- Branch protection on `main` requires strict `tests`, one approving review, admin enforcement, linear history, no force pushes, and no deletions.
- Repository security settings show Dependabot security updates, secret scanning, and push protection enabled.
- Baseline `Tests` and `CodeQL` runs on `main` passed on 2026-06-07.
- OpenSSF Scorecard initially failed because webapp publishing rejects workflows with write permissions; `.github/workflows/scorecard.yml` now keeps SARIF upload and disables Scorecard webapp publishing.
- Confirmed `.gitignore` excludes generated corpus/archive/cache paths including `data/`, `dist/`, `.hf_cache/`, and `.track15-smoke/`.
- Confirmed no tracked files currently exist under generated corpus/archive paths.
- Confirmed support files exist: `SECURITY.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, `.github/pull_request_template.md`, issue templates, Dependabot config, CodeQL, Scorecard, tests, doctor, Hugging Face sync, and annual Zenodo workflows.
- Workflow secret references are passed through environment variables and are not echoed directly; summaries include generated state/manifests and archive checksums only.
