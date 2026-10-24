# Analytical context register

Reconciled 2026-10-16 against merged source-specific implementations and their
retained evidence. This is the current planning register; dated source and
recovery receipts remain historical evidence. Source-faithful projections and
qualified analytical policies have distinct claims. The policies below support
only their named inputs and outputs, not general comparability across products.

## Retained context and analytical boundaries

| Context | Exact retained identity | Period/basis | Current state | Remaining boundary |
| --- | --- | --- | --- | --- |
| CPI | stats_nz_cpi-053a0705526fac8d / CPIQ.SE9A; original SHA-256 `f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d` | Quarterly all-groups index, June 2026 vintage | Captured, source-profiled and projected. The separate fiscal benchmark verifies retained methodology evidence and June 2017 = 1000, with an explicit four-quarter mean and FY2025 reference | Household purchasing-power benchmark only. GST effects remain; no health-input-cost deflator or generic real-spending measure is qualified |
| Wage | stats_nz_qes-faab0efe46470af8 / QEMQ.SASZ9A | Nine quarters through June 2026; total-sector ordinary-time hourly earnings per paid hour | Captured, source-profiled and projected. Supplemental methodology supports not-seasonally-adjusted status | ISO currency remains unknown. Earnings are not a constant-quality wage index; no spending-deflator policy is selected |
| Stats NZ GDP | stats_nz_gdp-9fc80ed4b7f234b2 (March) and stats_nz_gdp-588a47c19c9dbc44 (June) | Separate current-price income/expenditure workbook vintages | Both captured, source-profiled and projected; vintage/revision evidence retained | Keep separate from each other and Treasury fiscal GDP; no cross-vintage splicing, currency inference or annual denominator join follows from contextual admission |
| Working-age population | stats_nz_population-806dead2a5b8ab69 | HLFS June 2026 quarter; working-age estimate | Captured as its own contextual source | Not an all-age resident denominator for per-capita spending |
| Quarterly resident-population lead | Stats NZ DPE054AA; population C, age DPE054FF, estimate 1 (As at) or 2 (Mean year ended) | Quarterly metadata selection described in the earlier census | Retained discovery lead; distinct from the captured annual export below | Do not substitute quarterly stocks or this discovery lead for the selected annual mean denominator |
| Annual resident population | Stats NZ DPE056AA annual June mean-year-ended Total All Ages; original SHA-256 `a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9`; release 18 August 2026 | Persons; matching July-June mean population | Numeric export captured, normalized and projected. A pinned two-vintage policy supports the Fiscal 2025 nominal per-capita query | Retain provisional/revision flags. March fiscal periods are unsupported; unmatched June years remain missing. No uniform historical census base or other denominator substitution is inferred |
| Treasury fiscal GDP and Crown expenses | Fiscal-Time-Series-1972-2025; original SHA-256 `de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f` | Same-workbook source dollar millions; explicit March/June fiscal definitions and cash/old-GAAP/IFRS/PBE regimes | Captured and projected. Pinned period evidence supports Health/GDP, Health/core Crown and Health/total Crown ratios | Keep regime breaks and missing denominators. Total-Crown ratio retains the core-Crown Health numerator; it does not estimate Health expenditure across all Crown entities. ISO currency and cross-family joins remain unqualified |
| Forecast Crown expense sources | befu_2026-003 and hyefu_2025-006 | Edition-specific forecast/actual and accounting bases | Captured and covered by existing source-specific profiles | No unified join with historical fiscal, Budget or Pharmac measures. Preserve edition, amount type, period and accounting context |

## Implemented policies and evidence

- [Fiscal Health shares](./fiscal-health-shares-20261004.md), policy
  `fiscal-2025-source-period-health-shares/v1`: 162 rows, including 115
  calculated ratios and 47 missing-denominator rows. All 115 calculated
  percentages were independently reconciled. Source-level unknown starts remain
  distinguishable from dates derived using the pinned Treasury observation.
- [Annual mean resident rates](./fiscal-health-per-capita-20261004.md), policy
  `fiscal-2025-population-20260818-june-mean/v1`: 54 rows, with 34 calculated,
  two missing-population and 18 unsupported March-period dispositions. This
  policy intentionally pairs two exact source vintages.
- [Household CPI benchmark](./fiscal-health-cpi-benchmark-20261004.md), policy
  `fiscal-2025-cpi2026q2-equal-quarter-FY2025/v1`: 54 calculated benchmark rows.
  Published quarterly indices are equally weighted; this is a declared policy,
  not an official annual Stats NZ series. Source projection flags are retained
  alongside the separate methodology qualification.
- [Fiscal analytical Gold](./fiscal-analytical-gold-20261004.md) packages nominal,
  share, per-capita and CPI benchmark tables with pinned manifests, exact
  schemas, formulas and exclusions. Its named-query implementation is
  `fiscal_analytical_operations.py`; the Phase 6 plan records subsequent query,
  report, plot and recovery integration rather than treating the earlier
  product receipt's then-open follow-ups as current blockers.

On 2026-10-16, local readback matched the three retained analytical Parquet
outputs to their receipt digests, verified their Treasury period observation
pin, matched the combined Gold manifest to its recorded digest, and verified
all three Bronze originals against their content-addressed identities. This was
fixity readback, not a new source retrieval, full rebuild or rights review.

## Remaining qualification work

Complete query and reconciliation contracts for the existing source-separated
Budget, classification, department/portfolio and Pharmac products. A shared
period label alone is insufficient to establish economic comparability. Any new
comparison must document its measure, coverage, period boundaries, units,
accounting/GST basis, amount type and vintage policy, retaining missing or
incompatible observations with reasons.

The [Budget comparison](./budget-comparison-gold-20261005.json) already supports
literal-dimension estimate-to-later-value diagnostics. It does not establish
restated appropriation comparability or expenditure performance. Pharmac's
existing [published-budget profile](./pharmac-cpb.md) already includes 2026/27,
despite the retained caption ending in 2025/26. Keep allocation distinct from
actual expenditure and preserve the 2022 funding-holder reform; do not capture
or introduce another vintage solely because the table contains 2026/27.

For a proposed health-service purchasing-capacity measure, first qualify an
exact deflator candidate against its official definitions, coverage, period,
GST treatment and revisions, then prepare the formula and sensitivity evidence.
Selecting such a policy is separate from the implemented household benchmark.

A concrete methodological lead is Stats NZ's
[September 2022 national-accounts update](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/81c86948-c813-486a-b46b-0c614f03291a),
reviewed as web-tool text on 2026-10-16. It describes a revised deflator for the
health compensation component of central-government consumption, alongside
deferred alignment work and coherence adjustments. This component-specific,
historical methods note does not identify a qualified numeric series covering
all Vote Health expenses. The exact series/export, current methodology, coverage,
period/base, revision and rights evidence remain pending. No original-page
capture or numeric admission is claimed by this review.

The earlier [2018 GDP sources and methods, table 8, printed pages 43-44](https://www.stats.govt.nz/assets/Uploads/Methods/Quarterly-gross-domestic-product-Sources-and-methods-fifth-edition/quarterly-gross-domestic-product-sources-and-methods-fifth-edition.pdf)
distinguishes health PPI sub-indexes for intermediate consumption, health LCI
sub-indexes for employee compensation, and health CPI for social benefits in
kind. These are component-specific methods, not interchangeable whole-budget
deflators. Qualifying a new policy therefore needs the exact component coverage
and current methodology as well as an index locator; this historical manual
does not itself qualify current series, weights or a Vote Health join.

This register grants no new derivative redistribution rights or publication
eligibility. Keep resource-specific rights evidence and existing external
publication receipts separate from local analytical completion.
