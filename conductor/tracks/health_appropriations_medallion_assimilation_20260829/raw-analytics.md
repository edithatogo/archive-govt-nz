# Source-derived analytical contracts

## Scope

Pure historical and Budget functions consume canonical source facts, not the
compatibility database. They do not verify files, write Gold artifacts,
publish data or clear rights. A persistence caller must verify pinned raw-run
manifests, snapshots and lineage. Phase 4.3 analytics remains in progress.

## Historical

Preserve exact Health values, input IDs and source context. Partition source
objects and vintages; reject duplicate year/measure identities. Growth requires
consecutive years, known matching fiscal-year ends and Health accounting bases,
and a positive previous value. GDP share requires the same source, vintage,
currency unit and exact period end, plus positive GDP. GDP need not have a
Health accounting basis. Period starts remain unverified; period alignment
does not assert institutional-scope equivalence.

Missing comparisons are null with reason codes, never zero-filled. Preserve
previous/denominator exact values and IDs. Percentages use an independent
80-digit Decimal context, half-even rounded to 12 decimal places. Canonical
Decimal(38,17) inputs stay exact. Reject inconsistent/non-month-end dates and
non-text accounting bases.

Verified retained input: 106 facts, returning 53 Health rows, 53 period-aligned
GDP shares and 48 growth observations. Growth is unavailable at 1972 (first
observation), 1990 (fiscal-period change), and 1994/1997/2005 (accounting-basis
changes). The 1976 exact amount stays `605.70000000000005000`.

## Budget

Sum Decimal(20,3) values by source object, vintage, year, source classification
label and amount type. Retain contributing IDs, departments, portfolios and
quality flags. Never combine Actuals, Estimated Actual and Budget categories.
Keep negative corrections. Fiscal-year basis remains explicitly unverified.

The breakdown selects only 2025 `Estimated Actual`. Verified retained input
has 215 facts, 16 trend rows and four breakdown rows; all 215 IDs accounted for.

| Source classification | 2025 Estimated Actual, NZD thousands |
| --- | ---: |
| Core Government Services | 5036.000 |
| Health | 26740144.000 |
| No Functional Classification | 3225798.000 |
| Social Security and Welfare | 12573.000 |

These are source labels within the selected Health inputs, not a mapped
cross-government classification series or newly acquired resource.

## Validation and continuation

Functional commit `0bf14b07ac07ef5271a5e44626e4a8857907641b`.
Full isolated harness exit 0: 1,656 tests, 96.09% coverage, eight existing
SQLite resource warnings, 35 schemas/25 documents, 9/9 parity, all mutation
and supply-chain gates; validated 110-component SBOM.

Historical: 47 focused tests, 30 generated growth cases, 100% critical line/branch
coverage; 71/71 unfiltered mutants killed, zero pardons. Report
`bc16dcf301e3dc8147be5859b98011b85951b1e3374a6fb1e86e337c2305e932`.
Budget: 32 focused tests, 100% critical line/branch coverage; 33/33 unfiltered
mutants killed, zero pardons. Report
`f3bf27e942822a5c239983fbf6092ef6e65016cf49e9bc6345399f2bd9000c99`.

Next: verified raw-reader integration, exclusive deterministic Gold tables and
manifest/CLI, donor analytical comparison with source-only/precision/basis
differences, then six plot contracts. Real/per-capita/Crown-share and broader
datasets retain separate denominator, period, rights and scope gates.
Originals and existing publication remain unchanged; no assimilation closeout.
