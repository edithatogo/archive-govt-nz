# Canonical historical Gold mart checkpoint — 2026-09-28

## Delivered

The canonical consumer now reads both `health_spending_fact` and
`fiscal_context_fact` from independently pinned historical packages and emits a
typed observation mart with each original record ID, source vintage, period
token, source label/locator, measure, unit, and available basis/context fields.
It also builds a coverage report partitioned by exact vintage, recordset,
measure, unit, currency, price basis, base period, and denominator definition.
The report retains the observed period tokens and does not infer chronology.

`canonical_gold_export.py` writes both Parquet tables and a SHA-256 manifest to
an exclusive local directory. It defaults to dry-run, bounds aggregate output
to 128 MiB, protects package/original/raw inputs from overlap, and reads back
each output to compare bytes and Arrow schema. Two independent exports from
the same fixture package produced byte-identical files.

## Validation

- Focused consumer/export tests: 12 passed.
- `./scripts/validate.sh`: passed on the final implementation; 6,993 passed,
  9 skipped, 98.10% branch coverage; 49 schemas and 39 representative
  documents validated; differential parity 9/9; mutation, hygiene, dependency,
  license, secret-scan, and SBOM gates passed.
- Exact output schemas and input-ID closure are asserted in the tests.

## Boundaries and next work

This checkpoint is a historical-package Gold bridge. It does not make an
analytical join between health spending and GDP, CPI, population, wages, or
Crown expense; unknown bases and denominators remain unknown. It does not
complete all longitudinal Silver source families, the remaining Gold measures,
reports and plots, Platinum metadata/federation, operational CLI/MCP/schedules,
or clean-room recovery of every product. Rights remain not evaluated and
publication was not performed. Continue those criteria independently and
preserve their evidence gates.
