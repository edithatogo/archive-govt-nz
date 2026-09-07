# Six remaining explicit Health chart literals — 2026-09-07

Dedicated raw/context slice only. No new chart area or PDF work, arithmetic,
formula-cache admission, general-government extraction or analytical equivalence.
API: `health_chart_residual_literals.admit_health_chart_residuals(path, vintage)`.

## Exact profiles

| Vintage | Retained source SHA-256 | Sheet and selection | Semantics |
| --- | --- | --- | --- |
| BEFU-2025 | cf98f5e21f60c76c7d05f788df7955fb45cfdd780c12cb18e26ff8e83615e168 | Data 2.12!C8 | Health net capital spending; period unknown |
| HYEFU-2024 | f77bdab5ef808b0e451a52b9b448a52b07899bc4523da3c02aa5725325d6203c | Table 2.10!D14:H14 | Health NZ contribution to OBEGALx movements, not Health spending |

Existing CAS root: `/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/sha256`.
Donor locators are `data/raw/befu25-charts-data.xlsx` (1,909,842 bytes) and
`data/raw/hyefu24-charts-data.xlsx` (1,311,850 bytes). No fresh acquisition,
endpoint verification, payload in Git, publication or rights inference.

### BEFU: one literal, six context cells

- B1: `Figure 2.12: Breakdown of total core Crown net capital spending`.
- B2: `Source: The Treasury`.
- B4: `Net capital spending`.
- B5: `Area`; C5: `$millions`; B8: `Health`.

The worksheet provides no period for C8. The record explicitly returns
`unknown_no_period_on_source_sheet`, empty column headers and null period bounds.
It does not infer a forecast horizon from BEFU-2025, a neighbouring figure or
the capital-decisions tables. ISO currency remains null.

### HYEFU: five literals, fifteen context cells

- B1: `Table 2.10 - Movements in OBEGALx since the Budget Update`.
- B2: `Source: The Treasury`; B5: `Year ending 30 June`; B6: `$billions`.
- B14: `Health NZ results`.
- D5:G5: 2025, 2026, 2027, 2028; D6:G6: `Forecast`.
- H5: `Total`; H6: `change`.

The measure is explicitly `health_nz_obegalx_movement_not_spending`.
Four Forecast columns and the literal Total/change column remain distinguishable.
No total is calculated, reconciled or netted. Original period context is retained
without creating projected period bounds; currency remains null. Zero and
negative amounts retain their source signs and exact XML numeric tokens.

## Preservation and validation

Every record preserves the exact numeric token, source number format and all
reviewed context coordinates. Lineage references include amount and each
context cell: 7 for BEFU, 16 per HYEFU record, **87 references total**.
Only the semantic anchors listed above enter context; unrelated fiscal rows
are neither admitted nor silently treated as Health data. The earlier complete
worksheet audit found no footnote applying to either selected row. The selected
headers and amounts are literal; no formula resolver or data-only workbook is
used.

Reuses unchanged bounded chart `_selected_tokens`, verified snapshot, workbook
inventory and exact-decimal helpers. Full-source SHA pins precede parsing.
Unapproved vintage, missing/symlink source, unit/label/header drift and
formula/blank selected inputs fail closed. Originals are never written.

- TDD red: the new test initially failed import because the module was absent.
- 33 focused tests passed: 12 new residual tests, 14 existing BEFU chart tests,
  seven HYEFU allowance tests.
- New-module mutation: 12/12 killed, zero survivors; cold, unfiltered run.
- Ruff check/format passed.
- Full correct-runtime typing: zero errors, warnings or notes with
  `/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/basedpyright --threads 4
  --pythonpath /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python`.
- No full harness. No edits to parent detail tests or shared lifecycle files.

Actual replay read both retained originals, checked SHA-256, independently
parsed the OOXML workbook relationships, selected worksheet cells and shared
strings. All six numeric tokens and all six/fifteen context values matched;
selected cells and context had no formula nodes. Repeat admissions were
identical and original bytes remained unchanged. Canonical result digests:

- BEFU: `b4b1e9fe13d2e5a37234b280a88aeae731482065d44ef3140f10a4da7ff67f4e`.
- HYEFU: `8ffb2c29bf6c44e6816ede0860b333d4cc32f1c40190ea247c6ff86453be5e36`.

Focused tests use `PYTHONPATH=src` and the correct `.venv/bin/python -m pytest`
on `test_health_chart_residual_literals.py`, `test_befu_chart_literals.py`,
and `test_hyefu_allowance_literals.py` under `tests/domains/health_appropriations/`.
Mutation uses only the new test file, with `--gremlins
--gremlin-targets=src/archive_govt_nz/domains/health_appropriations/health_chart_residual_literals.py
--gremlin-report=json --gremlin-workers=2 --gremlin-no-coverage-filter
--strict-pardons --max-pardons=0 --no-cov -q`. Synthetic fixtures are not replay.

## Parent disposition

Proposed clause: **Six remaining explicitly Health-labelled donor chart literals
admitted as raw/context records; BEFU period remains unknown, HYEFU observations
remain OBEGALx movements, not spending.** Adds six records only. Previous BEFU86,
HYEFU16 and detail160 cohorts remain distinct. Formula totals and PDF numerical
qualification are not closed or counted by this slice.

Conductor implement/review guided the TDD, source-bound checks and scoped
self-review. No further area started.
