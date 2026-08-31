# Plan - GitHub Repository Name Migration Assessment

## Tasks

- [x] Confirm current public-surface state and existing local implementation.
- [x] Define the intended target state and migration constraints.
- [x] Update docs needed for this area.
- [x] Record GitHub/Hugging Face/Zenodo/OSF/future-metadata implications.
- [x] Confirm no Zenodo draft/archive workflow change is required for this track.
- [x] Record evidence and command outputs.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] Acceptance criteria are linked to release or maintenance docs.

## Evidence

- Assessment: `docs/github_repository_name_migration_assessment.md`.
- `gh repo view edithatogo/corpus-legislation-nz` confirmed the live public
  repository, default branch, and latest release.
- `gh repo view edithatogo/corpus-nz-legislation` returned not found or not
  accessible at the Track 28 check point.
- Local `origin` remains
  `https://github.com/edithatogo/corpus-legislation-nz.git`.
- Decision: reserve-first; no live repository rename in this track.
