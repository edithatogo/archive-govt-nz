# Budget 2026 Estimates workbook source profile

The Treasury's [Budget 2026 Estimates data release](https://www.treasury.govt.nz/publications/data/budget-2026-data-estimates-appropriations-2026-27)
publishes separate expenditure and Crown revenue/capital-receipts workbooks for
the Estimates of Appropriations 2026/27. The source census captures the
expenditure workbook as `budget_2026-000` at
`https://budget.govt.nz/budget/excel/data/b26-expenditure-data.xlsx`, SHA-256
`3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0`.

The Treasury release describes the workbook's reporting years as actuals for
the years ended 30 June 2022–2025, estimated actual for the year ending 30 June
2026, and budget for the year ending 30 June 2027. It says the workbooks are
based on Crown Financial Information System data, exclude the 2025/26
Supplementary Estimates, and do not restate pre-2026/27 data for later agency
restructuring. Thus earlier-year amounts are source-vintage observations, not a
continuous restated appropriation series. The release says 2026/27 data should
match the Estimates exactly; the tabled Estimates remain the official source.

The source page declares Crown Copyright, Attribution 4.0 International
(CC BY 4.0). This is a recorded publisher statement, not an independent legal
assessment or derivative-release approval. The captured workbook has since
been extracted and independently reconciled against literal OOXML cell values.
`Raw Data` has 6,451 source rows; the bounded Vote Health projection selects
185 facts and accounts for all other 6,266 rows as out of scope, with no
rejected rows. The selected facts have these source amount-type counts:

| Year | Source amount type | Selected facts |
| ---: | --- | ---: |
| 2022 | Actuals | 61 |
| 2023 | Actuals | 25 |
| 2024 | Actuals | 24 |
| 2025 | Actuals | 24 |
| 2026 | Estimated Actual | 25 |
| 2027 | Main Estimates | 26 |

`Amount $000` is retained as `NZD_thousands`; every selected fact has its 17
source columns linked through cell lineage. These counts describe this
workbook's selected Vote Health rows, not complete Vote Health coverage across
agencies, supplementary estimates, or years. In particular, the release
excludes 2025/26 Supplementary Estimates and warns that pre-2026/27 data are
not restated for later agency restructuring. Row-level exposure to that
restructuring cannot be determined from the published workbook profile alone.
Financial-year start/basis remains unverified in the canonical facts, and the
2026/27 Estimates tables remain the official source. See
`raw-budget-successors.md` for the extraction receipt and independent
reconciliation. This closes the workbook-native unit and bounded row-count
inspection for this captured expenditure workbook; it does not establish
complete annual appropriation coverage or analytical admission.

This profile closes the public release's headline period and revision-boundary
census for this one workbook. It does not close annual Budget source discovery,
Vote Health/Supplementary Estimates reconciliation, rights review, or
analytical admission.
