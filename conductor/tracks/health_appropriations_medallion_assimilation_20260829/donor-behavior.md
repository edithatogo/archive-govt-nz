# Pinned donor behavior characterization

Source: `edithatogo/nz_health_appropriations` commit
`4668e6c3b1b492086941d4c1ef96e299250a8301`, re-observed 2026-08-30.
Files were read and compiled, not imported or executed. This characterizes
static intent and failure boundaries, not successful execution of every branch.
The original source files remain unchanged outside Git in the donor capture.

| Script | SHA-256 | Compile observation |
| --- | --- | --- |
| inspect_excel.py | `4a7892f96b2124a0a6af37e3be3eaa583c39feca8ad00d76eca3f4d837e1d02c` | Compiles |
| process_data.py | `0beb01bbf6956f6ed9f5925c73199dc0a67f6022673dba78fded819597d63ed3` | IndentationError at line 199 after duplicated if at line 198 |
| run_analysis.py | `eb004ba16b36976e679104b68c5fc6a3fd491b792babeba1c1511a25ee705d6e` | Compiles |

## Inspection

`get_sheet_names` lists worksheets; `print_sheet_head` reads a sheet without
headers and prints its first rows. Both catch broad exceptions and print them
instead of propagating a structured failure. Two main blocks execute when run
as a script. Replacement inventory must be non-mutating and machine-readable;
its successful structural census is not evidence of complete extraction.

## Processing

The compile failure prevents all runtime processing, including directory
creation. Merely repairing indentation would expose these further risks:

- Historical spending uses fixed columns B/H, starts at row 5, truncates using
  text/blank heuristics, coerces bad values away, discards amounts below one and
  keeps only the first duplicate year.
- Recent expenditure selects exact Vote `Health`, tolerates missing expected
  columns, coerces and drops invalid amount/year rows, and truncates years to
  integers. It normally replaces the destination table.
- Functional summaries select the first row containing three year-like values
  and the first subsequent label containing `Health`. They may confuse repeated
  blocks or labels and discard unparsable/missing observations.
- GDP uses B/C positional extraction, stops on a blank pair, drops values below
  one and keeps the first year duplicate.
- Processing and table writes catch broad exceptions and print them. A final
  completion message would not prove every intended table was rebuilt.

The checked-in SQLite database is an observed derivative, not evidence that
this broken script generated it. Retain it as a parity oracle, never substitute
it for the original workbooks or silently repair it.

## Analysis

Four functions implement nominal spending/growth, GDP share, appropriation
breakdowns, and classification trends. They catch broad exceptions and return
early on absent data. GDP uses an inner year join without an explicit zero
denominator check. Breakdowns prefer 2025 Main Estimates, then fall back to the
latest Actuals/Estimated Actual row without a declared tie-break policy.
Department plots are conditional on multiple departments; classification plots
depend on exact labels. Output directory creation occurs at import time, and
plot saving overwrites matching filenames. Nominal growth across a missing year
would not necessarily represent a one-year change.

Replacement analytics require explicit year/amount-type selection, denominator
and gap checks, semantic plot contracts, structured failures and separately
identified products. Existing Gold parity does not close these broader risks.

## First raw-source extraction target

`data/raw/b25-expenditure-data.xlsx` has SHA-256
`d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338`.
Its `Raw Data` sheet contains 17 named columns and 6,504 data rows, including
215 exact Vote Health rows. A read-only named-column comparison reproduced all
seven donor-table fields in order. This is a bounded parity observation, not
complete normalization of the workbook's other worksheets or all fiscal data.
