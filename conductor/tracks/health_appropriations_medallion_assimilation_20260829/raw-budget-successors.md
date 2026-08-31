# Budget successor extraction and verification

## Scope

Budget 2026 is a separate source vintage, not a replacement for Budget 2025.
The already-captured original remains in Bronze. The pilot reuses the existing
named-column adapter after inspecting the actual 17-column header contract;
it does not enable a generic unknown-layout or revenue adapter.

Original SHA-256:
`3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0`.
Source: `https://budget.govt.nz/budget/excel/data/b26-expenditure-data.xlsx`.
The retained capture receipt records 918,842 bytes and WARC SHA-256
`94a9637ed1c1e363a5a0a0cab84268343982ae11fbba92c55cb3f20cd579ea55`.
This turn did not reacquire the source or independently re-audit that WARC.

## Local pilot receipt

Retained directory: `silver/raw-budget-2026-20260831-v1` beneath the external
Health archive. The four-file manifest SHA-256 is
`f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738`.

| Observation | Result |
| --- | ---: |
| Input rows accounted for | 6,451 |
| Selected Health facts | 185 |
| Non-Health rows preserved with out-of-scope disposition | 6,266 |
| Rejected rows | 0 |
| Source-cell lineage entries | 3,145 |
| Original columns linked per selected row | 17 |

Values cover Actuals 2022-2025, Estimated Actual 2026 and Main Estimates 2027.
Amount types, source labels and NZD-thousands units are retained; fiscal period
starts remain unknown and `financial_year_basis_unverified` is kept. Timestamp
`2026-08-31T05:50:00Z` is fixed local reproducibility context, not original HTTP
capture time.

Two independent builds match every file. An independent literal OOXML
comparison, separate from openpyxl extraction, reconciles every selected amount
and year exactly, all selected labels and all 3,145 lineage coordinates. Every
input row has a disposition. Original SHA-256 remains unchanged before/after.

Output SHA-256 values:

- `budget_facts.parquet`: `42781cb2723f9b1b32a536a46389b0c5a54431d9c600380c6058e740a96b6f9f`
- `field_lineage.parquet`: `917e14e0de9d5fc3f7c56d14da9cc103031aa475e59157da46824d63c06c9a4b`
- `row_dispositions.parquet`: `e4bad4ad0a92b80257526fddcf4d7b7e665d1eddee90cedf6706977e65260b0f`

## Versioned regression and consumer boundary

Synthetic Budget-2025/Budget-2026 full-layout fixtures exercise exact amounts,
zero/negative corrections, all-cell lineage, deterministic rebuild and source
preservation. Combined analysis keeps overlapping years, amount types and
vintages separate; a later Actual does not overwrite an earlier estimate.
Three tests pass. Invented fixture values are not copied source rows.

A bounded verified Budget-package reader is being added to consume these
packages without treating the fixed four-profile raw-run wrapper as a universal
source registry. Reader assurance and live readback remain separate acceptance
steps; the pilot alone does not complete multi-vintage archival operation.

## Remaining boundaries

The capture manifest records resource-level Treasury licence evidence; new
facts still have `rights_state=not_evaluated`. No implicit rights promotion or
Hugging Face upload occurs. Future publication must join exact source rights
evidence and receive exact-candidate approval.

Seven other sheets remain inventoried and excluded from this narrow Raw Data
Health selection. Revenue workbooks, other Budget years, remaining fiscal
sources and complete in-scope data-area normalization remain pending. Captured
HLFS working-age population is not a national-total denominator; unqualified
per-capita measures remain unavailable until a suitable, temporally aligned
population series is selected.
