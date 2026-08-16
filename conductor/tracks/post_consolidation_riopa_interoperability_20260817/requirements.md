# Track 14 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Maintain strict architectural boundaries—do not merge unrelated corpora or web products into `archive-govt-nz`.
- **MUST-2**: Provide stable JSON-LD and Parquet export interfaces for RIOPA public data consumers.
- **MUST-3**: Adopt standard RIOPA metadata and provenance schemas for cross-corpus interoperability.

## Should Have
- **SHOULD-1**: Define candidate shared libraries (e.g. `riopa-cas`, `riopa-warc`) for future extraction only after two or more independent consumers exist.

## Won't Have
- **WONT-1**: Do not merge `corpus-nz-hansard`, `fyi-archive`, or `hathi-nz` into `archive-govt-nz`.
