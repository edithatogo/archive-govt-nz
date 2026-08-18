# Spec - Zenodo Rights Metadata And Zenodraft Workflow

## Status
done

## Goal

Harmonise Zenodo rights metadata and migrate/evaluate draft operations through zenodraft.

## Acceptance Criteria

- The work preserves the preferred corpus-family labels corpus-nz-legislation and corpus-nz-hansard.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments are considered where relevant.
- Evidence is recorded in the track and linked documentation.
- Existing published URLs and DOI records are not broken without a migration plan.

## Zenodo Requirement

Any Zenodo draft/archive workflow work in this track must use or formally evaluate zenodraft from https://github.com/zenodraft/zenodraft. Publication commands must remain separate from draft upload/update commands and require protected approval.

## Evidence Recorded

- `docs/zenodo_rights_metadata_zenodraft.md` records the rights-scope decision,
  current Zenodo DOI state, zenodraft evaluation, token mapping, sandbox proof
  target, and protected publication gate.
- `docs/zenodo/zenodo-2026-metadata.example.json` is a validated Zenodo-format
  metadata example carrying the source-rights caveat.
- `NOTICE.md`, `README.md`, `DATASET_CARD.md`, and `CITATION.cff` now expose or
  link the rights-scope boundary.
- `.github/workflows/annual_zenodo_archive.yml` keeps production publication
  separate from draft upload/update and links the rights/zenodraft policy in
  workflow summaries.
- Full sandbox draft creation/upload/update remains a future migration proof
  before replacing the Python uploader.
