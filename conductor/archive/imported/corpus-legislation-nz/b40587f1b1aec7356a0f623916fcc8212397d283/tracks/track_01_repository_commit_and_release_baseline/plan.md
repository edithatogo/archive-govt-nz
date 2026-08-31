# Plan - Repository Commit And Release Baseline

## Tasks
- [x] Resolve the parent `OneDrive - Flinders` Git root lock issue or move `corpus-law-nz` into an isolated Git repository.
- [x] Commit the currently staged rate-limit hardening, bootstrap guardrails, tests, and documentation.
- [x] Generate a clean `uv.lock` from the final repository root.
- [x] Switch CI dependency installation to `uv sync --all-extras --frozen` after `uv.lock` exists.
- [x] Run `pytest -q -p no:cacheprovider tests`.
- [x] Run `ruff check src/nz_legislation_corpus tests`.
