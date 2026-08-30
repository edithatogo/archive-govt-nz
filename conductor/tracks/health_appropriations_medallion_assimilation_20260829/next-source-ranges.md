# Next raw-source ranges — observed 2026-08-30

These observations come from read-only XML inspection of the pinned donor
workbooks, not formula execution or a completed extraction adapter. Retain
these distinctions when adding the remaining 97 donor-oracle rows. Source
coverage can legitimately exceed the oracle; never discard originals or
unmatched rows simply to force parity.

## BEFU 2025 and HYEFU 2024

| Source | SHA-256 | Sheet | Year labels | Amount type | Health summary |
| --- | --- | --- | --- | --- | --- |
| `befu25-data-expense-tables.xlsx` | `dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6` | `Core Crown Expense Tables` | F4:O4 | F5:O5 | F8:O8; D8 = Health |
| `hyefu24-data-expense-tables.xlsx` | `725399c09323594c921dbcc493206abe59bf7b91dd968b8c7f6f3a67d4707969` | `Expense Tables` | F3:O3 | F4:O4 | F7:O7; D7 = Health |

Both summaries contain literal amounts for 2020–2029, with Actual labels for
2020–2024 and Forecast for 2025–2029. Units are explicitly `$millions` at D5
(BEFU) and D4 (HYEFU). The donor oracle contains ten rows per workbook.

The later detailed Health expenses totals at F111:O111 (BEFU) and F112:O112
(HYEFU) are formulas with stored cached values. Do not confuse them with the
literal summary or silently use their caches as verified fresh results. The
detail includes classification and health-system-reform footnotes; retain and
link these to any detailed extraction. Validate semantic labels and contiguous
year/type ranges rather than trusting these coordinates across new vintages.

## Historical fiscal series

`fiscaltimeseries1972-2024.xlsx` SHA-256:
`769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d`.

The `Spending` sheet explicitly distinguishes:

- `$ millions` at A3, Health at H4, year labels in B and amounts in H;
- Cash, March Years beginning at A5;
- Cash, June Years at A23 (year label `1990†`);
- old-GAAP at A27 (`1994*`);
- IFRS, June Years at A30 (1997);
- PBE Standards, June Years at A38 (`2005^`); and
- a separate `% GDP` block beginning at A68, with its own repeated headers
  and periods. It must not be read as another currency block.

Footnotes distinguish GAAP backdating, GST inclusion, restatements and
cash-to-accrual transitions. Preserve annotated year labels and their footnote
links; do not simply discard non-numeric years. Some stored XML numbers expose
binary floating-point tails, requiring an explicit source-precision policy
before canonical fixed-decimal amounts are asserted.

The `Nominal GDP` sheet labels `$ millions` at A3, Nominal GDP at C3 and uses B
for years/C for values. Its period changes from March Years at A5 to June Years
at A23. Do not join these series on year alone without checking period and basis.

The observed SQLite oracle has 24 historical-health rows and 53 GDP rows, each
spanning 1972–2024. The health row count does not demonstrate complete annual
source coverage. The next adapter must report every unmatched/missing/annotated
year and justify differences, rather than reproduce the donor's lossy behavior.
