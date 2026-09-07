# Donor parity checkpoint acceptance

This bounded checkpoint is based on the protected integration chain through
PR #429. It records evidence already produced by the repository tests and
receipts; it does not create or alter source payloads.

The donor-compatible lane retains all five SQLite tables and 312 donor rows,
with source-specific values and repair differences represented in the existing
repair ledger. The functional lane has tests for the four analysis families,
the six plot contracts, deterministic rebuilds and unsupported layouts. The
newer health integration batches additionally preserve the 160 donor-detail
observations, 69 revenue facts, 108 chart/context admissions and their native
lineage, but these are not silently substituted for the donor's 312-row parity
population.

PR #429 merged at 2026-09-07T07:09:35Z as
`33dcc5504e597a907003095933b7a508c8f39e82`; reviewed head
`488879677672ee9fa747d4b25fa73c2a521b40d4`. Its exact-head hosted checks passed
on Linux, macOS and Windows, with CodeQL, lint and patch coverage also passing.
The supplemental job was skipped. The combined local gate at the reviewed
integration head passed 6,517 tests, 98.0441% coverage and all configured
schema, differential, mutation, hygiene and supply-chain checks.

This accepts only the named parity-suite execution and reproducibility evidence.
It does not approve the 29 source-only restorations or the precision difference,
claim every workbook area is normalized, establish pixel-identical plots, select
Gold denominators, clear source rights, authorize publication, or complete the
health track. The track remains in progress.
