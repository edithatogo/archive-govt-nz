# Health component index discovery

The official [Infoshare catalogue](https://infoshare.stats.govt.nz/Default.aspx)
provides separate wage-rate and producer-input tables. Conductor identified
the tables through visible Browse navigation; the Archive owner independently
verified named dimensions, code/text display and table information through
bounded one-cell, on-screen queries for 2026Q2. No source files were exported,
native payloads archived, numeric values copied into the census receipt or analytical inputs admitted.
Session `pxID` URLs are transient and are not durable source identifiers.

## Central-government wage-rate candidate

Work income and spending → Labour Cost Index - LCI → `LCI358301.px`:
Central Govt Sector and Industry Group (ANZSIC06), June 2009 quarter = 1000.
The table reference is `LCI025AA`; Labour Cost code `3` means All Salary and
Wage Rates; Observations code `LCI025AC` means Health Care and Social Assistance.
These are observed table/dimension codes, not an inferred LCIQ concatenation.
The catalogue offers 135 quarter labels, 1992Q4–2026Q2; that does not prove
non-missing numeric coverage over the span. The selected table reports Index,
Magnitude = Units, and an update of 5 August 2026 at 10:45am. Status display
was enabled for the bounded query; historical flags remain unreviewed.

The [LCI methodology, version 66](https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/9007195c-8dc3-4dfb-b5da-1b12c32e90ac/66),
updated 26 October 2023, describes fixed-quality/quantity wage rates and excludes
merit, performance, promotion and service-increment effects. The [June 2026 period information](https://datainfoplus.stats.govt.nz/item/example.org/19f13c9d-878c-4055-88c1-5ad70a1169c0/12)
identifies pay rates at 15 May. QES average earnings retain
their separate composition-sensitive meaning. Central-government, public-sector
and all-sector catalogue tables are distinct. The release's corrected public
all-industry selector `LCIQ.SG33Z9` is not the selected Health tuple.

## Producer-input candidate

Economic indicators → Producers Price Index - PPI → `PPI387801.px`:
Inputs (ANZSIC06), NZSIOC level 3, December 2010 quarter = 1000.
The table reference is `PPI021AA`; Observations code `PPI021CC` means Health
Care and Social Assistance. The table offers 129 quarter labels, 1994Q2–2026Q2,
reports Index, Magnitude = Units, and was updated 19 August 2026 at 10:45am.
Its December 2013 rebasing footnote names specified agricultural industries;
it must not be transplanted to Health. Status display was enabled for the
bounded query; full-series numeric coverage and flags remain unreviewed.

The [business-price methodology, version 3](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/66006ba0-02ee-4c5e-9b31-9c093ba8d84f/3),
updated 15 August 2023, distinguishes input prices from wages and capital
costs. It excludes wages/salaries and capital expenditure/depreciation and says
GST is generally excluded. Its general finance-cost exclusion coexists with
explicit FISIM inclusion from March 2015; preserve that distinction rather than
claiming all financial services are excluded. General methods still require
selected-vintage and detailed-footnote qualification.

## Admission boundary

Both industry labels include social assistance. The PPI selection establishes
no central-government-only scope. Neither table is the whole Vote Health cost
basket; component weights, funding flows, ownership, capital, GST, fiscal-period
aggregation, revisions and classification/reweighting breaks remain to be
qualified before any spending comparison. Full LCIQ/PPIQ export references,
resource-specific rights and native capture/fixity remain pending. Publisher
copyright defaults and metadata readback grant no analytical or publication
approval. No new deflator policy or whole-budget formula is selected.
