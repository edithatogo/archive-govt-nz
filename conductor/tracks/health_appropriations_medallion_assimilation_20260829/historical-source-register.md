# Historical edition discovery — 27 September 2026

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


## Earlier Budget and forecast inventory — 27 September 2026

The register now contains 68 locators across 21 editions (1997, 2001, 2005,
and 2007–2024). Official Treasury release pages establish linked appropriation
expense/revenue workbook resources for Budget 2007–2016 (where listed),
BEFU 2001, 2005, 2007–2008 and 2010–2016, and a HYEFU 2015 charts/data
workbook. The BEFU 2014–2016 expense tables are represented by their official
edition pages, which publish the tables directly; these entries are page
locators and do not claim separate spreadsheet payloads. The 2013 BEFU chart
workbook page and older expense tables provide historic coverage for the
Treasury core Crown expense measure.

Budget workbook release pages say these workbooks support but are not part of
the official Budget documents; the Estimates and Supplementary Estimates as
tabled are authoritative. The listed Budget workbooks exclude the previous
year's Supplementary Estimates, and prior detail may not reconcile after later
restructuring. Their time columns encode actual, estimated actual and budget
values for specific year ends, so edition vintage and status must remain
separate. Treasury page-level CC BY 4.0 statements are retained only as rights
leads. No locator in this register establishes item-specific rights,
redistribution eligibility, retained bytes, or fixity.

Budget workbook and other source-family locators for 1998–2000, 2002–2004,
2006, and 2025–2026 remain missing from this discovery pass; BEFU 2002 has a
separate GAAP expense-table locator described below. All 30 years remain
pending because no edition has had its complete source families enumerated; a
locator never marks an edition complete. Captured Budget 2026, BEFU 2026 and
HYEFU 2025 resources remain separately represented in the source census.

## BEFU 2002 GAAP expense series — 6 October 2026

The official [BEFU 2002 page](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-befu-2002)
links [Generally Accepted Accounting Practice (GAAP) Series Tables](https://www.treasury.govt.nz/sites/default/files/2007-09/befu02-gaap.pdf)
and states the Treasury copyright licence as CC BY 4.0. The observed item is
the 52-page PDF `befu02-gaap.pdf`; bytes have not been retained or hashed and
the item-level rights state remains `not_evaluated`.

The printed page 144 (`PDF page 4`) contains a Forecast Statement of Financial
Performance for years ending 30 June. Its exact total-expense series is
`Total Expenses`, in `$ million`: 2001 Actual, 2002 Previous Budget, 2002
Estimated Actual, and 2003–2006 Forecast. The PDF states that forecasts follow
the Fiscal Responsibility Act 1994 and reflect information and decisions
communicated by 10 May 2002. This is a GAAP Crown reporting-entity measure; it
is not assumed interchangeable with Core Crown Expenses, later accounting
bases, or modern financial-year tables.

This adds one official BEFU resource locator and a source-backed period/unit
description. It does not enumerate the complete 2002 source families, locate
the Budget 2002 expenditure/revenue data workbooks, retain payload bytes, or
approve a historical join. The 2002 edition remains pending and publication
remains unauthorized.

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


## Budget 2021–2022 workbook locators — 25 September 2026

Read-only review of the official Treasury [Budget 2021 data page](https://www.treasury.govt.nz/publications/data/budget-2021-data-estimates-appropriations-2021-22) and [Budget 2022 data page](https://www.treasury.govt.nz/publications/data/budget-2022-data-estimates-appropriations-2022-23) found separate expenditure and revenue workbooks for each edition. The pages describe source years and warn that earlier actual/estimated-actual detail is not restated after later restructuring. Budget 2022's landing page states CC BY 4.0; the Budget 2021 page's license field was not observed, so its rights remain not evaluated.

The four exact workbook URLs are in the machine register. The browser could not retrieve the XLSX payloads; hashes and byte counts therefore remain null. These four discoveries do not close either edition's source enumeration, establish captured bytes or rights eligibility, or qualify the workbooks for analysis/publication.


## Budget 2020–2022 workbook locators — 25 September 2026

Read-only review of the official Treasury [Budget 2020](https://www.treasury.govt.nz/publications/data/budget-2020-data-estimates-appropriations-2020-21), [Budget 2021](https://www.treasury.govt.nz/publications/data/budget-2021-data-estimates-appropriations-2021-22), and [Budget 2022](https://www.treasury.govt.nz/publications/data/budget-2022-data-estimates-appropriations-2022-23) data pages found separate expenditure and revenue workbooks for each edition. The [BEFU 2020 page](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2020) links chart/data and expense-table workbooks. The pages describe source years and warn that prior actual/estimated-actual detail is not restated after later restructuring. The Budget 2020 and 2022 landing pages state CC BY 4.0; Budget 2021's license field was not observed. Rights remain not evaluated for every resource.

The eight exact workbook URLs are in the machine register. The browser could not retrieve the XLSX payloads; hashes and byte counts therefore remain null. These discoveries do not close the editions' source-family enumeration, establish captured bytes or rights eligibility, or qualify the workbooks for analysis/publication.


## Budget 2018–2019 workbook locators — 25 September 2026

Read-only review of the official Treasury [Budget 2018](https://www.treasury.govt.nz/publications/data/budget-2018-data-estimates-appropriations-2018-19), [Budget 2019](https://www.treasury.govt.nz/publications/data/budget-2019-data-estimates-appropriations-2019-20), [BEFU 2018](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2018), and [BEFU 2019](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2019) pages found eight workbook locators: expenditure and revenue for each Budget, and charts/data and expense tables for each BEFU. Both budget data pages warn that prior actual/estimated-actual detail is not restated after later restructuring. The landing pages state CC BY 4.0; this is recorded as page-level evidence only and rights remain not evaluated.

The 2018–2019 Budget workbooks use legacy `.xls` format. The browser could not retrieve the linked workbooks; hashes and byte counts remain null. These discoveries do not close either edition's source-family enumeration, establish captured bytes or rights eligibility, or qualify data for analysis/publication.


## Budget, BEFU and HYEFU 2017 workbook locators — 25 September 2026

Read-only review of Treasury's official [Budget 2017 data](https://www.treasury.govt.nz/publications/data/budget-2017-data-estimates-appropriations-2017-18), [BEFU 2017](https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2017), and [HYEFU 2017](https://www.treasury.govt.nz/publications/efu/half-year-economic-and-fiscal-update-2017) pages found five workbook locators: Budget expenditure and revenue, BEFU charts/data and expense tables, and HYEFU charts/data. The Budget page warns historical detail predates later restructuring and excludes the prior year's Supplementary Estimates. Landing pages state CC BY 4.0; this is page-level evidence only and rights remain not evaluated.

The linked payloads were not retrieved; hashes and byte counts remain null. These five discoveries do not close the 2017 edition's full source-family enumeration or qualify data for analysis/publication.
