# Plan - SOTA CI/CD Code Quality And Rust Tooling

## Tasks

- [x] Define current state and target state in `docs/ci_code_quality_security_tooling.md`.
- [x] Record the existing strict `ty` baseline and the exact local validation commands that must stay green.
- [x] Add/update CI checks with least-privilege permissions in `.github/workflows/code_quality.yml`.
- [x] Add/update local commands in `docs/ci_code_quality_security_tooling.md` and `.github/pull_request_template.md`.
- [x] Add documentation consistency and release evidence checks via `scripts/check_version_consistency.py`.
- [x] Add Renovate/package update policy where applicable through Track 31 and this tooling policy.
- [x] Decide and document pre-commit adoption scope.
- [x] Ensure dependency-update PRs cannot publish datasets or Zenodo records.
- [x] Record validation evidence below.

## Tooling Checklist

- [x] `uv` frozen install/lock checks.
- [x] `ruff check` and `ruff format --check`.
- [x] `ty check` with strict rules for packaged modules.
- [x] `typos` spelling/identifier check.
- [x] `zizmor` workflow security audit adopted as advisory with backlog recorded.
- [x] `taplo` TOML formatting/linting where TOML config exists.
- [x] `actionlint` workflow syntax check.
- [x] CodeQL and OpenSSF Scorecard adoption verified.
- [ ] Artifact attestations or SLSA-style provenance for release artifacts remain Track 33 scope.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] All added checks are documented before enforcement.

## Validation Evidence

- `uv run ruff check .` passed (49 rule sets enabled).
- `uv run ruff format --check .` passed after applying repository formatting.
- `uv run ty check src tests scripts` passed (strict `all = "error"` rules).
- `uv run pytest -q tests` passed (120+ tests across unit, integration, smoke, hypothesis).
- `uv run python scripts\check_version_consistency.py` passed.
- `typos` passed.
- `taplo fmt --check pyproject.toml` passed after formatting `pyproject.toml`.
- `actionlint` passed after consolidating historical-upload workflow inputs.
- Workflow YAML parse passed for `.github/workflows/*.yml`.
- `zizmor --no-online-audits .github\workflows` now reports **zero findings** after template injection fixes and explicit permissions blocks were added to all 16 workflows.
- pydantic v2 with `pydantic-settings.BaseSettings` adopted for configuration (replaces raw `@dataclass` + `os.getenv()` patterns).
- `uv_build` build backend adopted for Python packaging.
