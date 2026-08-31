# Source coverage, canonical schemas and remaining context

This is a bounded reconciliation, not Phase1.2, M-05 or longitudinal completion.
The 141-record official census contains73captured objects and68out-of-scope
dispositions (including discovery-only edition pages). Do not describe all141
records as captured payloads. The independent local preservation audit in
`preservation-recheck.md` verifies all73captured CAS objects, their73WARC
receipts/payloads, all23donor objects and the94listed v4candidate files. That
proves selected-byte fixity, not complete annual discovery, semantic accuracy,
rights clearance or current remote publication state.

## Source-family coverage

| Family | Retained selection / bounded processing | Still pending |
| --- | --- | --- |
| Annual Budget | 2026 expenditure/revenue captured; 2025 donor and 2026 expenditure extracted | Earlier annual editions unenumerated here; revenue normalization; retrospective rows do not replace edition history |
| BEFU/HYEFU | 2026 BEFU charts/expenses/economic forecasts; 2025 HYEFU charts/expenses captured; two literal Health-summary editions each extracted | Earlier editions and other expense/chart/forecast areas |
| Fiscal/Crown expenses | 1972–2025 workbook captured; 2024 and 2025 Health/GDP source pilots retained | Other fiscal measures, exact Crown-expense contract and complete edition history |
| QES | June2026 Table8 QEMQ.SASZ9A ordinary-time average hourly earnings, total sector;9quarters and180lineage rows retained in a source-specific package; PR#298 merged | ISOcurrency, sex and adjustment metadata not inferred; deflator selection and annual alignment remain pending |
| Stats NZ GDP | March2026 current-price income/expenditure workbook captured; exact60quarter expenditure observations retained by the PR#302 implementation | Hosted delivery of that implementation at this checkpoint; fiscal aggregation and canonical projection; Treasury GDP stays separate |
| Ministry Vote Health | Two HAIR2024 indicator CSVs captured and source-specific pilot extracted | Unit/base/method metadata; independent real/per-capita reproduction |
| Pharmac CPB |14published budget-allocation observations,186lineage records and64table-cell dispositions retained; PR#295 merged | Not actual expenditure; caption lag, missing2014amount and2022scope change remain explicit; canonical projection and comparison policy pending |
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

The additive eight-record-set Arrow registry and JSON row-shape descriptors
now provide versioned structural contracts (merged PRs#293/#300). The merged
historical snapshot reader (#303) verifies pinned originals and source packages;
it is transport validation, not semantic acceptance. Narrow historical
Health/GDP and Budget classification projections, local canonical export and
source-operation interfaces are active parallel implementation streams, not
completion of the full canonical model. Preserve exact precision,
unknown fields, unmapped classifications, vintage keys and source pointers;
do not rewrite v1 packages or force unknown Ministry semantics into canonical
health-spending measures. Read-only Budget/raw-run CLI/MCP verification already
exists; equivalent family-wide operational exposure, recovery/resume and
scheduling remain separate acceptance tasks.

## Executable remaining route

1. Finish the active exact-head delivery/assurance streams: historical semantic
   projection and canonical export, Budget source-label classification and
   source-operation CLI/read-only MCP. Check live PRs and appended receipts;
   the bounded checkpoint above is not a permanently current PR dashboard.
2. Extend existing local operational profiles to already-reviewed adapters,
   preserving each source-specific schema. Persist classification occurrences
   only through verified immutable source packages and exclusive local output.
3. Add the remaining canonical semantic projections and source-area adapters:
   Budget/forecast facts, fiscal/Crown expenses, published indicators and
   contextual series. Keep source facts and every unmapped field available;
   registry membership alone does not satisfy M-05.
4. Build denominator-qualified Gold measures and metadata from those contracts.
   Population-dependent measures remain blocked on a suitable original and
   period-alignment policy; independent nominal/source-faithful work continues.
5. Exercise interruption, retained partial failures, deterministic clean-room
   rebuild and bounded scheduling before assembling a new rights-filtered
   candidate. A local staging or canonical marker is never upload approval.

The next rights work is an evidence join, not an inferred licence grant: the
three legacy workbook embedded-notice observations are hash-bound but do not
yet make those objects members of the complete-capture/v4rights qualification.
New derivatives need their own candidate-level review. Do not recapture or
overwrite retained originals to resolve a metadata gap. Earlier-edition source
discovery and Vote Health PDF table normalization remain substantive work.

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
