# Source coverage, canonical schemas and remaining context

This is a bounded reconciliation, not Phase1.2, M-05 or longitudinal completion.
The 141-record official census contains73captured objects and68discovery or
non-data dispositions. All73captured CAS objects were freshly SHA-256 checked
locally with zero missing/mismatched objects. That proves selected-byte fixity,
not complete annual discovery, rights clearance or publication.

## Source-family coverage

| Family | Retained selection / bounded processing | Still pending |
| --- | --- | --- |
| Annual Budget | 2026 expenditure/revenue captured; 2025 donor and 2026 expenditure extracted | Earlier annual editions unenumerated here; revenue normalization; retrospective rows do not replace edition history |
| BEFU/HYEFU | 2026 BEFU charts/expenses/economic forecasts; 2025 HYEFU charts/expenses captured; two literal Health-summary editions each extracted | Earlier editions and other expense/chart/forecast areas |
| Fiscal/Crown expenses | 1972–2025 workbook captured; 2024 and 2025 Health/GDP source pilots retained | Other fiscal measures, exact Crown-expense contract and complete edition history |
| QES | June2026 workbook captured | Exact sector/sex/hourly-weekly/actual-adjusted series contract |
| Stats NZ GDP | March2026 current-price income/expenditure workbook captured | Exact quarterly measure and fiscal aggregation; Treasury GDP stays separate |
| Ministry Vote Health | Two HAIR2024 indicator CSVs captured and source-specific pilot extracted | Unit/base/method metadata; independent real/per-capita reproduction |
| Pharmac CPB | Budget-information HTML captured | Exact numeric table and historical source contract; capture is not extraction |
| CPI | CPIQ.SE9A source-specific extraction | Base-metadata provenance join and derived-period policy |
| Population | HLFS working-age workbook captured | Suitable national all-age resident original export; HLFS is not that denominator |
| Treasury Vote Health | 66landing/discovery records and58captured PDFs | Table normalization and semantic alignment across editions |

The donor inventory separately preserves Budget2025, BEFU2025, HYEFU2024
and fiscal2024 originals. Their absence from the official census does not mean
they were lost. All existing originals and older source-specific packages stay
intact; no newer edition silently overwrites an earlier one.

## Canonical schema and operational gaps

Health is registered in `schemas/medallion.py`, and dedicated source adapters
produce typed Arrow/Parquet tables with original lineage. This is archival
system integration, but not completion of all eight separately versioned M-05
recordsets. Budget/forecast broad Silver tables, historical exact-number and
basis fields, CPI-specific fields and Ministry published indicators are not
yet one canonical federation contract.

The next architectural slice is explicit versioned schema/registry contracts
and projections over those retained source tables. Preserve exact precision,
unknown fields, unmapped classifications, vintage keys and source pointers;
do not rewrite v1 packages or force unknown Ministry semantics into canonical
health-spending measures. Read-only Budget/raw-run CLI/MCP verification already
exists; equivalent family-wide operational exposure, recovery/resume and
scheduling remain separate acceptance tasks.

## Population route: metadata resolution, not acquisition

A later bounded metadata investigation identified Stats NZ Infoshare selector
`DPEQ.SG1CTOT` from the primary [RBNZ M12 population metadata](https://www.rbnz.govt.nz/statistics/series/economic-indicators/population-and-migration):
quarterly estimated resident population, number of people, release18August2026.
This is point-in-time population, not an annual mean or working-age population.
[Stats NZ's concept definition](https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/5c91579c-9077-4553-ae9a-1e04e6bce0e7)
supports the usual-resident reference-date interpretation. Exact payload,
full coverage, census-base metadata and fiscal mean alignment remain unverified.

The M12 workbook was not successfully inspected or acquired. Once the
[RBNZ terms](https://www.rbnz.govt.nz/about-our-site/terms-of-use) requiring
permission for automated access were read, no further RBNZ request, binary
retry or workaround occurred. The next permitted route is an original Stats NZ
export with metadata or a separately verified permitted official API/download.
No displayed summary was used to calculate spending per capita. This blocks
population normalization only, not independent archival work.

The earlier Aotearoa Data Explorer catalogue search found historical
POPES_ERP and subnational POPES_SUB dataflows, not a verified replacement
quarterly national series. In particular POPES_ERP_005 is census-date ethnic,
age and sex context; POPES_ERP_010 is health-region/district/DHB census-date
context. Both may be useful future datasets but cannot substitute silently
for the exact national denominator.
