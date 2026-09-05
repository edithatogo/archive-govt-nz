# Analytical context register

Observed 2026-09-05 from the pinned source census and retained source-specific
profiles. This register defines join candidates; it is not an authorization to
calculate or promote Gold measures.

| Context | Exact retained identity | Period/basis | State | Join boundary |
| --- | --- | --- | --- | --- |
| CPI | stats_nz_cpi-053a0705526fac8d / CPIQ.SE9A | Quarterly, June 2026 release; index, not currency | Captured and source-profiled | Do not infer an annual fiscal mean; preserve the June 2017 = 1000 base and source vintage |
| Wage | stats_nz_qes-faab0efe46470af8 / QEMQ.SASZ9A | Nine quarters through June 2026; ordinary-time hourly earnings, total sector | Captured and source-profiled | Currency, sex and adjustment metadata remain null; not a deflator by itself |
| GDP | stats_nz_gdp-9fc80ed4b7f234b2 | March 2026 current-price income/expenditure workbook; quarterly observations | Captured and source-profiled | Keep quarterly basis and national-accounts vintage separate from Treasury fiscal series |
| Working-age population | stats_nz_population-806dead2a5b8ab69 | HLFS June 2026 quarter; working-age estimate | Captured | Not a national all-age resident denominator; cannot support per-capita spending |
| Resident population | Stats NZ national estimated resident population selector DPEQ.SG1CTOT | Quarterly point-in-time number of people | Metadata lead only | Exact permitted payload, full coverage, census base and fiscal-period alignment remain unverified |
| Crown expense | befu_2026-003, hyefu_2025-006, and fiscal_time_series-007 | Source-specific forecast/actual and accounting bases | Captured source material; no unified join | Require explicit measure definition, accounting basis, period and vintage before Gold use |

The CPI profile source contract retains the index base as unresolved in its
derived output even though Stats NZ metadata describes the June 2017 quarter as
the reference period. This register records that metadata lead without
retroactively changing the retained package.

No row establishes rights for a new derivative, complete historical coverage,
or publication eligibility. A future promotion must join the exact source
object, source-specific schema, period/basis definition, vintage, lineage and
rights receipt, and must report unmatched observations.

*** Update File: /Volumes/PortableSSD/GitHub/archive-govt-nz-health-dcat-review/conductor/tracks/health_appropriations_medallion_assimilation_20260829/plan.md
@@
 - [ ] Enumerate the exact official CPI, QES wage, population, GDP and Crown
   expense series needed for approved derived measures; reject discovery leads
   that lack a stable definition or join. [M-02, M-12; AC-03, AC-10]
   Analytical context register records exact captured identities and keeps
   resident-population and Crown-expense joins explicitly unresolved.
