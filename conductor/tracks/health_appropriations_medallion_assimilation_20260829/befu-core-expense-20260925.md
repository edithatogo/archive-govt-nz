# BEFU 2026 core Crown expense checkpoint

This checkpoint records one bounded Silver extraction from the retained
Treasury BEFU 2026 expense workbook. It does not promote the values into Gold or
establish a Crown share measure.

## Source and layout evidence

- Official source: `https://budget.govt.nz/budget/excel/befu2026/befu26-data-expense-tables.xlsx`
- Vintage: `BEFU-2026`; source ID: `befu_2026-003`.
- Bronze SHA-256: `313ee040abd9a332cc36245da5a0c2cb0d38fe2cedc013d731c1f12db463b0d1` (193,830 bytes); independently recomputed from the retained CAS object.
- Observation timestamp: `2026-08-29T09:00:17Z`, bound from the source census record.
- Workbook sheet: `Core Crown Expense Tables`; label `D26` is `Core Crown expenses`; unit `D6` is `($millions)`.
- Years in `F5:O5`: 2021–2030. `F6:J6` are Actual and `K6:O6` Forecast. `F26:O26` hold `SUM(column8:column24)` formulas with numeric stored caches. The adapter reads formulas and caches separately and does not recalculate.
- The formula-cache inventory independently reports stored numeric values at all ten selected coordinates. The workbook also contains 390 other formulas outside this profile; they remain preserved-only.

## Local result

The exact profile `befu-core-2026/v1` produced 10 `fiscal_context_fact` rows,
60 lineage fields, 24 context cells and 2,341 preserved-only cells. No cells
were rejected. The output package is retained outside Git at
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/silver/raw-befu-core-expense-20260925-v1`.
Its manifest reports status `passed` and binds the source hash, locator,
vintage, transformation, three Parquet output hashes, and workbook inventory.
Rights remain `not_evaluated` for the derivative.

The ten source cache values, in year order, are 107764, 125641, 127574, 138998,
141675, 147239, 154823, 158788, 162767, and 167892 (millions as labelled by
the workbook). They are observations of stored formula caches, not assertions
that the caches are fresh or that the formulas were recalculated by this
pipeline.

## Limits and next gates

The workbook text does not resolve currency, financial-year date boundaries,
or cache freshness. All are marked unverified in each fact and the manifest.
These totals are fiscal context only; they are not Health expenditure and are
not suitable for a Crown-share denominator until those semantics, vintage
alignment and any required approval are independently established. Historical
GDP/Crown series and other BEFU/HYEFU vintages are not covered.

The focused adapter tests pass (4 tests); repository validation and hosted
checks are recorded with the implementation PR, not claimed by this local
checkpoint.
