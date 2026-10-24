# Fiscal Gold source reconciliation — 5 October 2026

Extended the existing pinned Fiscal analytical reports product with a
machine-readable `reconciliation.json`. Each of the 54 nominal source
observations now links to its three GDP/Core Crown/Total Crown share facts, one
per-capita fact and one household-CPI benchmark fact. The row carries source
period, amount, accounting basis, source hash/vintage/status/coverage, exact
parent-equality control, denominator IDs and status, population IDs and source
identity, and CPI quarter IDs/statuses, period definitions, source identity and
formula metadata.

Missing denominator and population statuses stay explicit with null results.
The report retains source-separated metrics and does not calculate a health
input-cost deflator, ISO currency, cross-source comparison, or an aggregate
across overlapping periods and reporting bases. Rights remain unevaluated and
publication was not performed. Existing plots and structured summaries are
reused; no equivalent Gold package was rebuilt.

Two written builds from the same pinned Gold manifest produced byte-identical
13-file packages. The standalone verifier passed for all 12 payloads, with
byte-equal catalogue and provenance projections. An independent read of the
four pinned Arrow tables verified all 54 source rows, 162 share rows, 54
per-capita rows and 54 CPI rows. All 270 derived rows passed exact parent
amount and identity checks, and all 54 nominal rows passed source amount and
metadata checks. Existing plot coverage remains 257 plotted points and 67
explicitly excluded points. The pinned source package was not modified.

See `fiscal-gold-source-reconciliation-20261005.json` for hashes and retained
external evidence location. This closes only the bounded reconciliation report
slice; broader Phase 6 donor/cross-source controls, other Gold products, and the
final track review remain open.
