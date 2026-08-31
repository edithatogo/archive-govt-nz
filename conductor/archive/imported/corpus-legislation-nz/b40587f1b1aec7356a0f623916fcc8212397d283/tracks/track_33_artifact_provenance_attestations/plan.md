# Plan - Artifact Provenance And Attestations

## Tasks

- [x] Define current state and target state in `docs/artifact_provenance_attestations.md`.
- [x] Define the release evidence ledger schema and required fields in `schemas/release_evidence.schema.json`.
- [x] Map artifact classes to provenance strategy: GitHub artifact attestation, SLSA-style provenance, signed checksum, or documented deferral.
- [x] Add/update CI checks with least-privilege permissions.
- [x] Add/update local commands or Makefile targets.
- [x] Add documentation consistency and release evidence checks.
- [x] Add Renovate/package update policy where applicable through the existing dependency/publication boundary.
- [x] Ensure dependency-update PRs cannot publish datasets or Zenodo records.
- [x] Record validation evidence below.

## Tooling Checklist

- [x] `uv` frozen install/lock checks.
- [x] `ruff check` and `ruff format --check`.
- [x] `ty check` with strict rules for packaged modules.
- [x] `typos` spelling/identifier check.
- [x] `zizmor` workflow security audit remains advisory under Track 32 until workflow-hardening backlog is complete.
- [x] `taplo` TOML formatting/linting where TOML config exists.
- [x] `actionlint` workflow syntax check.
- [x] CodeQL and OpenSSF Scorecard.
- [x] Artifact attestations or SLSA-style provenance for release artifacts.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] All added checks are documented before enforcement.

## Validation Evidence

- `uv run python scripts\check_artifact_provenance.py` passed.
- `uv run pytest -q tests\test_artifact_provenance.py` passed.
- `uv run ruff check src\nz_legislation_corpus\artifact_provenance.py src\nz_legislation_corpus\archive.py src\nz_legislation_corpus\cli.py scripts\check_artifact_provenance.py tests\test_artifact_provenance.py` passed.
- `uv run ty check src tests scripts` passed through `cmd` after a local PowerShell profile/CLR crash.
