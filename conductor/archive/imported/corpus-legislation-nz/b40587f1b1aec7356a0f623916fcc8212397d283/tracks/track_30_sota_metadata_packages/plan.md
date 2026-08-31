# Plan - SOTA Metadata Packages

## Tasks

- [x] Confirm current public-surface state and existing local implementation.
- [x] Define the intended target state and migration constraints.
- [x] Update docs and validation scripts needed for this area.
- [x] Record GitHub/Hugging Face/Zenodo/OSF/future-metadata implications.
- [x] Confirm no Zenodo draft/archive workflow change is required for this generator-only track.
- [x] Record evidence and command outputs.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] Acceptance criteria are linked to release or maintenance docs.
- [x] Metadata package generator tests pass.
- [x] Metadata package CLI generation and validation pass.

## Evidence

- Documentation: `docs/sota_metadata_packages.md`.
- Generator: `src/nz_legislation_corpus/metadata_packages.py`.
- Tests: `tests/test_metadata_packages.py`.
- Generated output location: `generated/metadata-packages` (ignored by Git).
