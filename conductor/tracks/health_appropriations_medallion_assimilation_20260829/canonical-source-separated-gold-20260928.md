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

## Verification

- Focused canonical consumer and Gold exporter tests: 15 passed, including a
  mixed three-family build, exact output comparisons with the verified
  read-only consumers, dry-run behavior, repeat-build byte equality, and the
  existing bounded failure contracts.
- Ruff check, Ruff format, and `git diff --check`: passed.
- `./scripts/validate.sh`: passed with 6,996 tests, 9 skipped, and 98.12%
  branch coverage; 49 schemas and 39 representative documents validated;
  differential parity 9/9; mutation, hygiene, dependency audit, licence,
  secret-scan, and SBOM gates passed.
- Hosted PR checks: pending.

## Remaining scope

This package does not provide contextual denominator joins, real/per-capita or
GDP/Crown-share measures, all source-native Silver projections, new Gold plots,
Platinum federation, or broader CLI/MCP/scheduled build operations. Those remain
separate acceptance work and require source and period evidence before
analytical promotion.
