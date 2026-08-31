# Spec - Public Surface Audit Evidence

## Status
done

## Goal

Create an evidence ledger for GitHub, Hugging Face, Zenodo, OSF, and future metadata surfaces.

## Acceptance Criteria

- The work preserves the preferred corpus-family labels corpus-nz-legislation and corpus-nz-hansard.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments are considered where relevant.
- Evidence is recorded in the track and linked documentation.
- Existing published URLs and DOI records are not broken without a migration plan.

## Zenodo Requirement

Any Zenodo draft/archive workflow work in this track must use or formally evaluate zenodraft from https://github.com/zenodraft/zenodraft. Publication commands must remain separate from draft upload/update commands and require protected approval.

## Evidence Recorded

- Public-surface evidence ledger:
  `docs/public_surface_evidence_ledger.md`.
- GitHub public repository, release/tag, branch protection, repository
  variables, secret names, open issue/PR state, and recent workflow runs are
  recorded.
- Hugging Face live, historical, legacy DOI-bound, and historical redirect
  surfaces are recorded with current revisions.
- Zenodo published record, DOI, concept DOI, related identifier, files, and
  immutable filename caveat are recorded.
- OSF is recorded as inactive pending an explicit optional mirror/review policy.
- Future Croissant, RO-Crate, Frictionless, DCAT, and PROV-O surfaces are
  recorded as roadmap work, not active public outputs.
- A 2026-06-10 live refresh confirmed the recorded GitHub, Hugging Face, and
  Zenodo public-surface state remains current.
