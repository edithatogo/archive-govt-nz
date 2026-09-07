# Budget 2025 Health revenue: bounded extraction

Base: `eb90aa921a795184db606faf4070d86b9bf1683f`, source-contracts integration
HEAD when this isolated branch was created. Scope: Phase 4.2/5.2 source
extraction, M-05/M-06/M-07/M-11/M-18, AC-03/AC-05/AC-09/AC-16. No shared
plan, metadata, registry or lifecycle changes; this is not whole-phase closure.

## Source and accounting

Original `data/raw/b25-revenue-data.xlsx`, SHA-256
`2aef43eb419420a549fe56a946539f6e9afcbd91f95e9242457f26c97bafafaa`,
106159 bytes, remains in external Bronze CAS. The replay independently
decodes its literal OOXML, rather than using the adapter's normalized output
as expected values.

Raw Data rows 2:1001 have 1000 complete dispositions: 69 normalized Health
rows 172:240, 931 non-Health rows explicitly out of scope, no blanks/rejections.
The 69 facts retain 56 Non-Tax Revenue and 13 Capital Receipts observations.
Years 2021 through 2026 retain Actuals, Estimated Actual and Main Estimates
as supplied, with no aggregation or netting. App ID, department, Vote,
description, revenue type, amount, year and amount type retain source lineage.

Six other sheets receive explicit preservation/context exclusions: Intro,
Explanation, Pivot Trend by Type, Graph Trend by Type, Pivot Trend by Vote,
Graph Trend by Vote. The complete workbook structural inventory accompanies
the manifest. These exclusions do not claim normalization of the pivot/graph
content or closure of other donor workbooks.

The dedicated `budget_revenue_fact` schema does not modify the global
eight-recordset registry or automatically promote revenue into spending.
Exact decimal128(20,3) values come from original lexical numeric tokens;
unrepresentable values and selected formulas/errors are rejected. Original
amount tokens also survive rejected/out-of-scope row dispositions.

Unit is literal `$000`; ISO currency remains null. Explanation B3 binds
Budget 2025 vintage and actual/estimate context; B37/B38/B39/B43 establish
unit, June-30 year ending, amount types and App ID meaning. Year-end dates
are source-backed; period starts remain null. Each fact has 16 lineage rows
(1104 total), including these context cells. No ISO currency, period start,
classification mapping, expenditure offset or new rights decision is inferred.

Intro A10/A13/A14 are hash-bound decoded-text observations only. The manifest
labels these uninterpreted embedded-notice cells, `rights_state: not_evaluated`
and `eligibility_state: not_assessed`. The replay verifies their hashes against
the pinned original; no shared notice registry is changed.

## Implementation and verification

The adapter reuses bounded `verified_snapshot`, source context, exact-number,
identity, JSON and exclusive-output helpers. Existing workbook inventory
preflight precedes the existing historical lexical-number helper; no new
workbook parser or dependency is introduced. Output directories are exclusive;
write failure preserves partial files without a completion manifest. This is
not a claim of hostile concurrent-filesystem protection.

TDD evidence: initial missing-module red; then a failing Budget overview-year
drift test before checking B3; then a failing rejected-precision token assertion
before adding the original numeric token to dispositions. Final focused tests
cover deterministic output, exact decimals under low ambient precision,
invalid types/periods/formulas, schema and lineage, byte/hash admission,
symlinks, exclusive outputs and interrupted writes. No artificial coverage
exclusions or mutation pardons were added.

Using the existing repository Python environment with `PYTHONPATH=src`:

```sh
python -m pytest tests/domains/health_appropriations/test_budget_revenue.py -q --cov=archive_govt_nz.domains.health_appropriations.budget_revenue --cov-branch --cov-report=term-missing
# 33 passed; 101/101 statements, 32/32 branches covered.
python -m pytest tests/domains/health_appropriations/test_budget_revenue.py tests/domains/health_appropriations/test_budget.py tests/domains/health_appropriations/test_historical_numeric.py tests/domains/health_appropriations/test_workbook_common.py -q
# 124 passed.
python -m pytest tests/domains/health_appropriations/test_budget_revenue.py -q --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/budget_revenue.py --gremlin-clear-cache --gremlin-workers=4
# 70/70 killed, zero survivors, zero cache hits; 33 tests passed.
```

Ruff check, formatting and basedpyright passed on the new adapter, tests and
replay recipe. The mutation runner emitted a previously-imported-module
coverage warning; the coverage figures above are from the separate coverage
run, not inferred from mutation instrumentation.

`replay.py ARCHIVE_ROOT NEW_OUTPUT_ROOT` builds exclusive `first` and `second`
directories and verifies exact output hashes, physical schemas, every source
row/value/token, all field/context lineage, notice observations and original
byte preservation. The successful two-build receipt is
[retained-replay.json](./retained-replay.json); derivative bytes remain outside
Git. Observation time reuses retained donor context, not a new capture.

Conductor implement/review skills guided the scoped TDD and self-review.
Parent owns independent review and integrated full harness. No full harness,
new acquisition, source rights promotion, donor repair approval or publication
was performed. CPI/QES/GDP/Crown context and classification/area mapping remain
outside this adapter's scope.
