# Specification: New Zealand Health Appropriations Medallion Assimilation

## Status

Approved for track initialization on 2026-08-29. Implementation, source
capture, dependency adoption, and publication remain subject to the gates in
this specification and `metadata.json`.

## Objective

Assimilate all data and useful functionality from
[`edithatogo/nz_health_appropriations`](https://github.com/edithatogo/nz_health_appropriations)
into Archive Govt NZ as a first-class, reproducible health-appropriations
domain. Preserve every donor and subsequently acquired original byte stream,
replace fragile one-off transformations with tested medallion pipelines, and
prepare rights-aware Hugging Face publication to the existing
[`health-economics-and-outcomes-research`](https://huggingface.co/collections/edithatogo/health-economics-and-outcomes-research-6a2e9986698340a8c8f4e4b4)
collection.

This track treats preservation, transformation, analysis, upload, remote
verification, collection membership, and release as distinct states.

## Pinned planning baseline

The implementation baseline is frozen to the following observations. Live
sources and hosted state must be re-observed and hash-bound before use.

| Item | Pinned observation |
| --- | --- |
| Archive Govt NZ | commit `1896ee088a3703562258268821a0e1c3bfc3f211` |
| Donor commit | `4668e6c3b1b492086941d4c1ef96e299250a8301` |
| Donor tree | `c6d44ff79eda73cfc6ba7db5764e27ce01b890e1` |
| Deterministic donor Git archive SHA-256 | `9c8ab0feaa752ead08163463a634623d55a62a69608772b73127b3d7b709157e` |
| Donor inventory | 23 tracked files; 6,604,301 bytes |
| Original source payloads | eight files: seven XLSX workbooks and one PDF |
| Donor analytical database | five SQLite tables; 312 rows in total |
| Donor functionality | workbook inspection, normalization to SQLite, four analysis families, and six checked-in PNG plots |
| Known donor defect | `process_data.py` does not compile because of an indentation error; intended behavior must be characterized and repaired |
| Hugging Face collection | public collection exists; only `edithatogo/reimbursement-atlas` was observed as a member |
| Proposed Hugging Face dataset | `edithatogo/nz-health-appropriations`; not created or published by track initialization |

The donor repository's Apache-2.0 licence covers repository code. It does not
by itself establish redistribution rights for each embedded government source
file. Rights and licence evidence are therefore recorded per resource.

## Architectural invariants

1. Every discovered original is immutable. Transformation never overwrites,
   replaces, or silently repairs source bytes.
2. The authoritative preservation record is Bronze content-addressed storage
   plus manifests and receipts; large payloads remain outside Git.
3. Silver, Gold, SQLite, plots, search indexes, and publication packages are
   deterministic, separately identified derivatives.
4. Every record and aggregate can drill through field/cell lineage to an
   original object, source location, observation time, and transformation.
5. Vintages remain distinct. Revised estimates do not overwrite prior
   budgets, forecasts, estimates, or actuals.
6. Rights uncertainty fails closed for redistribution while still permitting
   metadata, fixity, and tombstone preservation where lawful.
7. No external publication, collection mutation, release, donor retirement,
   or destructive action is implied by local validation.

## Medallion scope

### Bronze: zero-loss source and donor preservation

Bronze stores byte-exact objects and complete observation receipts for:

- the entire pinned 23-file donor tree, including documentation, code, source
  workbooks/PDF, SQLite database, and plots;
- every newly retrieved official workbook, CSV, PDF, HTML representation, API
  response, or supporting metadata file in scope;
- material HTTP context in WARC 1.1 where retrieval occurs over HTTP;
- source URL, retrieval and observation timestamps, response status and
  headers, media type, length, SHA-256, BLAKE3 where enabled, CID, source
  revision, rights evidence, and capture disposition;
- unchanged, changed, unavailable, withdrawn, restricted, corrupt, and
  retryable observations; and
- deterministic manifests, CAS deduplication, heartbeats, and reconstruction
  receipts.

Macro-enabled workbooks, formulas, charts, comments, hidden sheets, named
ranges, formatting, and embedded objects remain intact in the Bronze original
even when Silver extraction cannot interpret them. Every discovered item
receives a disposition; unsupported content is documented, never discarded.

### Silver: typed, source-faithful record sets

Add a dedicated `health_appropriations` domain rather than routing binary
workbooks through generic text normalizers. The domain supports at least:

1. `source_inventory` — object, workbook, sheet, table/range, formula and
   extraction coverage;
2. `appropriation_fact` — vote, appropriation, department, portfolio,
   category, functional classification, amount type, year/vintage, unit and
   amount;
3. `health_spending_fact` — longitudinal health spending observations;
4. `fiscal_context_fact` — GDP, total/core Crown expense and forecast context;
5. `pharmaceutical_budget_fact` — Combined Pharmaceutical Budget observations;
6. `price_population_fact` — CPI, wage and estimated-resident-population
   context used for transparent derived measures;
7. `classification_dimension` — source labels, stable internal identifiers,
   mappings and mapping confidence; and
8. `field_lineage` — record/field to object, sheet/page, row/cell/range,
   extraction rule, transformation and validation result.

Schemas preserve source labels alongside normalized values, explicit units,
financial-year semantics, nominal/real status, seasonality where applicable,
quality flags, source vintage, `valid_time`, `observed_at`, and `supersedes`
relationships. Extraction is loss-accounted: every in-scope data area is
normalized or receives a machine-readable reason for exclusion.

### Gold: reproducible analytical products

DuckDB-readable, versioned Parquet products provide:

- nominal expenditure and appropriation series;
- real terms and per-capita series with explicit base period and denominator;
- health spending as a share of nominal GDP and total/core Crown expenses;
- budget, supplementary estimate, estimated actual, and actual comparisons;
- revision- and vintage-aware comparisons without splicing incompatible
  series silently;
- appropriation, department, portfolio and functional-classification
  breakdowns;
- Combined Pharmaceutical Budget context;
- data-quality, coverage, reconciliation and source-health summaries;
- deterministic equivalents of the donor's four analysis families and six
  plots, with data extracts and plotting parameters; and
- a compatibility SQLite database generated from canonical Silver/Gold
  Parquet, never treated as the sole preservation state.

Gold products must state where fiscal classifications or institutional
boundaries changed and must not imply causal inference or forecasting.

### Platinum: governed discovery, federation and release candidates

Platinum produces schema-as-code contracts, DCAT, Croissant, RO-Crate and W3C
PROV mappings, dataset/estate cards, citation metadata, search/catalogue
projections, and fail-closed release-readiness reports. Licence text is
resource-aware; no hard-coded blanket CC BY assertion is permitted.

The domain may federate through versioned, rebuildable keys with
`reimbursement-atlas` and `global-medicines-atlas`. Graph and vector indexes
are optional projections and never preservation truth.

A Hugging Face candidate package contains only rights-cleared originals and
derivatives, plus manifests, schemas, data cards, limitations and source-level
rights information. Upload, remote readback, Dataset Viewer checks, immutable
revision capture, and collection membership are separate gated events.

## Dataset scope

### Seed corpus: pinned donor contents

The entire donor tree is in scope. Its eight original source files are:

- `b25-expenditure-data.xlsx`;
- `b25-revenue-data.xlsx`;
- `befu25-charts-data.xlsx`;
- `befu25-data-expense-tables.xlsx`;
- `fiscaltimeseries1972-2024.xlsx`;
- `historical_appropriations/appropriation-main-estimates-2024-25.pdf`;
- `hyefu24-charts-data.xlsx`; and
- `hyefu24-data-expense-tables.xlsx`.

The donor SQLite tables are `historical_health_spending` (24 rows),
`recent_health_appropriations` (215), `gdp_historical` (53), and the HYEFU24
and BEFU25 health-spending summaries (10 rows each). These counts are parity
fixtures, not proof that the donor extraction is complete or correct.

### Direct official expansion

At the implementation inventory cutoff, enumerate and disposition:

- all retrievable Vote Health Estimates and Supplementary Estimates linked by
  the [Treasury historical Vote index](https://www.treasury.govt.nz/publications/budgets/vote-information?vote=1640&year=All),
  targeting the index's 1998–2026 span while preserving gaps explicitly;
- annual Budget expenditure and revenue workbooks from the
  [Budget data library](https://budget.govt.nz/budget/2026/data-library.htm),
  including the donor's Budget 2025 inputs and the observed
  [Budget 2026 appropriation data](https://budget.govt.nz/budget/2026/estimates/data.htm)
  successor;
- BEFU and HYEFU charts, core Crown expense tables and economic/fiscal
  forecast workbooks for available vintages;
- the current successor to Treasury's
  [Data - Fiscal Time Series: Historical Fiscal Indicators](https://www.treasury.govt.nz/publications/information-release/data-fiscal-time-series-historical-fiscal-indicators),
  while retaining the donor's 1972–2024 workbook;
- Ministry of Health Vote Health series in the
  [Health and Independence Report 2024](https://www.health.govt.nz/publications/health-and-independence-report-2024-online-version),
  including available nominal, real, GDP-share and per-capita CSVs; and
- Pharmac's published
  [Combined Pharmaceutical Budget information](https://www.pharmac.govt.nz/medicine-funding-and-supply/the-funding-process/setting-and-managing-the-combined-pharmaceutical-budget-cpb/budget-bid-information).

The span and availability above are planning observations, not completeness
claims. The source census freezes exact URLs, bytes, timestamps, rights
evidence, gaps and replacement relationships before capture claims are made.

### Indirect analytical context

Where rights and stable public access permit, incorporate official Stats NZ
CPI, Quarterly Employment Survey wage measures, and estimated resident
population series, plus Treasury GDP and total/core Crown expense series. The
[Stats NZ copyright statement](https://www.stats.govt.nz/about-us/copyright/)
is recorded with each applicable resource; one current
[CPI release page](https://www.stats.govt.nz/information-releases/consumers-price-index-june-2026-quarter/)
is a discovery lead, not a frozen payload URL.

Published aggregate New Zealand Health Survey indicators may be linked when a
specific analytical question and stable join contract exist. Restricted or
unit-record survey microdata is excluded.

## Functional assimilation

The track preserves the donor's functionality while replacing unsafe
assumptions:

- workbook/sheet inspection becomes a bounded inventory command with
  machine-readable output;
- `process_data.py` behavior becomes source-specific, typed Silver extractors
  with explicit failure states and row/cell lineage;
- the donor SQLite schema remains available as a compatibility export;
- `run_analysis.py` becomes deterministic Gold queries and plot recipes;
- console summaries become structured report outputs; and
- all six donor plots receive semantic parity tests using data/query and plot
  contracts rather than requiring byte-identical PNGs across platforms.

`openpyxl` and Matplotlib are candidates because the donor relies on workbook
structure and plotting. They may be adopted only after a focused capability,
licence, security, reproducibility and maintenance evaluation, an explicit
`tech-stack.md` amendment, lockfile update, and tests. The workbook inventory
phase must remain executable even if the first candidate is rejected.

## Acceptance criteria

- **AC-01 — Complete donor preservation:** a manifest proves all 23 donor
  paths and bytes are present in Bronze or records a hard failure; the pinned
  tree and archive digest verify.
- **AC-02 — No original loss:** every acquired official item is retained
  unchanged and has exactly one explicit disposition; derivatives never
  replace originals.
- **AC-03 — Source and extraction census:** all donor workbooks/sheets and all
  discovered official candidates have stable inventory records; every
  detected data area is normalized or has a reason-coded exclusion.
- **AC-04 — Provenance and fixity:** object, observation, rights, HTTP,
  transformation and validation receipts are complete and schema-valid.
- **AC-05 — Dedicated Silver contract:** all required record sets validate,
  preserve units/vintages, and expose field/cell lineage to Bronze.
- **AC-06 — Donor database parity:** all five tables and 312 rows reconcile,
  or every row-level difference is explained, tested and approved as a repair.
- **AC-07 — Functional parity:** inspection, processing, four analysis
  families and six plots are reproducible; the donor compile defect and any
  semantic defects have regression tests.
- **AC-08 — Rebuildable compatibility:** the SQLite compatibility database,
  plots and reports rebuild from canonical Parquet and manifests.
- **AC-09 — Longitudinal coverage:** each direct source family and target
  vintage has a captured, unchanged, unavailable, withdrawn, restricted or
  superseded disposition; no silent year gaps remain.
- **AC-10 — Contextual measures:** real, per-capita, GDP-share and Crown-share
  measures identify their exact numerator, denominator, base period and
  vintage.
- **AC-11 — Quality and reconciliation:** row counts, sums, uniqueness, units,
  temporal coverage, cross-source variances and classification drift have
  deterministic checks and thresholds.
- **AC-12 — Recovery:** a clean-room reconstruction test rebuilds Silver,
  Gold, SQLite, plots and Platinum metadata from Bronze and versioned code.
- **AC-13 — Operability:** typed CLI/MCP read surfaces and scheduled capture
  support dry-run, idempotency, interruption, retry, resume, and structured
  failure receipts without requiring an always-on service.
- **AC-14 — Rights-aware Platinum:** DCAT, Croissant, RO-Crate, PROV, cards and
  catalogue records validate and never promote a resource whose redistribution
  decision is absent or incompatible.
- **AC-15 — Hugging Face verification:** after explicit approval and credential
  availability, the exact candidate manifest is uploaded, remotely read back,
  Dataset Viewer/Parquet behavior checked where applicable, revision pinned,
  and collection membership independently verified.
- **AC-16 — Repository assurance:** focused, property, mutation, recovery,
  schema, security, supply-chain and full repository gates pass at the required
  checkpoints, with 100% branch coverage for critical policy/integrity logic
  and at least 95% overall production coverage.

## External and accountable gates

The following are not satisfied by this track scaffold or by green local CI:

- parent GitHub issue creation and hosted issue hierarchy;
- resource-level redistribution-rights decisions;
- adoption of material new dependencies;
- access to publication credentials;
- approval of a checksum-pinned Hugging Face candidate manifest;
- creation or mutation of the Hugging Face dataset and collection;
- remote verification and public release claims;
- donor repository archival or deletion; and
- any Zenodo deposition or DOI publication.

Independent local implementation may continue around a pending external gate
where the affected branch can remain fail-closed.

## Out of scope

- merging or rewriting donor Git history;
- deleting or archiving the donor repository;
- committing source payloads or large derivatives to Git;
- publishing private, restricted, personal or unpublished data;
- acquiring New Zealand Health Survey unit-record microdata;
- treating forecasts as observed outcomes or making causal claims;
- providing an always-on service or bespoke interactive frontend; and
- publishing a Zenodo release or DOI.
## Principal risks and controls

| Risk | Control |
| --- | --- |
| Donor code is syntactically broken or semantically lossy | Characterization tests, row/cell lineage, parity fixtures, and reason-coded repairs |
| Workbook layouts and classifications drift across vintages | Source-specific adapters, schema fingerprints, header/table discovery tests, and vintage dimensions |
| An aggregate is double counted across appropriation types | Stable amount-type semantics, uniqueness constraints, reconciliation queries, and non-additive flags |
| A licence is inferred from repository context | Per-resource rights evidence and fail-closed publication eligibility |
| Current source replaces historical bytes | Immutable Bronze versions and explicit supersession relationships |
| Binary payloads enter Git | CAS paths outside Git, manifest-only source control, and size/secret gates |
| Reproducible PNG bytes vary by platform | Semantic plot contracts plus pinned environment and data/query digests |
| HF upload is mistaken for verified release | Separate candidate, upload, readback, viewer, collection and release states |
| Context series are mixed across bases/vintages | Explicit units, base periods, denominators and source-vintage keys |
