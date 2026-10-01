# Pharmac canonical Gold promotion — 2026-10-01

The verified Pharmac CPB Silver projection now enters the shared canonical
Gold package as a separate product. The 14 source rows remain source-record
rows in `nominal_pharmaceutical_budget.parquet`; the adjacent lineage product
retains populated source-coordinate fields, and Gold drillthrough resolves all
eight source coordinates for each fact. The discrete display plots split the
pre- and post-2022 funding-holder regimes. Source financial-year tokens and the
published budget-allocation meaning are preserved.

This is a local analytical derivative only. Rights remain unevaluated, the
published allocation is not actual expenditure, the 2022 policy regimes are
not pooled, and no cross-source join or publication is performed. The clean
recovery receipt also records that classification drift, revision and
cross-source reports, remaining source adapters, and the complete Platinum
profile remain unbuilt; this subtask does not clear the parent track's final
release gate.

The exact-head clean-room replay confirmed Bronze unchanged and two identical
Gold builds. The receipt is
[`clean-room-recovery-20261001-pharmac-gold.json`](./clean-room-recovery-20261001-pharmac-gold.json),
SHA-256 `d94d20dff8df328bd3b1f3b14a7e12364bd21d5da2613a7598e514190fa7c91f`.

`./scripts/validate.sh` passed: 7,231 tests passed, 10 skipped, 98.26% branch
coverage against the configured 80% floor, 53 schemas and 43 representative
documents, 9/9 parity checks, all configured mutation lanes, secret scan, and
113-component SBOM validation. Automatic Conductor Phase 7 review passed with
receipt SHA-256
`fec6b9d8eb49689aefa79ba58e25946a2ec0be2c5ceefa2bb83999ef35df365f`.
