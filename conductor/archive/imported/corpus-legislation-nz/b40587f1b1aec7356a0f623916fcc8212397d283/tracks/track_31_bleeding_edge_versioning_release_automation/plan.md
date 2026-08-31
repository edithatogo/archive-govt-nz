# Plan - Bleeding Edge Versioning And Release Automation

## Tasks

- [x] Define current state and target state in `docs/versioning_release_automation.md`.
- [x] Define the authoritative version sources for code/package, dataset, schema, Hugging Face revision, Zenodo DOI snapshot, and manifest hash.
- [x] Add consistency checks across `pyproject.toml`, release notes, `CITATION.cff`, dataset card text, manifests, and publication metadata.
- [x] Decide whether to use Release Please or an equivalent Conventional Commits release-note/tag workflow: deferred until publication gates and protected environments are fully proven.
- [x] Add/update CI checks with least-privilege permissions through the read-only `Tests` workflow.
- [x] Add/update local commands: `uv run python scripts/check_version_consistency.py`.
- [x] Add documentation consistency and release evidence checks in `scripts/check_version_consistency.py`.
- [x] Add Renovate/package update policy where applicable in `docs/dependency_updates.md`.
- [x] Ensure dependency-update PRs cannot publish datasets or Zenodo records.
- [x] Record validation evidence below.

## Tooling Checklist

- [x] `uv` frozen install/lock checks remain in `.github/workflows/tests.yml`.
- [x] `ruff check` used for the new script and tests.
- [ ] `ruff format --check`, `ty`, `typos`, `zizmor`, `taplo`, and `actionlint` are documented as Track 32 scope.
- [ ] CodeQL and OpenSSF Scorecard are documented as Track 32 scope.
- [ ] Artifact attestations or SLSA-style provenance for release artifacts are Track 33 scope.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] All added checks are documented before enforcement.

## Validation Evidence

- `uv run python scripts\check_version_consistency.py` passed.
- `uv run pytest -q tests\test_version_consistency.py` passed.
- `uv run ruff check scripts\check_version_consistency.py tests\test_version_consistency.py` passed after the E402 import exception was documented.
