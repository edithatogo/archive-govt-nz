# Repository access, CI credentials and dual-remote setup

This repository is pushed to **two** remotes so that a single `git push` keeps both
copies current:

| Remote | URL | Purpose |
|-------|-----|---------|
| GitHub | `https://github.com/edithatogo/archive-govt-nz.git` | Primary public mirror; GitHub Actions workflows in `.github/workflows/` |
| GitLab | `https://gitlab.com/edithatogo/archive-govt-nz.git` | CI runner pool (`.gitlab-ci.yml`), no minutes quota on public projects |

`origin` has two push URLs configured, so `git push origin main` updates both:

```bash
git remote set-url --add --push origin https://github.com/edithatogo/archive-govt-nz.git
git remote set-url --add --push origin https://gitlab.com/edithatogo/archive-govt-nz.git
git remote get-url --all --push origin   # verify
```

## What credentials are needed

### GitLab

A **personal access token** with the scopes:

- `write_repository` — required to `git push`
- `api` — required by `glab` for pipelines/variables/runners (optional for push only)

Created at <https://gitlab.com/-/user_settings/personal_access_tokens> and stored once:

```bash
glab auth login --hostname gitlab.com          # paste the token
git config --global credential.https://gitlab.com.helper '!glab auth git-credential'
```

The helper entry is what makes `git push` reuse the `glab` token instead of falling
back to the macOS keychain, which holds no `gitlab.com` password. Without it a push
fails with `HTTP Basic: Access denied`.

### GitHub

A token with `repo` (classic) or `Contents: read/write` (fine-grained) scope. The
recommended setup is the `gh` CLI, which stores the token in the keyring:

```bash
gh auth login --hostname github.com
gh auth setup-git          # configures credential.https://github.com.helper
```

### Hugging Face (publish target)

Both CI systems need the same secret, already configured:

| System | Where | Name |
|--------|-------|------|
| GitLab | Settings → CI/CD → Variables | `HF_TOKEN` (protected + masked) |
| GitHub | Settings → Secrets and variables → Actions | `HF_TOKEN` |

Locally the token is in the macOS keychain:

```bash
security find-internet-password -s huggingface.co -w
```

## CI execution prerequisites

`git push` permissions and *running CI jobs* are separate concerns:

- **GitLab** additionally requires **identity verification** on the account. Without
  it, pipelines are created but fail immediately with zero jobs and the API returns
  `Identity verification is required in order to run CI jobs`. Verify at
  <https://gitlab.com/-/user_settings/identity_verification>. Shared runners are
  otherwise enabled and online (`project.shared_runners_enabled == true`).
- **GitHub** Actions consume a monthly minutes quota. When exhausted, runs sit in
  `queued` indefinitely. Check <https://github.com/settings/billing>; a public repo
  still bills macOS/Windows minutes, and Linux minutes are only free for public repos.

Either platform alone is sufficient to run the harvest; the other acts as a fallback.

## Verifying the setup

```bash
git ls-remote origin main     # GitHub reachable and authenticated
git ls-remote gitlab main     # GitLab reachable and authenticated
gh auth status                # GitHub token
glab auth status              # GitLab token
glab variable list -R edithatogo/archive-govt-nz   # HF_TOKEN present
gh secret list -R edithatogo/archive-govt-nz       # HF_TOKEN present
```
