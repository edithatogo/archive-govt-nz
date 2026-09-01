# Evidence

## Live identity correction

`evidence/migrations/corpus-legislation-nz/zenodo-identity-correction.json` (SHA-256 `eb9e3fc21bad482691814a45791c5e0ca6ef43658f70d2241ec9f56f335b737a`) records the live read-only API and DOI-resolver observations. Concept DOI `10.5281/zenodo.20592539` redirects to immutable version DOI `10.5281/zenodo.20592540`; the versions endpoint reports one version. The record is the 2026 annual snapshot, published 2026-06-08, open access, with `cc-by-4.0` licence metadata.

The receipt records API response hashes and independently downloaded fixity for all three files. It also records the sole live related identifier (the Hugging Face dataset), the absence of a live GitHub related identifier, and the historical pipeline identity found inside the published manifest.

## Future metadata contract

- `config/legislation/zenodo-publication.json` — SHA-256 `88f9d78f626a215e7ffeddf39dcae558ef6499ec166ad0d29404db5fc6a42760`.
- `schemas/zenodo-publication-identity-v1.schema.json` — SHA-256 `116718d88d05bddea47d3f02b98a316d820e846e29dbfb1d98354f90b5de573d`.

The contract binds concept and version DOI/record IDs, target commit, archived donor head, manifest and inventory roots, canonical Hugging Face revision, operation kind, approval, status, and remote receipt. The current operation is read-only observation.

## Validation

Focused suite: 80 passed. Critical modules `zenodo.py`, `zenodo_identity.py`, and `dist/zenodo_adapter.py`: 100% line and branch coverage. Two targeted mutation suites: 10/10 killed. Full harness: 4,472 passed, 97.50% total coverage; schemas, parity 9/9, configured mutations, dependency audit, licence inventory, secret scan, and SBOM passed.

Failed attempts are retained in `runlog.md`. The unrelated Hypothesis timing failure reproduced green without a test or threshold change.

## External actions

Read-only Zenodo API, DOI resolver, and public file downloads were performed. No draft was created, no record was modified, no DOI or version was minted, and no publication occurred.
