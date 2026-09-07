# HYEFU 2024 operating-allowance literals — 2026-09-07

Separate local slice based on integrated G `3403365ecd3cb79fb0f771b2228be4ffa8f1d114`,
including the parent's detail-test typing fix. No shared lifecycle edits.

## Exact profile and semantics

Retained donor original `data/raw/hyefu24-charts-data.xlsx`, 1,311,850 bytes,
SHA-256 `f77bdab5ef808b0e451a52b9b448a52b07899bc4523da3c02aa5725325d6203c`.
Existing CAS root: `/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/sha256`.
This is donor-byte replay, not a new source capture or current-endpoint claim.

Table 2.4 selects **16 literal amounts** at C6:F8 and C10:F10. Exact context:

| Coordinate | Source text |
| --- | --- |
| B1 | Table 2.4 - Future budget operating allowances |
| B2 | Source: The Treasury |
| B4 | Year ending 30 June |
| B5 | $millions (average per annum) |
| C5:F5 | Budget 2025; Budget 2026; Budget 2027; Budget 2028 |
| B6 | Announced Budget operating allowance |
| B7 | Pre-commitments |
| B8 | Non-discretionary spending |
| B10 | Remaining unallocated future operating allowances |

All 12 populated non-selected context cells are preserved with coordinates.
The pinned table has no additional populated footnote cells. Six field lineage
references per record retain amount, label, budget label, unit, period context
and table title: **96 references**. Number format and exact XML numeric token
are preserved separately from decoded context.

`average per annum` is retained verbatim: these are not asserted yearly totals,
nor individual financial-year expenditure facts. Budget labels are not turned
into fabricated period bounds. Remaining-unallocated cells are published
literals, not recomputed residuals. No multiplication, subtraction, aggregation,
currency inference, BEFU/HYEFU equivalence or rights inference occurs.

## Implementation and safety

`hyefu_allowance_literals.admit_hyefu_allowances(path)` returns raw/context
records in memory only. It reuses verified snapshot, bounded inventory, exact
decimal conversion and the chart module's selected-worksheet XML reader.
The latter now accepts an explicit `selected_sheets` keyword; its default BEFU
selection and public BEFU entry point remain unchanged. No global profile
mutation, new adapter, dependency, payload or output writer is introduced.

Pinned hash precedes parsing; direct symlinks/missing files are rejected.
Header/unit/label drift, blank amounts and formulas fail closed. Selected
worksheet relationship/duplicate and DTD guards remain in the reused reader.

## Validation and real replay

- TDD: new tests initially failed import because the module did not exist.
- 48 focused tests passed: 7 new allowance tests, 14 chart regressions and
  the parent's 27 corrected detail tests.
- Mutation runs: chart reader/module 27/27 killed; new allowance module
  separately 12/12 killed. Cold unfiltered runs, zero survivors/cache hits.
  Repeated `--gremlin-targets` selected the last target in the first run;
  the new module was therefore explicitly rerun as a separate target.
- Ruff check/format passed for changed Python files.
- Full repository typing passed: zero errors, warnings or notes using
  `/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/basedpyright --threads 4
  --pythonpath /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python`.
  No full test harness was run.
- Actual retained-byte replay independently parsed OOXML workbook relationships,
  selected sheet cells and shared strings. All 16 literal tokens and all 12
  context values per record matched; selected inputs contained no formulas.
  Repeated admissions were identical and original bytes stayed unchanged.
- Canonical `encode_json(result)` SHA-256:
  `b0a56475bed1bd79efa064afb17bf698c07713ce0459962a81931b30ac2f654f`.

Focused tests use `PYTHONPATH=src` and the same `.venv/bin/python -m pytest`
with `test_hyefu_allowance_literals.py`, `test_befu_chart_literals.py`, and
`test_donor_health_detail.py` under `tests/domains/health_appropriations/`.
Mutation flags: `--gremlins --gremlin-targets=<one module> --gremlin-report=json
--gremlin-workers=2 --gremlin-no-coverage-filter --strict-pardons --max-pardons=0
--no-cov -q`. Synthetic test fixtures are not claimed as original replay.

## Parent disposition

Proposed clause: **HYEFU-2024 Table 2.4 literal raw/context admission complete:
16 average-per-annum allowance observations; no annual-total interpretation,
analytical arithmetic or cross-vintage equivalence.**

This slice adds 16 local records, not 16 pages/tables or 16 canonical facts.
Previously reported 86 BEFU literals remain a separate source/vintage cohort;
no revenue-worker progress is added to this ledger. Other chart/PDF areas are
unchanged and no further area is started. Conductor implement/review guided
TDD, bounded self-review and this dedicated evidence receipt.
