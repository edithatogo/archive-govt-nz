# Fiscal 2025 literal Crown admission

The source supports bounded literal raw/context admission: **32 core Crown
records (1994–2025) and 29 total Crown records (1997–2025)**. The dedicated
`admit_fiscal_crown(source)` function returns all 61 records in memory or raises;
it writes nothing and creates no canonical Silver/Gold package. This closes the
literal admission gap, not analytical equivalence, rights or publication.

## Source and reused contracts

The sole accepted original is SHA-256
`de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f`,
116,265 bytes, from the existing [Fiscal 1972–2025 download](https://budget.govt.nz/budget/excel/fiscal-time-series/fiscaltimeseries1972-2025-year-end25.xlsx).
Source vintage is `Fiscal-Time-Series-1972-2025`; the retained capture context
is `2026-08-29T09:00:17Z`, not a new retrieval or processing timestamp.

The existing historical adapter was audited first. It selects Health in H and
GDP in C, and its fact builder emits Health/GDP measure names and
`NZD_millions`. Reusing that builder for D/E would mislabel both measure and
currency. This small dedicated admission reader instead reuses its bounded
OOXML literal-number helper and exact Decimal representability validator,
plus existing workbook inventory, verified snapshots, context and identity
helpers. No dependency or shared adapter changed.

`fiscal-crown-literals.profile.json` was read from retained source metadata,
not populated from invented amounts. It pins the eight sheet names, Spending
geometry, headers, exact number format and 32 shared year labels. Synthetic
tests use this separate metadata observation rather than deriving expected
headers/year labels from the implementation under test.

## Exact selection and meaning

- Core: Spending D27:D58, label D4 `Core Crown Expenses`; 32 literals.
- Total: Spending E30:E58, label E4 `Total Crown Expenses`; 29 literals.
- A3 supplies `$ millions`. Amounts remain in those source units; scaling is
  labelled million but no multiplication or currency conversion occurs.
- June-year basis comes from A23, then A30/A38. Old-GAAP at A27 inherits the
  prior June-year marker, not the word Cash as its accounting basis. The
  regimes are old-GAAP 1994–1996, IFRS 1997–2004, PBE Standards 2005–2025.
- Year labels preserve `*`, `^` and `#`. Each applicable shared-year annotation
  retains its source note coordinate and exact text. A total-Crown-specific
  note is not applied to core Crown merely because the year column is shared.
- Currency and price basis remain null; amount type is
  `historical_as_published`, not an invented Actual flag. Period start remains
  null. Consolidation equivalence is `not_asserted`; rights remain
  `not_evaluated`.

Each record carries its original numeric token, exact Decimal amount, number
format, source hash/URL/vintage/observation, series label, year, period end,
accounting basis and field-coordinate lineage. Date lineage explicitly includes
both the year cell and period-basis cell. Raw context and year-note references
are returned beside the record; all unselected cells remain in the unchanged
original, not silently normalized. This is not an all-workbook disposition
package or an analytical consolidation model.

## Failure boundaries and corrected observations

Wrong hashes, direct source symlinks, missing sources, changed sheet/geometry,
labels, unit, period markers, year sequence/annotations, notes, pre-series
values, selected number formats, missing/text/error/formula cells, and
unsupported numeric precision fail closed. Numeric zero and signed values are
valid literals. No cached formula value can supply a selected literal token.
Forecast workbooks cannot pass the pinned original identity.

Real replay caught two transcription errors before completion: the percent-GDP
label is **A69**, while A68 is blank (earlier context notes said A68); the
publisher number-format string contains one literal backslash, not two. Both
are corrected in this new source-derived profile, with failures retained in
the validation receipt. No historical/shared context note was silently edited.
Neither correction changes the requested D27:D58/E30:E58 selections.

## Evidence and review

The red phase failed on the absent module. Focused admission and historical
helper suites now pass **51 tests**, with **100% of 73 statements and 12
branches** in the new module. Ruff lint/format and strict Pyright pass.
Cold, unfiltered mutation uses two workers: **35/35 killed**, no survivors,
timeouts, errors, pardons or cache hits.

Independent readback resolved the Spending worksheet via OOXML relationships,
shared strings, styles and literal value nodes, without using the new reader's
extraction helpers for comparison. It reconciled all **61 amounts**, **671
lineage references**, and **43 year-note references**, including exact formats,
year annotations and accounting boundaries. Original bytes stayed unchanged;
two reads returned equal results. Only metadata, counts and content hashes are
recorded in Git; neither raw values nor a derived fact payload was persisted.
The canonical in-memory fact digest is in the paired validation receipt.

Conductor implement/review guided TDD and scoped self-review. No remaining
source-fact blocker was found for this literal contract. Broader annual joins,
consolidation comparisons, ISO-currency evidence, forecast cache qualification,
canonical projections and publication remain separate. The earlier GDP/Crown
policy stays conservative and was not edited to auto-enable this new reader.

Proposed parent clause (no shared lifecycle edit):

> Admit the pinned Fiscal 2025 core/total Crown literal ranges with exact
> source tokens, units, labels, period/basis and field lineage, retaining
> unknown currency/price basis and unasserted consolidation equivalence.

## Focused reproduction

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_fiscal_crown_literals.py tests/domains/health_appropriations/test_historical.py -q --cov=archive_govt_nz.domains.health_appropriations.fiscal_crown_literals --cov-branch --cov-report=term-missing
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_fiscal_crown_literals.py --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/fiscal_crown_literals.py --gremlin-report=json --gremlin-workers=2 --gremlin-no-coverage-filter --strict-pardons --max-pardons=0 --no-cov -q
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff check src/archive_govt_nz/domains/health_appropriations/fiscal_crown_literals.py tests/domains/health_appropriations/test_fiscal_crown_literals.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff format --check src/archive_govt_nz/domains/health_appropriations/fiscal_crown_literals.py tests/domains/health_appropriations/test_fiscal_crown_literals.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/pyright src/archive_govt_nz/domains/health_appropriations/fiscal_crown_literals.py tests/domains/health_appropriations/test_fiscal_crown_literals.py
```

Real replay calls `admit_fiscal_crown` on the existing external
`bronze-cas/sha256/de/de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f`
object. Returned records are in memory only. No full harness, shared lifecycle,
source promotion, acquisition or publication operation was performed.
