# Spec - Corpus Family Naming And Publication Alignment

## Status
done

## Goal

Adopt `corpus-nz-legislation` as the preferred systematic label for the legislation corpus and align GitHub, Hugging Face, Zenodo, OSF, and other public environments with the sibling `corpus-nz-hansard` project.

## Context

Sibling corpus project: `C:\Users\60217257\OneDrive - Flinders\repos\corpus-nz-hansard`.

Use this repository as the engineering baseline, but cross-reference Hansard for parliamentary interoperability and publication-surface lessons.

## Acceptance Criteria

- Preferred name `corpus-nz-legislation` is documented in Conductor product/setup/docs.
- Existing published names are not broken without a migration plan.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments each have explicit audit tasks.
- Requirements, design, Mermaid diagrams, and Conductor tracks cross-reference `corpus-nz-hansard`.
- Public metadata alignment includes repository description, topics, license/provenance, README, dataset card, CITATION, release notes, DOI links, and manifest references.
- Naming differences and migration risks are documented before any rename.

## Environment Requirements

- GitHub: assess whether to reserve or migrate to `corpus-nz-legislation`; keep current `corpus-legislation-nz` stable until redirects and release links are safe.
- Hugging Face: keep `edithatogo/corpus-legislation-nz`; verify dataset access, card metadata, files, Xet status, and viewer behaviour.
- Zenodo: keep DOI snapshots immutable; align related identifiers and license wording with HF/GitHub.
- OSF: optional only; define review-bundle/mirror policy before use.
- Other: prepare Croissant, RO-Crate, Frictionless, DCAT/PROV-O as generated metadata endpoints, not hand-edited releases.

## Out of Scope

- Immediate renaming of live repositories.
- Deleting or replacing published DOI records.
- Claiming complete legislation coverage.

## Evidence Recorded

- Preferred name `corpus-nz-legislation` is documented in
  `conductor/product.md`, `docs/corpus-family-requirements-moscow.md`,
  `docs/corpus-family-design.md`, and `docs/naming_publication_alignment.md`.
- Sibling `corpus-nz-hansard` is documented with local path and GitHub remote in
  `docs/naming_publication_alignment.md`.
- Current GitHub, Hugging Face, Zenodo, OSF, and future metadata surfaces are
  audited in `docs/public_surface_evidence_ledger.md`.
- README and dataset card now explain the preferred family label while
  preserving the current `corpus-legislation-nz` publication line.
- Migration/reservation of `corpus-nz-legislation` is deferred to Track 28.
