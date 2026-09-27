# Context Gold coverage mart — 2026-09-28

`context_gold.export_context_gold` builds a bounded, source-separated local
Gold product from the exact retained Silver packages for CPIQ.SE9A, QEMQ.SASZ9A,
Stats NZ current-price GDP and the DPE056AA annual mean-year-ended population
series. It verifies each source object against Bronze CAS, checks each Silver
manifest and Parquet hash, validates row lineage and binds source IDs/vintages
to the reviewed profile constants.

The two output Parquets contain 554 observation rows and four exact-source
coverage groups: CPI has 449 rows (422 admitted, 27 excluded missing values);
QES has nine context observations; GDP has 60 current-price observations; and
population has 36 rows (33 admitted, one unavailable and two excluded because
their status is not retained in the shared fact schema). The report records
exact input record IDs, source locators, period tokens, values, units, bases,
status and reason-coded admission. It does not combine periods or vintages.

The package is context-only. CPI base approval, GDP currency qualification,
population status/vintage/denominator approval, all rights decisions, and any
annualization, deflation, denominator or cross-series measure remain open.
Nothing is published. The read-only CLI supports dry-run by default; writing a
new local package requires the explicit `--write` flag.

## Verification

- Four focused tests pass, including repeat-build byte equality, persisted
  hashes/readback, status and missing-value exclusion, and tampered evidence
  rejection.
- Ruff and basedpyright pass for changed code; the CLI dry-run returned the
  expected 554 observations, four series, 524 eligible context values and 30
  exclusions.
- `./scripts/validate.sh` passed: 7,004 tests, 9 skipped, 98.05% branch
  coverage; 49 schemas/39 documents; parity 9/9; all configured mutation,
  hygiene, benchmark, audit, licence, secret-scan and 113-component SBOM gates.
- Output remains local validation only; source rights and publication are not
  asserted.
