# Pinned donor behavior characterization

## Current evidence and replacement conformance — 2026-08-31

Fresh full bytecode compilation (without import or execution) reproduces the
three observations below. Hashes were checked before and after; all 23 donor
objects also pass their manifest fixity checks. The machine-readable receipt is
`donor-script-observation-20260831.json`. Compilation success is not runtime
success, security isolation or evidence that a derivative came from this code.

The replacement regression mapping is deliberately bounded to donor-intended
Health/GDP/summary extraction and the four analysis families. Test names below
are in `tests/domains/health_appropriations/`; preservation of other workbook
areas does not imply they have been normalized.

| Observed donor risk | Receiver contract and executable evidence |
| --- | --- |
| Processor cannot compile | `test_rebuild.py::test_broken_donor_processor_is_preserved_but_not_a_runtime_dependency` retains a synthetic duplicate-if script while orchestration consumes only four original-workbook profiles. Adapters are stubbed in this orchestration test; separate real adapter and live rebuild evidence remains required. |
| Broad exceptions print errors or suggest completion | `test_rebuild.py::test_failure_preserves_partial_bytes_and_requires_new_run` requires redacted failure, preserved partial bytes and no completed manifest for both ValueError and RuntimeError. Inspection `test_selected_sheet_and_bounded_failures` rejects absent sheets/bad pins. |
| Budget positional assumptions and silent coercion/drop | `test_budget.py::test_named_headers_and_nonpositive_amounts` permits reordered named columns and retains zero/negative values; `test_bad_rows_are_disposed_not_silently_dropped` records rejected fractional years, malformed values, formulas and errors. |
| First Health/year-like summary can select a wrong block | `test_forecast.py::test_literal_summaries_have_semantic_layout_and_lineage` supports shifted layouts and exact lineage; `test_layout_drift_fails_before_output` rejects ambiguous labels/years/units. |
| Historical heuristics lose annotations, precision or values | `test_historical.py::test_exact_values_annotations_periods_and_rebuild` retains annotated years/context and exact numeric tokens; `test_unknown_layout_fails_without_outputs`, `test_ambiguous_context_rejected` and `test_nonpositive_source_values_preserved` bound accepted source layouts. This is not generic positional-layout support. |
| Missing-year/basis growth and unchecked GDP division | `test_historical_analysis.py::test_growth_breaks`, `test_denominator_gates`, `test_never_splice_source_or_vintage` and `test_duplicate_keys_or_ids_rejected` retain explicit unavailable comparisons and reject ambiguity. |
| Undeclared fallback/type mixing in breakdowns | `test_appropriation_analysis.py::test_exact_aggregation_and_explicit_breakdown` and `test_group_boundaries` use explicit year/type/source filters and preserve exact sums. |
| Import-time mkdir and destructive plot saving | Receiver inspection is read-only; `test_plot_export.py::test_preserved_output_and_input_boundaries` and `test_partial_failure_preserves_redacted_receipt` reject overwrite and retain failed bytes. The donor analysis script is never imported. |

All 253 selected inspection, rebuild, adapter and analytical tests passed after
adding the compile-independence regression. This is fresh focused evidence, not
an assertion that every legacy runtime branch was executed. Current CLI
readback independently verifies the retained four-stage raw run with manifest
`da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
It verifies existing bytes; it does not claim another fresh extraction.

Complete workbook/PDF data-area coverage, contextual datasets, partial-stage
resume, scheduling and publication remain separate pending tasks.

## Original static characterization

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
