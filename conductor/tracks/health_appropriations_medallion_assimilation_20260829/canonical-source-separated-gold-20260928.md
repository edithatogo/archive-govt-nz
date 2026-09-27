# Source-separated canonical Gold package

This is a local, rebuildable Gold package over exact pinned canonical package
inputs. It extends the historical observation mart in
`canonical-historical-gold-20260928.md` with nominal Budget appropriation and
Budget revenue products. It accepts the already verified historical, Budget,
and revenue package kinds and runs each consumer independently.

The v2 manifest records one bounded input/output report for each included
product, output hashes/byte lengths/row counts, and exact package marker pins.
The files retain their declared canonical consumer schemas and source record
IDs. Historical context coverage remains grouped by its complete measure,
unit, currency, price basis, base period, and denominator context. Budget totals
sum only identical source labels and units. Revenue remains an identity
projection; expenditure/revenue netting is prohibited. There are no
cross-family joins or cross-vintage pooling.

The existing dry-run-first and exclusive local write path remains in force.
Every Parquet file and the manifest are read back before success, a partial
failure produces only a bounded failure receipt, and each family of inputs is
protected from output overlap. Rights remain `not_evaluated` and publication is
`not_performed`.

The v2 package also includes one or more bounded display-only PNGs per eligible
source context. Categories preserve the exact source period token and labels;
the charts do not parse periods, connect points or imply continuity. The plot
report binds each image to its context digest and input record IDs, records its
hash/size, and makes limit-based omissions visible. Exact Decimal values remain
in the Parquet tables; conversion to floating point occurs only for rendering.

## Verification

- Focused canonical consumer and plot tests: 19 passed, including a mixed
  three-family build, output comparisons with verified read-only consumers,
  dry-run behavior, repeat-build byte equality, bounded plot omissions, and
  fail-closed contracts. Both changed product modules have 100% branch coverage.
- Ruff check, Ruff format, and `git diff --check`: passed.
- `./scripts/validate.sh`: passed with 7,000 tests, 9 skipped, and 98.13%
  branch coverage; 49 schemas and 39 representative documents validated;
  differential parity 9/9; mutation, hygiene, dependency audit, licence,
  secret-scan, and SBOM gates passed.
- Hosted PR checks: pending.
- Hosted PR checks: pending.

## Remaining scope

This package does not provide contextual denominator joins, real/per-capita or
GDP/Crown-share measures, all source-native Silver projections, the full Gold
report suite, Platinum federation, or broader CLI/MCP/scheduled build
operations. Those remain separate acceptance work and require source and period
evidence before analytical promotion.
