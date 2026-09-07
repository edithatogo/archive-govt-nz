# Donor chart tables and PDF structural-unit audit — 2026-09-07

Dedicated source/context receipt only; no shared lifecycle changes. Implements
`befu_chart_literals.admit_befu_chart_literals(path)` with no output files,
capture, publication, cache admission, arithmetic or analytical total netting.

## Source identity

Manifest: existing external `manifests/donor-4668e6c.json`, donor commit
`4668e6c3b1b492086941d4c1ef96e299250a8301`. Verified original CAS bytes under
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/sha256`:

| Donor path (under data/raw) | SHA-256 | Bytes |
| --- | --- | --- |
| befu25-charts-data.xlsx | cf98f5e21f60c76c7d05f788df7955fb45cfdd780c12cb18e26ff8e83615e168 | 1909842 |
| hyefu24-charts-data.xlsx | f77bdab5ef808b0e451a52b9b448a52b07899bc4523da3c02aa5725325d6203c | 1311850 |
| historical_appropriations/appropriation-main-estimates-2024-25.pdf | 620ff6a34e7be955ce70316af8f6fa4a9ca95689fa5036e076b50c13431d1fa8 | 1339480 |

This is donor-original replay, not verification of new official endpoints or
current source versions. No source payload is committed.

## Selected smallest coherent literal profile

| BEFU table | Admission | Exclusion | Meaning retained |
| --- | --- | --- | --- |
| 2.4 | D7:I17: 66 literals | None in selected numeric block | Budget 2025 expenditure decisions; five Forecast columns 2025–2029 and distinct published 5-year Total |
| 2.5 | D7:E12 and D14:E14: 14 literals | F7:F15, D13:E13, D15:E15: 13 formulas | Capital decisions; 5-year Total distinct from Post/2029; no inferred annual allocation |
| 2.8 | C6:D6, C8:D9: 6 literals | C11:D11: 2 formulas | Budget 2026 allowances and pre-commitments, Operating distinct from Capital |

Source `Year ending 30 June`, `$millions`, original row/column labels, notes,
number formats and exact XML numeric tokens remain attached. No dollar-to-ISO
currency inference. Labels retain whitespace and footnote markers. Complete
non-selected populated table context includes decoded formula strings, but not
cache values. Shared-formula strings may be expanded by openpyxl; these are
decoded context, not claims of literal OOXML formula text or evaluated results.

Every record has five field-coordinate lineage references. Published literal
totals are admitted as their own source observations, not recomputed or added to
components. Defence pre-commitment precision is retained, not rounded.
Capital and operating allowances are not recast as Health expenditure.

Existing adapters cover budget raw data, literal expense summaries and fiscal
series, not these chart tables. Reuse: verified snapshot, bounded workbook
inventory, DTD-rejecting XML reader and exact-decimal conversion. The historical
whole-workbook token helper rejects chart-sheet relationships; a bounded
selected-worksheet lexical reader is needed here. It skips unrelated chart
parts, rejects duplicate selected sheets/relationships/cells/values and external
or unsafe selected worksheet targets. Full-source hash pin prevents applying
these coordinates to another vintage. No shared adapter was edited.

## Remaining chart table census

BEFU has 109 sheet names and 20 Table worksheets; HYEFU has 97 sheet names and
15 Table worksheets. The following are **populated numeric-cell/formula-cell
counts**, not qualified fact counts: numeric year headers and note markers can
be included. Figure/Data sheets, Index and time-series sheets are outside this
table census and remain unqualified here.

| Table | BEFU numeric/formula | HYEFU numeric/formula |
| --- | --- | --- |
| 1 | 36/0 | 35/0 |
| 1.1 | 198/0 | 198/0 |
| 1.2 | 18/0 | 114/0 |
| 1.3 | 114/0 | absent |
| 2.1 | 182/0 | 186/0 |
| 2.2 | 68/0 | 80/0 |
| 2.3 | 30/0 | 9/0 |
| 2.4 | 71/0 | 16/0 |
| 2.5 | 14/13 | 30/0 |
| 2.6 | 60/20 | 48/0 |
| 2.7 | 8/1 | 60/0 |
| 2.8 | 6/2 | 36/0 |
| 2.9 | 22/14 | 47/0 |
| 2.10 | 36/12 | 52/0 |
| 2.11 | 42/18 | 37/1 |
| 2.12 | 60/9 | absent |
| 2.13 | 45/12 | absent |
| 2.14 | 30/17 | absent |
| 2.15 | 35/0 | absent |
| 4.1 | 55/0 | 60/0 |

Three BEFU table literal profiles now covered, **32 other Table worksheets
not qualified by this slice**. HYEFU table numbers do not mean the same thing:
2.4 is future operating allowances (16 literal amounts; explicit average per
annum unit), 2.5 is OBEGAL/OBEGALx reconciliation, 2.8 is borrowing. The simplest
next independent profile is HYEFU 2.4 C6:F8 and C10:F10, retaining each Budget
column and its average-per-annum unit; no cross-vintage allowance equivalence.
Other tables need their own semantic/range audit, not blanket admission from
numeric counts. HYEFU 2.11 includes an array formula in its title context.

## PDF disposition

The donor manifest contains one PDF: one `pdf_structure` accounting unit.
Existing `inventory_pdf` returns `page_count=471` by lexical page-marker regex.
Replayed that result and source fixity. This is **not a validated page-tree
count**, 471 extracted pages, table recognition, or numerical admission.
No page-layout/text/table extraction was performed; zero PDF facts admitted.
Next PDF work needs an explicit page-tree/layout/text qualification contract
before countable table/cell lineage. Structural preservation remains distinct
from data extraction. No guessed PDF amounts or OCR output were introduced.

## Count ledger and checks

- Earlier integrated detail: 160 records (user-reported integration).
- Earlier integrated Crown: 61 records (user-reported integration).
- Revenue: 69 in progress elsewhere, **not counted complete here**.
- This new local chart profile: 86 literal records, 430 field lineage links,
  15 formula exclusions; pending parent integration/review.
- These named cohorts total 307 delivered/local records excluding revenue;
  this is not a programme-wide unique-fact total or donor-coverage denominator.
- PDF: one structural unit, zero admitted facts.

TDD began red with missing module. Final focused tests: 14 passed; cold,
unfiltered mutants: 27 killed, zero survivors/cache hits. Ruff and module
Pyright passed. No full harness. Synthetic tests are not original replay.

Actual replay independently parsed selected OOXML worksheet parts through
workbook relationships: all 86 numeric tokens matched with no formula nodes;
all 15 excluded cells had formula nodes. A first replay comparison encountered
shared-formula nodes with no text, so verification correctly checks formula
presence, not equality to decoded expanded strings. Two admissions matched
deterministically and source bytes remained unchanged. Canonical result hash:
`8bcf1427b3151ddc296a43632ea5fa87e9ecb777bb439160008a864e9ec8a40b`.

Focused command: `PYTHONPATH=src python -m pytest
tests/domains/health_appropriations/test_befu_chart_literals.py -q`.
Mutation adds `--gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/befu_chart_literals.py
--gremlin-report=json --gremlin-workers=2 --gremlin-no-coverage-filter
--strict-pardons --max-pardons=0 --no-cov`.

Proposed parent clause: **BEFU-2025 Tables 2.4/2.5/2.8 literal raw/context
admission complete for 86 cells; formula results, other chart tables and PDF
data extraction remain separately pending.** Conductor implement/review guided
TDD, evidence boundaries and scoped self-review; no shared lifecycle edits.
