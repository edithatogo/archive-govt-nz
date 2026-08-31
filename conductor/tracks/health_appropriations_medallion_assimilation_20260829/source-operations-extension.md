# Pharmac and GDP operational extension

## Bounded contract

This approved M15/M18, AC13/AC16 increment extends the existing source-operation
allowlist only. It preserves source-specific adapter schemas, filenames,
counts, supplied metadata and numeric observations. No canonical projection,
actual-expenditure reinterpretation, denominator selection, new acquisition or
Hugging Face/publication write is included.

Pharmac profile `pharmac-cpb-20260807/v1` dispatches the existing exact
`Pharmac-CPB-2026-08-07` HTML contract. Its source-derived pharmaceutical budget
allocations remain distinct from actual expenditure. Counts remain
facts/lineage/table_cells, with pharmaceutical_budget_facts, field_lineage and
cell_dispositions Parquet files. The existing adapter already supports true
dry-run and exclusive new-local-directory writing.

The local stack uses PR302 dependency `98fcb0d03339fb108506254fd5d1666c772664e6`,
not yet claimed delivered. Profile `gdp-expenditure-actual-2026q1/v1` retains
the exact `StatsNZ-GDP-2026Q1` source contract: quarterly current-price
expenditure-measure actuals and unknown currency, not annual aggregation or a
selected ratio denominator. Counts remain facts/lineage/dispositions; the
source-specific gdp_facts/field_lineage/cell_dispositions files are unchanged.
Publication of this extension awaits verified PR302 dependency delivery.
Forecast's missing no-write capability remains a separate task; neither
forecast profiles nor their default-writing behavior change here.

## Current evidence

The new Pharmac preflight test first failed because the profile was absent.
After the bounded dispatch/schema addition, 177 focused tests pass (3.18s),
Ruff and basedpyright pass. Existing parameterized CLI default dry-run,
explicit-local-write, forced-read-only MCP, malformed context, redaction,
failure/interrupt and original-byte tests now cover Pharmac too. A separate
direct-adapter versus dispatch comparison proves all output package bytes are
identical for the same synthetic original and context. No real source payload
is committed or used by these tests. Critical coverage is 100% (66 statements,
12 branches), with 177 tests passing in 13.44 seconds. Combined mutation/native
and hosted assurance remain pending.

The GDP profile likewise started with an expected unsupported-profile red test.
All six profiles then pass 211 focused tests (10.13 seconds), Ruff and types.
Both extended families have independent direct-adapter versus dispatch full
package byte comparisons. Independent review found no actionable issue in the
bounded allowlist/schema/parity delta. No source adapter or canonical metadata
was modified.

## Preceding delivery

PR307 was checked fresh at `d67a0358c9628c905f0dd4aacb9b517085869826`: seven
successful checks and clean mergeability. Expected-head squash merge succeeded;
readback confirmed `5fc7fc8a021e38d5759c9587c6a3908b71af4823` at
2026-08-31T15:43:42Z. No branch or clone was deleted; originals and publication
were unchanged. Its local failure/success receipts remain in source-operations.md.
