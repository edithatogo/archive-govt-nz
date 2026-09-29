# HYEFU 2025 core Crown expense checkpoint

## Source and extraction

The exact captured source is `hyefu_2025-006`, the Treasury workbook
`https://budget.govt.nz/budget/excel/hyefu2025/hyefu25-data-expense-tables.xlsx`.
Its 191,581 Bronze bytes rehash to
`f9f9190a69ce0a7c53b89d690d50170e2a6a457e6821afeb93edc08cef4b9c7d`; its
census observation is `2026-08-29T09:00:17Z`. In `Core Crown Expense Tables`,
D25 is `Core Crown expenses`, D5 is `($millions)`, years F4:O4 are 2021–2030,
and F5:O5 label 2021–2025 Actual and 2026–2030 Forecast. F25:O25 contain
column-specific `SUM(F7:F23)`-style formulas and stored numeric caches. The
adapter reads formula and cache workbooks separately and does not recalculate.

The retained Bronze source was replayed to a new external Silver package at
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/silver/raw-hyefu-core-expense-20260929-v1`.
It contains 10 facts, 60 source-lineage rows, 24 context cells, 2,312
preserved-only cells and zero rejected cells. Its manifest SHA-256 is
`8440d81f4cab378b47cba1e3de22b57f687571ea60f2e95728d179e7527847e3`.
The previous HYEFU-2024 forecast summary package remains distinct and intact.

## Canonical projection and limits

`hyefu_crown_expense_canonical_projection.py` rehashes Bronze, checks the exact
Silver manifest and product hashes, reparses Bronze, and requires every
regenerated Silver table to match before emitting 10 `fiscal_context_fact`
rows with 80 direct lineage rows. HYEFU-2025 remains its own forecast vintage;
there is no BEFU/HYEFU splice or comparison. Source year labels are tokens,
and the literal `($millions)` unit is preserved while currency remains null.
Cache freshness, financial-year boundaries, accounting basis and rights remain
unqualified. No denominator, Crown share, analytical comparison or publication
is produced.
