# Plan - Corpus Family Naming And Publication Alignment

## Phase 1 - Naming and sibling setup

- [x] Record `corpus-nz-legislation` as the preferred systematic project label
  in Conductor product/setup docs.
- [x] Cross-reference `corpus-nz-hansard` and its local path.
- [x] Update requirements and design docs with naming decision and Mermaid
  diagrams.
- [x] Document current published names and migration risks.

## Phase 2 - GitHub environment

- [x] Audit current GitHub repo metadata, topics, homepage, release tags,
  branch/ruleset posture, Actions, CodeQL, Scorecard, license, and SECURITY
  files through `docs/public_surface_evidence_ledger.md`.
- [x] Defer reservation or migration of `corpus-nz-legislation` to Track 28.
- [x] Add explicit cross-links to `corpus-nz-hansard` in
  `docs/naming_publication_alignment.md`.
- [x] Preserve partial/API-discovery caveats in README and release docs.

## Phase 3 - Hugging Face environment

- [x] Audit `edithatogo/corpus-legislation-nz` card metadata, access/gating,
  files, Xet status, and DOI/legacy constraints through
  `docs/public_surface_evidence_ledger.md`.
- [x] Keep `edithatogo/corpus-legislation-nz` as the live dataset surface.
- [x] Keep `edithatogo/corpus-legislation-nz-historical` separate from the live
  dataset.
- [x] Record HF revisions and current publication constraints in the evidence
  ledger.

## Phase 4 - Zenodo environment

- [x] Audit Zenodo DOI record metadata, creators, license, files, related
  identifiers, concept DOI, and links through
  `docs/public_surface_evidence_ledger.md`.
- [x] Record the immutable old-prefix file-name caveat.
- [x] Keep production publish draft-first and reviewer-approved for future
  snapshots.

## Phase 5 - OSF and other environments

- [x] Record OSF as inactive pending optional mirror/review policy.
- [x] Record Croissant, RO-Crate, Frictionless, DCAT, and PROV-O as future
  generated metadata surfaces.

## Verification

- [x] Requirements/design docs include the naming preference and environment
  matrix.
- [x] Mermaid diagrams are present in `docs/corpus-family-design.md`.
- [x] `conductor/tracks.md` registers this track.
- [x] Environment tasks are present and cross-reference Hansard.
- [x] Public README and dataset card preserve existing published URLs and
  coverage caveats.
