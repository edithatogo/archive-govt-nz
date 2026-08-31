# Exact-series CPI source adapter

## Scope and contract

`cpi.normalize_cpi` reads a hash-pinned, size-bounded original CSV snapshot.
The default is a read-only preflight; `dry_run=False` writes only to a new,
exclusively reserved local directory. Interrupted files remain without a
completed manifest. Originals, donor derivatives and Hugging Face are unchanged.

This is the explicit `CPIQ.SE9A` profile, with the exact nine source headers,
Subject `CPI`, Group `CPI All Groups for New Zealand`, title `All groups`, second
title `NA`, units `Index` and supplied status `FINAL`. Metadata/layout drift,
duplicate selected periods, unsupported numeric/period tokens and invalid UTF-8
fail closed. This version accepts one physical CSV line per record; multiline
quoted fields are unsupported, not flattened. Source row numbers and all nine
decoded source fields are preserved; original CSV quoting remains in Bronze.

Periods are explicit quarter-ending `YYYY.MM` tokens, converted to quarter-end
dates without fiscal-year joins. Values are exact Decimal128(38,18), without
rounding; literal `NA` becomes null with `missing_unknown_reason`. The original
value and status tokens remain separate: `NA` rows can and do carry `FINAL`.
The adapter does not interpret FINAL as immutable. It does not infer the index
base from a value of 1000, impute zeros, interpolate gaps or adjust spending.
Base stays null with `index_base_not_verified`; household CPI is explicitly
not health-service input-cost inflation. Extraction is not rights approval.

Four files: `cpi_facts.parquet`, `field_lineage.parquet`,
`row_dispositions.parquet`, and the hash-pinning completion `MANIFEST.json`.
Typed facts use the `price_population_fact` recordset, source observation,
vintage, locator, source row, original period/value/status fields and lineage.
Every source row has a disposition, including all unselected series.
Limits: 16 MiB source, 100,000 data rows, 8,192 characters per physical line,
4,096 characters per decoded field; these are bounded-parser contracts, not
a general hostile-input process sandbox.

## Local retained-source evidence

Original SHA-256:
`f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d`.
The existing source census supplies the exact source URL and capture timestamp
`2026-08-29T09:00:17Z`; derivative vintage is `Stats-NZ-CPI-2026-Q2`.
No new source request was made.

Two independent new local builds agreed byte-for-byte across all four files.
Retained output: external archive `silver/raw-cpi-20260831-v1`.
Manifest: `edb62f4b106948502e717f5f6c5e3da00efc0a64bb10b5dcbafc48cd1a6c257e`.

| Product | SHA-256 |
| --- | --- |
| CPI facts | `0dfed3330c379af6c08dfcac0235149b81fa76f3131b32865ae92ddc98911560` |
| Field lineage | `948e0533cd941f08401026bb71b577c6a1e145ac0d1882e31125aa8d06ae6df5` |
| Row dispositions | `bc4c5af889ff01bae782c9c6321bfdd31afa03433998c178d2af1357e71643d0` |

22,701 source rows: 449 selected (422 numeric, 27 literal NA), 22,252 unselected;
4,041 selected field-lineage entries. Separate original-token reconciliation
matched all 449 facts and all 22,701 raw disposition dictionaries. The original
hash matched before and after. These counts do not imply other CPI series were
normalized, index-base metadata was acquired or inflation-adjusted products exist.

## Validation and failure ledger

- Red: initial test collection failed because the module did not exist.
- First expanded suite: 41 passed, one assertion mismatch for Python 3.14.6's
  year-zero exception wording; invalid input was correctly rejected. The test
  match was corrected; no supported period rule changed.
- Focused: 42 tests passed, including a bounded pure Hypothesis property;
  critical coverage 100% across 77 statements and 14 branches.
- Cold mutation: all 36 mutants killed; zero survivors, timeouts, errors,
  pardons or cache hits. Report SHA-256:
  `4fa82c89c23831315a2db2503e32fa0d105a52d39de33c4277f7781e88a00b9d`.
- Production source SHA-256:
  `ee92ff2149af279a240268afdbfd62a484c1ab984021d806d7d4c6b4f59cc699`.
- Ruff passes; basedpyright passes after giving the synthetic test's provenance
  kwargs an explicit TypedDict (no production behavior change).
- Native harness, CPython 3.14.6: lock, Conductor (70 tracks), format (1,366
  files), lint and types passed. The test stage created four workers and
  collected 1,953 tests, reached approximately 92% without an observed failure,
  then exited 124 at the native 300-second budget. An unrelated FOI harness
  overlapped. This is a timeout, not a full validation pass. No thresholds,
  deadlines, unrelated tests or other actors' processes were changed.
- A second unchanged native harness again passed the pre-test stages and
  exited 124 at the 300-second test budget, this time at approximately 99%
  of 1,953 collected tests. One failure marker appeared, but no traceback was
  emitted before termination; its cause is unknown. This run is not a clean
  pass or merely a presumed timing-only failure. Read-only machine inspection
  recorded one-minute load 551.15 during the run. All owned test processes
  exited; no other actors' processes were changed. Further overloaded local
  retries are deferred in favor of explicit hosted exact-head checks.
- Independent review added test-only checks for full source/field-lineage,
  disposition and output-hash closure, original-byte immutability and three
  source/output symlink cases. The initial new assertion distinguished the
  exact pre-Parquet Decimal spelling from scale-18 readback padding; its test
  expectation was corrected, with no production change. The expanded suite
  passed all 45 tests in 12.21 seconds with 100% critical line/branch coverage;
  final basedpyright passed. The 36-mutant report predates these additions and remains
  bound to the unchanged production source above.

## Hosted delivery

PR #271 was observed merged at `2026-08-31T10:56:19Z`, merge
`4ec9920a2121f0af5319783c0c1d5bb5decf91d4`, checked head
`f4b90eabd85ff2f6d709e78552d1b4d490345349`. All seven exact-head checks passed:
Ubuntu/macOS/Windows assurance, analyze, CodeQL, workflow lint and codecov/patch.
CI run `33383803345` Ubuntu job `99461794236` passed 1,956 tests with eight
warnings, 40 schemas/30 representative documents, 9/9 parity and all native
mutation/supply-chain gates; its SBOM contained 112 components. This hosted
success does not retroactively change either local exit-124 receipt or explain
the unidentified local failure marker. The merge actor is not asserted.

CPI base metadata, total-resident population,
fiscal-period joins, inflation/per-capita products and exact-candidate HF
publication remain separate tasks and gates.
