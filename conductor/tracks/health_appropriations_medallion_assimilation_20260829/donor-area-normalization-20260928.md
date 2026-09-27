# Donor workbook area normalization — 2026-09-28

This checkpoint closes the Phase 4.1 extraction-fixture and Phase 4.2
normalization clauses for the explicitly selected donor-functional data areas.
It does not claim that every one of the 152 inventoried workbook sheets is an
analytical table or has been semantically normalized. Those unrelated/support
tabs remain in the preserved originals and retain adapter-scoped exclusions or
remainder dispositions. The separate 158-unit structural census remains a
metadata-level unresolved inventory; this receipt does not convert it into a
global irrelevance decision.

## Normalized scope and retained-source replay

The seven XLSX objects in the pinned donor manifest were replayed through the
12-stage raw pipeline. The four core profiles retain the donor's 312-row
five-table oracle and restore the 29 footnote-marked Health years as separate
source observations. Additional stages normalize Budget revenue, detailed
BEFU/HYEFU Health classifications, chart/allowance/residual literals, and the
separately pinned Crown context area. Each stage now has a fixed expected fact
count in `rebuild_eight.EXPECTED_FACT_COUNTS`; the integrated completion check
fails closed if a source profile silently omits or adds facts.

| Stage | Source area | Facts | Lineage rows | Cell/row dispositions |
| --- | --- | ---: | ---: | ---: |
| budget | Budget-2025 expenditure Raw Data | 215 | 3,655 | 6,504 |
| befu | BEFU-2025 Health summary | 10 | 60 | 2,332 |
| hyefu | HYEFU-2024 Health summary | 10 | 60 | 2,333 |
| historical | Historical Health and nominal GDP | 106 | 1,143 | 1,503 |
| revenue | Budget-2025 revenue Raw Data | 69 | 1,104 | 1,000 |
| befu-detail | BEFU-2025 detailed Health classifications | 80 | 832 | 84 |
| hyefu-detail | HYEFU-2024 detailed Health classifications | 80 | 832 | 84 |
| befu-chart | BEFU-2025 selected chart tables | 86 | 3,054 | 167 |
| hyefu-allowance | HYEFU-2024 operating allowances | 16 | 288 | 73 |
| befu-residual | BEFU-2025 Health capital literal | 1 | 13 | 67 |
| hyefu-residual | HYEFU-2024 Health NZ movement literals | 5 | 155 | 62 |
| crown | separately pinned Fiscal-2025 contextual literals | 61 | 369 | 69 |

Each count is derived from the verified run manifest; per-reason counts,
source hashes, stage-manifest hashes, the file-hash map digest, donor pins and
the donor parity result are in
[`donor-area-normalization-20260928.json`](./donor-area-normalization-20260928.json).
Two clean builds produced identical manifests and all 50 output-file hashes.
Source payloads were read from the retained CAS and were not copied to Git.

The 23-object donor replay verified 6,604,301 bytes. All five donor SQLite
tables matched all 312 rows. Historical comparison remains 76 exact matches,
29 source-only annotated Health years and one decimal-token difference. The 30
differences retain the accepted source-backed `retain_both_observations`
dispositions; no replacement value, repair approval, rights determination or
publication approval was created.

## Workbook fixture coverage

The synthetic fixtures exercise layout and extraction boundaries independently
of the retained-source replay:

- Budget appropriation fixtures cover named-column reordering, repeated equal
  rows at distinct source coordinates, blanks, non-Health votes, footer rows,
  formula values, invalid numeric values, malformed/duplicate headers, units,
  hash binding and unsupported sheets.
- Historical fixtures cover Health and GDP series, exact numeric tokens,
  March/June periods, old-GAAP transition, footnote annotations, footnote
  context, non-selected percentage-of-GDP cells, blank/formula/error cells,
  missing or ambiguous labels and unsupported layouts.
- BEFU/HYEFU summary fixtures cover shifted layouts, Actual/Forecast headers,
  zero and negative amounts, blanks, formulas, spreadsheet errors, unknown
  units, non-contiguous years, ambiguous labels, footer/context rows and
  unsupported vintages.
- Detailed Health fixtures cover all 80 selected literal cells, multi-step
  header references, formula-backed total rows, source footnotes and rejected
  formulas, missing labels and wrong units/years/amount types.
- Budget revenue and chart/allowance/residual fixtures cover complete row or
  coordinate accounting, duplicate occurrences, exact amounts, literal
  headers/units, formula-cache exclusion, missing/blank selections, unsupported
  layouts, source hashes and repeat admissions.

Targeted fixtures added in this checkpoint are
`test_budget.py::test_footer_and_formula_rows_remain_explicitly_disposed`,
`test_donor_health_detail.py::test_admission`, and the integrated 739-fact
expected-count guard in `test_rebuild_eight.py`.

## Validation and boundaries

The 12-stage retained-source replay completed twice with identical output
hashes: 739 observations across 50 files. The donor row oracle verified all 23
objects and 312 donor rows. Donor, historical reconciliation, four analysis
families, compatibility export, Gold and six-plot contract/export suites passed
253 tests. The new focused fixture/orchestration selection passed 194 tests;
Ruff and strict basedpyright passed.

This normalization scope is the donor-functional set above, plus the explicitly
selected source/context literal areas that feed the existing analysis and chart
contracts. It is not normalization of every pivot, chart cache, forecast table,
unrelated fiscal series or the entire 152-sheet structural census. Formula
caches remain unadmitted; source-specific remainder and exclusion states stay
visible. Rights remain `not_evaluated`, Gold publication is `not_performed`,
and the 30 historical comparisons are not value repairs.
