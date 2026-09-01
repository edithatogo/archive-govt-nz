# Requirements

## Must

- Independently verify the live relationship between concept DOI `10.5281/zenodo.20592539` and immutable version DOI `10.5281/zenodo.20592540`.
- Correct current target registries, source-set contracts, documentation, tests, and future metadata templates without rewriting historical evidence.
- Bind future metadata to both DOIs, target authority, donor lineage, source manifest root, and the associated Hugging Face revision.
- Distinguish local candidate, draft/update, and published states and reject fabricated DOI or publication claims.
- Add a deterministic superseding `zenodo-identity-correction.json` receipt.
- Preserve the immutable 2026 record and perform no remote mutation or version minting.

## Should

- Preserve exact response and file checksums and document any ambiguous or absent linked metadata.

## Excluded

- Hugging Face card changes, merge-state changes, Zenodo record edits, DOI minting, donor mutation, or changes to `edithatogo/legislation`.
