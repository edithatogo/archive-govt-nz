# Fiscal Health share query — 2026-10-04

The read-only `query_fiscal_health_shares` verifies a canonical historical
package and recomputes Crown facts from its pinned original. It derives Health
spending shares of GDP, Core Crown expenses and Total Crown expenses from the
single Fiscal-Time-Series-1972-2025 workbook, SHA-256
`de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f`.

## Qualified definitions

[Treasury's explanatory notes](https://www.treasury.govt.nz/publications/information-release/data-fiscal-time-series-historical-fiscal-indicators)
define March fiscal years as April–March and June years as July–June. The
workbook labels identify the 1990 transition, cash accounting before 1994,
old-GAAP expenses for 1994–1996, IFRS from 1997, and PBE from 2005. The query
retains each basis and does not compute growth across these breaks.

The retained workbook headers are `Spending!A3` and `Nominal GDP!A3` for the
shared dollar-million scale; `Spending!H4` for Health; `Spending!G3` for Core
Crown expense classes; `Spending!D4/E4` for Core/Total Crown expenses; and
`Nominal GDP!C3` for nominal GDP. Common currency scale cancels in the ratio;
this does not independently qualify an ISO currency or enable currency joins.
The Total Crown ratio uses the Core Crown Health functional numerator, not a
new estimate of Health spending across all Crown entities. The pre-1994 cash
Health numerator has a separate coverage label. Source quality flags and year
annotations remain available on every output, together with exact amounts and
input canonical IDs. Source packages remain required for full field lineage.

## Replay evidence

`fiscal-health-shares-20261004.json` records two fresh Bronze-to-raw-Silver,
canonical and query rebuilds. Both emitted the same 162-row Parquet bytes:
54 GDP shares, 32 Core Crown shares, 29 Total Crown shares and 47 explicit
missing-denominator rows. All 115 percentages matched an independent exact
rational calculation rounded half-even to 12 decimal places. The original
Bronze digest remained unchanged. A typed Parquet readback also matched.

The retained product is outside Git at
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/gold/fiscal-health-shares-20261004-v3`.
It is a local analytical query product; integration into the canonical Gold
exporter, CLI/MCP and plots remains a next task. CPI, wages and population are
not joined. Rights and publication remain unevaluated/unperformed.

The metadata observation is preserved externally with its hash in the receipt.
Direct HTTP retrieval of the explanatory page returned 403; a retained web-tool
text observation supports the period review, without an original HTML-capture
claim. The initial readback found a list-child-name transport mismatch; the
schema now uses Parquet's explicit `element` name and repeated readback passed.

## Local checkout reconciliation

The primary checkout was reconciled to merged remote main after all 12 dirty
tracked/untracked files and staged/unstaged patches were saved and rehashed in
`/Volumes/PortableSSD/ArchiveGovtNZ/worktree-preservation/20261004T060953Z`.
Consumer-query and discovery-schema changes were already implemented upstream;
historical receipts and differing bookkeeping remain recoverable in that
snapshot. This change also removes the obsolete no-native-Crown-adapter gap
from the context register; period, currency and rights qualifications remain.

## PR review correction

The query now requires the retained Treasury period-definition observation as an explicit input and verifies its pinned SHA256 before deriving starts. Every row carries that evidence digest and the original numerator/denominator time-status labels. Source starts must remain null and match the expected source statuses; the source records are not rewritten. Changed or missing observation bytes fail closed. The retained observation is web-tool text, not original HTML.
