# Track 14 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Maintain strict architectural boundaries—do not merge unrelated corpora or web products into `archive-govt-nz`.
- **MUST-2**: Provide stable JSON-LD and Parquet export interfaces for RIOPA public data consumers.
- **MUST-3**: Adopt standard RIOPA metadata and provenance schemas for cross-corpus interoperability.

## Should Have
- **SHOULD-1**: Define candidate shared libraries (e.g. `riopa-cas`, `riopa-warc`) for future extraction only after two or more independent consumers exist.

## Won't Have
- **WONT-1**: Do not merge `corpus-nz-hansard`, `fyi-archive`, or `hathi-nz` into `archive-govt-nz`.

## Dated FOI ownership supersession — 2026-08-30

The user-approved [global FOI track](../global_foi_public_archive_20260830/index.md)
supersedes the federation-only restriction for FOI orchestration, indexing,
preservation and publication capabilities. `archive-govt-nz` is the approved
receiver; `fyi-cli` remains the capture adapter. This is a prospective ownership
change, not completed cutover. WONT-1 still prohibits wholesale donor-history
merging/deletion; its historical completion evidence is unchanged. Other corpus
boundaries are unaffected. See the [approval record](../global_foi_public_archive_20260830/approval.json).
