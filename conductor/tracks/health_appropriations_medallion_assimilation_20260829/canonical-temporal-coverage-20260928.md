# Canonical Gold temporal coverage report

The canonical Gold manifest now carries a deterministic temporal coverage
report for every included historical, Budget and revenue product. Each group
is partitioned by the product's full source context, including vintage and
measure/unit/basis fields where available. It lists the exact observed period
tokens and count of rows for each token.

The report sorts tokens as strings and explicitly does not infer missing
periods, connect separate vintages, or join source families. It is a coverage
inventory, not a completeness, reconciliation, or analytical measure. Existing
Parquet products, source row lineage, readback checks, and exclusive dry-run
first write behavior remain intact.

## Verification

- The canonical consumer integration test verifies all three product families,
  sorted observed tokens, positive per-token counts, and explicit no-gap/no-join
  semantics.
- Focused canonical consumer suite: 15 passed; the canonical Gold exporter
  achieved 100% statement and branch coverage.
- `./scripts/validate.sh`: passed with 7,055 tests, 9 skipped, 98.17% branch
  coverage; 52 schemas and 42 representative documents validated; differential
  parity 9/9; configured mutation, hygiene, benchmark, dependency, license,
  secret-scan and SBOM gates passed.
- Hosted pull-request assurance is recorded after delivery.
