# Spec - SOTA Metadata Packages

## Status
done

## Goal

Generate validated Croissant, RO-Crate, Frictionless, DCAT, and PROV-O metadata packages.

## Acceptance Criteria

- The work preserves the preferred corpus-family labels corpus-nz-legislation and corpus-nz-hansard.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments are considered where relevant.
- Croissant, RO-Crate, Frictionless, DCAT, and PROV-O outputs are generated from canonical manifests or metadata inputs rather than hand-edited as release artifacts.
- Each generated metadata package has validation commands, checksums, source-manifest references, and publication-surface links.
- Evidence is recorded in the track and linked documentation.
- Existing published URLs and DOI records are not broken without a migration plan.

## Zenodo Requirement

Any Zenodo draft/archive workflow work in this track must use or formally evaluate zenodraft from https://github.com/zenodraft/zenodraft. Publication commands must remain separate from draft upload/update commands and require protected approval.

## Evidence Recorded

- `docs/sota_metadata_packages.md` records the generated metadata package
  contract, validation commands, publication-surface implications, and release
  usage.
- `src/nz_legislation_corpus/metadata_packages.py` generates Croissant,
  RO-Crate, Frictionless, DCAT, PROV-O, a metadata-package manifest, and
  checksums from canonical repo inputs.
- `nzlc metadata-packages` and `nzlc validate-metadata-packages` expose
  generation and validation through the project CLI.
- `tests/test_metadata_packages.py` validates package generation, CLI behavior,
  and corpus-family label retention.
- No Zenodo publication or external metadata endpoint publication occurs in
  this track.
