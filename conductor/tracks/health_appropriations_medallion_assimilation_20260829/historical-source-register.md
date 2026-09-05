# Historical edition discovery — 5 September 2026

The [machine register](./historical-source-register.json) records the complete
30-edition scope listed by Treasury's [current and past Budgets index](https://www.treasury.govt.nz/publications/budgets/current-and-past-budgets):
1997–2026. This is a discovery denominator, not a captured corpus. Earlier
electronic documents are not held by Treasury according to that index; other
custodians have not been investigated. All 30 editions remain pending full
payload enumeration and reconciliation with existing retained objects.

Each resource has a stable `treasury-historical-` source ID followed by the
first 16 hexadecimal characters of the SHA-256 of its exact observed URL.
Uniqueness and derivation are checked by the register test. These identify
locators, not original bytes; payload hashes remain unknown until preservation
and fixity verification. A source replacement at the same URL must remain a
separate immutable object observation.

The [1997 edition page](https://www.treasury.govt.nz/publications/budgets/budget-1997)
specifically says its Estimates and Supplementary Estimates were not published
electronically on Treasury's website. The register retains that reason-coded
gap without implying worldwide unavailability; its linked BEFU remains a
separate pending discovery obligation.

The 2024 edition adds six exact workbook locators, grouped by three official
landing pages: [annual expenditure/revenue](https://www.treasury.govt.nz/publications/data/budget-2024-data-estimates-appropriations-2024-25),
[BEFU charts/expenses](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2024),
and [HYEFU charts/expenses](https://www.treasury.govt.nz/publications/efu/half-year-economic-and-fiscal-update-2024).
The workbook reader did not establish retained bytes, hashes or layout parity.
The HYEFU filenames may correspond to donor originals, but URL/name equality
alone does not prove byte equality; the donor remains intact.

The annual data page describes prior actuals, estimated actual and budgeted
values, and warns that earlier detail may differ from restated appropriation
totals. Treat these as vintage-specific observations, not interchangeable
longitudinal series. The page-level licence statement is a discovery lead,
not resource-level redistribution approval.

A direct index request returned HTTP 403 and was not retried. The metadata
observations above came from read-only web page retrieval. No local payload
retention, publication or rights qualification is claimed. The existing
141-record source census and its historical capture claims are unchanged.

Next: walk remaining official edition pages, retain explicit missing/blocked
families, reconcile duplicate locators against retained hashes, and perform
approved immutable capture with material HTTP context. Separate forecast-file
discovery remains open even for the 2024 edition. This advances M-02/M-11 and
Phase 1.2 without closing AC-03 or AC-09.

## Follow-up edition observations

The register now contains 15 locators. Six further workbooks are linked from
the official [2023 annual data page](https://www.treasury.govt.nz/publications/data/budget-2023-data-estimates-appropriations-2023-24),
[BEFU 2023](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2023),
and [HYEFU 2023](https://www.treasury.govt.nz/publications/efu/half-year-economic-and-fiscal-update-2023).
The BEFU expense filename is `befu23-data-expensetables.xlsx`, unlike the later
hyphenated pattern. Preserve the observed locator rather than guessing URLs.

The [1997 BEFU page](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-befu-1997)
links separate SNA-series, GAAP-series and Expenses PDFs. These are now
discovered resources, not absent spreadsheets or captured originals. Its other
sections remain unenumerated here. The [SNA introduction](https://www.treasury.govt.nz/sites/default/files/2017-11/befu97-sna.pdf)
distinguishes Central Government coverage from the GAAP Crown reporting entity
and discusses reconciliation differences. No cross-basis join or numerical
extraction is performed. PDF text observation is not byte-preservation evidence.
