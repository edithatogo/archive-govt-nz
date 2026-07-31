# Hugging Face Dataset Viewer support packet

## Reproduction

- Source archive: `edithatogo/archive-govt-nz-treasury`
- Derivative repository: `edithatogo/archive-govt-nz-treasury-data`
- CSV fallback: `edithatogo/archive-govt-nz-treasury-csv`
- Viewer endpoints: `/is-valid`, `/splits`, `/parquet`, `/rows`, `/size`, `/statistics`
- Result: HTTP 500 for all endpoints on fresh and existing repositories.

## Local evidence

- Parquet: 54 rows, six typed columns; direct Hub download and PyArrow reads pass.
- CSV: 54 normalized rows; direct Hub upload succeeds.
- Tested layouts: derivative-only, canonical split filename, minimal card, CSV-only, Parquet-only, and Snappy/Zstandard compression.

## Requested support

Please identify the conversion-service failure for these public repositories or
advise the required Dataset Viewer layout/configuration. No credentials or
private data are involved.
