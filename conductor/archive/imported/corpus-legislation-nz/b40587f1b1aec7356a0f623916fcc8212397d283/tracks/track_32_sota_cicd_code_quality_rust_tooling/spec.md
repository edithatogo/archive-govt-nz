# Spec - SOTA CI/CD Code Quality And Rust Tooling

## Status
done

## Goal

Adopt SOTA CI/code-quality automation using Rust-backed tools where possible: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, plus `actionlint`.

## Current State

The repository already has a strict local `ty` baseline in `pyproject.toml`; the remaining track work is to make the complete quality/security automation explicit, reproducible, and CI-backed without weakening publication gates.

## Acceptance Criteria

- Aligns with `docs/bleeding-edge-versioning-ci-quality.md`.
- Preserves `corpus-nz-legislation` and `corpus-nz-hansard` naming.
- Uses Rust-backed tooling where practical: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and local `ripgrep` guidance.
- Documents the local commands and CI commands for `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and `actionlint`.
- Adds or verifies CodeQL, OpenSSF Scorecard, Renovate, and pre-commit policy as explicit adoption decisions.
- Keeps publication to Hugging Face and Zenodo behind validation gates.
- For Zenodo work, uses or formally evaluates `https://github.com/zenodraft/zenodraft`.

## Completion Evidence

- CI workflow:
  `.github/workflows/code_quality.yml`.
- Tooling policy:
  `docs/ci_code_quality_security_tooling.md`.
- Strict local commands now pass for `uv`, `ruff`, `ruff format --check`, `ty`,
  `typos`, `taplo`, and `actionlint`.
- `actionlint` identified and drove the fix for
  `.github/workflows/historical_hf_upload.yml`, which exceeded GitHub's
  `workflow_dispatch` input limit.
- CodeQL, OpenSSF Scorecard, Renovate, and pre-commit adoption decisions are
  documented.
- `zizmor` is adopted as advisory first because existing workflows still have
  unpinned-action and template-expansion findings that require a dedicated
  workflow-hardening pass before the gate can be blocking.
- Ruff expanded from 6 to 49 rule sets, all passing cleanly.
- `ty` strict type checking (`all = "error"`) passes for `src`, `tests`, and
  `scripts`.
- pydantic v2 with `pydantic-settings.BaseSettings` adopted for all
  environment-based configuration.
- Template injection risks fixed across all 8 CI workflows; `zizmor` now
  reports zero findings.
- All 16 workflows have explicit `permissions:` blocks with least-privilege
  scoping.
- `uv_build` build backend adopted for Python packaging.
