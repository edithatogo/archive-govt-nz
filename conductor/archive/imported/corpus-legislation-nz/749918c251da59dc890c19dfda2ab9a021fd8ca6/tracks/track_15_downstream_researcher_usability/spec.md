# Spec - Downstream Researcher Usability

## Status
ready

## Goal
make the published corpus easy to inspect and query after the live hub is stable.

## Acceptance Criteria
- A new user can query the Parquet dataset without downloading the full raw corpus.
- Examples are tested or manually verified.
- Optional browser UI is clearly secondary to the dataset pipeline.

## Evidence to Record
- Example command output.
- Sample dataset path or revision.
- Documentation links.

## Evidence Recorded

- Documentation added on 2026-06-07:
  - `docs/researcher_quickstart.md`
  - `docs/data_dictionary.md`
- Documentation links added:
  - `README.md` links to researcher quickstart and data dictionary.
  - `DATASET_CARD.md` points core field definitions to the data dictionary.
- Researcher examples verified on 2026-06-11:
  - DuckDB `hf://datasets/` queries verified against live Hugging Face dataset.
  - Sample DuckDB output: 9 records, all `act` type, all 2026 year.
  - PyArrow example updated to avoid pandas dependency; verified with local smoke fixture.
  - Local smoke fixture commands (`nzlc smoke-fixture`, `nzlc validate`) verified to produce viable Parquet output.
- Sample split decision:
  - A public sample split is deferred until the full validated corpus is published (Track 08). The live dataset contains partial/API-discovery data; publishing a sample could be mistaken for coverage evidence.
- Optional browser UI decision:
  - Do not add a Hugging Face Space yet. Browser/search UI remains secondary until the dataset pipeline and live hub are stable.
