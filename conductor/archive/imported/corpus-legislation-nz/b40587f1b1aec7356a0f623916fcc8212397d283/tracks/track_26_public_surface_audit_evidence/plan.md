# Plan - Public Surface Audit Evidence

## Tasks

- [x] Confirm current public-surface state and existing local implementation.
- [x] Define the intended target state and migration constraints.
- [x] Update docs needed for this area.
- [x] Record GitHub/Hugging Face/Zenodo/OSF/future-metadata implications.
- [x] Record Zenodo evidence without changing draft/archive workflow
  implementation.
- [x] Record evidence and command outputs.

## Evidence

- Ledger: `docs/public_surface_evidence_ledger.md`.
- Live refresh performed on 2026-06-10 confirmed no drift requiring a policy or
  documentation change.
- GitHub evidence includes repo URL, release/tag, branch protection, variables,
  secret names, topics/homepage state, open issue/PR state, and recent workflow
  runs.
- Hugging Face evidence includes live, historical, old DOI-bound, and historical
  redirect dataset surfaces.
- Zenodo evidence includes record `20592540`, DOI, concept DOI, related
  identifier, license, file list, and immutable filename caveat.
- OSF is inactive and future metadata packages remain roadmap work.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] Acceptance criteria are linked to release or maintenance docs through the
  ledger, public launch decision, implementation status, and prioritized
  recommendations.
