# Track Spec: Medallion Silver Ingestion & Normalization

Transform raw Bronze CAS objects (`objects/`) into normalized, schema-validated Silver Parquet tables (`derivatives/parquet/`):
1. `silver_party_votes_1996_2026.parquet`: Standardized party names, percentages, and vote counts across all 10 MMP elections.
2. `silver_electorate_returns_1996_2026.parquet`: Electorate candidates, margins, winners, and voter turnout.
3. `silver_campaign_finance_1996_2025.parquet`: Cleaned party donations, candidate expense returns, and third-party promoter expenses.
4. `silver_census_electorates_2023.parquet`: Harmonized Stats NZ 2023 Census variables per electorate (renting ratio, median income, youth ratio, Māori roll migration).
5. Enforce Merkle provenance attestation using `edithatogo/tobac` and `edithatogo/sourceright`.
