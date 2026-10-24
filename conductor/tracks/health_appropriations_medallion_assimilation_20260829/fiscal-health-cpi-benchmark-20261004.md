# Fiscal Health spending at an FY2025 household CPI benchmark

The local query selects the exact Fiscal 1972–2025 workbook and Stats NZ's
CPIQ.SE9A all-groups quarterly index, vintage June 2026. Both originals and
Silver/canonical packages are verified. Fiscal periods require the pinned
Treasury definition observation. CPI qualification requires the pinned Stats NZ
methodology observation and a source-point check that June 2017 equals 1000.

Official CPI methodology:
https://datainfoplus.stats.govt.nz/item/nz.govt.stats/4fb499ed-5453-4a7f-bb87-5a3835184f79

The formula policy is `fiscal-2025-cpi2026q2-equal-quarter-FY2025/v1`:
nominal Health source millions × mean CPI for FY2025 / mean CPI for the
observation's fiscal year. Each mean uses four complete quarterly index levels
with equal weights. FY2025's benchmark mean is 1293, from September/December
2024 and March/June 2025. March fiscal years use the preceding June, September,
December and current March quarters. This is a declared analytical averaging
policy, not an official annual Stats NZ series. Arithmetic uses the retained
published index numbers, not an invented unrounded publisher series.

Every row retains original nominal amounts and canonical IDs, both source
hashes/vintages, accounting coverage/basis, GST inclusion basis, all four
period and benchmark CPI IDs, source time-status labels, original flags,
period/definition evidence digests and missing/invalid-denominator reasons.
Derived fiscal starts are distinguishable from source-only known end dates.
The original CPI projection's unverified-base flag remains an input annotation;
this query records its separate metadata/source-point qualification.

The output is a household-price purchasing-power benchmark, not a health input
cost deflator. It does not remove GST effects, repair historical CPI seasonal
component changes, splice reporting bases, infer ISO currency, adjudicate rights
or publish. In particular, GST-exclusive fiscal expense observations retain
that basis while CPI's GST effects remain. Do not interpret the output as an
estimate of inflation in health-system inputs.

## Replay and assurance

Two fresh builds from both Bronze originals, through Silver/canonical and the
verified query, emit identical typed Parquet bytes. All 54 fiscal observations
have four available quarters and calculated benchmarks; every mean and derived
amount matched independent exact rational calculations from the original CPI
CSV, including an independently selected fiscal-quarter window. Originals are
unchanged. Uniform index rebasing leaves the derived benchmark invariant.

The independent raw-CSV audit initially stopped on the publisher's `NA` token.
It now preserves those 27 pre-1926 missing observations as missing; production
normalization already did so. None intersect these fiscal windows. No missing
value was replaced. Seventeen focused tests pass for exact arithmetic, ambient
precision isolation, rebasing, March years, missing/nonpositive indices,
overflow and provenance/reference-point boundaries.

The product and rebuild recipe are outside Git in the retained Health archive.
`fiscal-health-cpi-benchmark-20261004.json` binds their digests and receipts.
Integrated Gold export, DuckDB/plots, CLI/MCP and final track review remain open.
