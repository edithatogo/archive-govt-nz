# Plan - Shared NZ Corpus Core Schema

## Tasks

- [x] Confirm current public-surface state and existing local implementation.
- [x] Define the intended target state and migration constraints.
- [x] Update docs and validation scripts needed for this area.
- [x] Record GitHub/Hugging Face/Zenodo/OSF/future-metadata implications.
- [x] Confirm no Zenodo draft/archive workflow change is required for this schema-only track.
- [x] Record evidence and command outputs.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] Acceptance criteria are linked to release or maintenance docs.
- [x] Shared core schema check passes.
- [x] Shared core schema tests pass.

## Evidence

- Documentation: `docs/shared_nz_corpus_core_schema.md`.
- Schema: `schemas/shared_nz_corpus_core.schema.json`.
- Checker: `scripts/check_shared_core_schema.py`.
- Tests: `tests/test_shared_core_schema.py`.
