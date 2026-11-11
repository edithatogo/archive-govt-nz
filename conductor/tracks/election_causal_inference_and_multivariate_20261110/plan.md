# Implementation Plan: Campaign Finance Causal Inference & Multivariate Drivers

- [x] Ingest preserved campaign finance returns (party donations, candidate expenses, promoter spending) into structured Parquet tables.
- [x] Implement `src/archive_govt_nz/domains/elections/finance_causal_engine.py`:
  - Compute cost-per-vote metrics and donation Gini coefficients.
  - Implement RDD at close electorate victory margins ($< 500$ votes).
  - Implement IV estimation using statutory expenditure limits as instrument.
- [x] Ingest Stats NZ 2023 Census electorate demographic profiles (renting ratio, median age, income, Māori roll migration).
- [x] Implement `src/archive_govt_nz/domains/elections/multivariate_exploratory.py`:
  - Run PCA to identify latent voter alignment axes.
  - Fit Elastic Net models predicting minor-party penetration (TOP, ACT, Greens, TPM).
  - Compute SHAP values attributing swing factors per electorate.
- [x] Export visualization telemetry feeds to `spaces/nz-election-explorer/` feeding the Political Splintering joyplot, the UMAP latent landscape, and the Coalition Matrix trees.

## Corrective validation gate (2026-11-11)

- [ ] Document causal identification, valid source observations, diagnostics and uncertainty; separate exploratory from empirical.
