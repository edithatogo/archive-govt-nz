# Fiscal Health spending per annual mean resident

This local query selects the exact Fiscal Time Series 1972–2025 spending
workbook and the Stats NZ DPE056AA annual June mean-year-ended Total All Ages
population export, release 18 August 2026. Both original objects and their
Silver/canonical packages are verified before arithmetic. The two source
vintages are intentionally distinct and remain explicit in every result.

The derived policy is `fiscal-2025-population-20260818-june-mean/v1`:
Health source dollar millions × 1,000,000 / annual mean resident persons,
rounded half-even to 12 decimal places. It compares matching July–June dates,
uses mean population for a spending flow over the year, and does not substitute
June-end population stocks. March fiscal years have no matching denominator.
The result is a nominal spending rate, not an individual's cost of care.

Fiscal starts require the pinned Treasury period observation introduced in
PR #627. Mean-population selection additionally requires the pinned Stats NZ
period-definition observation. Changed/missing observation bytes fail closed.
Both are retained web-tool text observations, not original HTML captures.

Population definitions: https://datainfoplus.stats.govt.nz/item/nz.govt.stats/4c9f3523-5386-4ce0-a8bd-993bb905f119/201

The query preserves canonical IDs, exact input amounts, both source hashes
and vintages, the spending coverage/accounting basis, original quality flags
and both period-evidence hashes. Fiscal flags include the shared-workbook GDP
context flags from the verified share query; GDP is not in the rate formula.
Source projection flags describing context-only status remain historical input
annotations. The new query receipt selects the denominator for this one policy;
it does not globally approve other joins or change the original projections.

Recent population observations are provisional; revision/census-base flags
remain visible. This does not assert a uniform 2023 census base throughout
history, splice accounting bases, infer an ISO currency, claim health-sector
price adjustment, adjudicate rights or publish anything. Missing/excluded rows
remain in the output with null derived amounts and explicit reasons.

## Native recovery evidence

Two fresh Bronze-to-Silver/canonical/query rebuilds emitted identical typed
Parquet bytes and unchanged originals. There are 54 Health-year rows:
34 calculated (1992–2025), 2 missing-population rows (1990–1991) and
18 unsupported March-year rows (1972–1989). Every calculated amount matched
an independent exact rational calculation and half-even rounding.
FY2025 is 30,311 million / 5,307,900 mean residents × 1,000,000 =
5,710.544659846644 source dollars per mean resident, with population's
provisional flag retained.

The product and repeat-build recipe are outside Git under the retained Health
archive. `fiscal-health-per-capita-20261004.json` binds their digests and the
query receipt. CLI/MCP, integrated Gold exporter and plots remain separate
work; this evidence does not close those products or the final track gate.

PR #628 review correction: every row now directly preserves the fiscal
`numerator_source_time_status` and population `valid_time_status` alongside
the derived period and pinned evidence digests. The fiscal source start remains
unknown at source level; its derived date is not relabelled as source-provided.
