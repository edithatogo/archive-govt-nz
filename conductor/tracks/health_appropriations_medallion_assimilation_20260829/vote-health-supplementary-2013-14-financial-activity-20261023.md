# Vote Health Supplementary Estimates financial activity — 2013/14

The retained Treasury PDF is pinned by SHA-256
`1ec8cf9e4c33d027f3ed02593ab3e8c7cab89883d5b286e0cf4aa4b1e947f5a2` and has
44 pages. The separately registered profile reads only PDF page 7,
“Summary of Financial Activity”. It preserves fourteen source rows across
Appropriations and Crown Revenue and Capital Receipts, five printed `$000`
columns, literal dash/`N/A` tokens and all 70 field-lineage coordinates.
Repeated `Output Expenses`, `Other Expenses` and `Capital Expenditure` labels
under the MCA heading retain distinct source-order identity.

Two independent builds from the Bronze CAS object produced identical Parquet
and manifest digests. The persistent Silver package at
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/silver/vote-health-supplementary-2013-14-financial-activity-20261023-v1`
matches both builds; Bronze remains unchanged. A source-operation dry-run
returns the same 14 facts, 70 lineage rows and one page disposition.

Evidence reconciliation found that the older
`vote-health-supplementary-2013-14-category-totals-20261006.json` reports
91,611 bytes for this same source hash. The official capture manifest and live
CAS object both report 470,538 bytes, and the CAS payload rehashes to the pinned
SHA-256. The older receipt is preserved; this record uses the verified length.

The capture manifest's Treasury CC BY notice is not a derivative-level rights
approval. Fact rights remain `not_evaluated`; currency, annual bounds,
cross-edition comparability, canonical/Gold admission and publication remain
unqualified. The repository lock now uses DuckDB 2.0.0, and full validation on
CPython 3.15.1 passes 8,309 tests with 14 skips and 97.17% coverage, plus all
schema, parity, mutation and supply-chain gates. Focused repeat-build tests
also pass; see the machine receipt and run log. Protected hosted delivery
remains pending.
