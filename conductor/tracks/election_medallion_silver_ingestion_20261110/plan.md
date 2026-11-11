# Implementation Plan: Medallion Silver Ingestion & Normalization

- [x] Ingest Bronze election result objects and build `silver_party_votes_1996_2026.parquet`.
- [x] Ingest candidate return objects and build `silver_electorate_returns_1996_2026.parquet`.
- [x] Parse Electoral Commission campaign finance into `silver_campaign_finance_1996_2025.parquet`.
- [x] Harmonize Stats NZ 2023 Census tables into `silver_census_electorates_2023.parquet`.
- [x] Validate Parquet outputs against JSON schemas using `pyarrow` and `pydantic`.
- [x] Generate Merkle provenance receipts linking each Silver row to Bronze CAS SHA-256 blobs (`src/archive_govt_nz/domains/elections/materialize_parquet.py`).

## Corrective validation gate (2026-11-11)

- [ ] Prove Bronze-to-Silver parity against versioned source snapshots and record source rights.
