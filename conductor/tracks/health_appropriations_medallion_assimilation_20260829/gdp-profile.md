# Exact quarterly GDP source profile

Focused, cold mutation, full native and two-build reconciliation assurance pass.
Hosted delivery remains pending. No source download, annual
aggregation, health/GDP denominator selection or publication occurs.

## Retained original and literal meaning

The 49,887-byte source SHA-256 is
`a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21`,
census ID `stats_nz_gdp-9fc80ed4b7f234b2`, observation
`2026-08-29T09:00:17Z`. Contents names the March 2026 quarterly current-price
income/expenditure release, published 18 June 2026. Reference quarter,
publication date and capture observation remain distinct.

`Table 1!C27:BJ27` supplies 60 actual current-price expenditure GDP values,
June 2011–March 2026. Reference `SG03AB01GE00S900` and prefix `SNEQ` remain
separate, not an externally verified concatenated series identifier. Income
GDP and Table 2 seasonally adjusted values are different series. The latter
table and every unselected nonempty cell remain preserved context.

Unit is literally `$(million)`, scaling million. ISO currency remains null:
the workbook does not explicitly spell it out. Publisher identity is not
substituted for currency qualification. Values are exact integer OOXML tokens,
not display-rounded float reads, annualized flows or recomputed totals.
Signed values and zero are supported without treating missing as zero.
The footnote permits rounding differences in totals; no exact additive
accounting assertion is made. Source has no formulas or missing numeric tokens.

## Implementation and preservation boundary

Library-only `normalize_gdp` uses `StatsNZ-GDP-2026Q1`, one capped/hash-verified
snapshot and existing bounded inventory/OOXML numeric-token helpers, unchanged.
Exact sheet, geometry, header, merge, date, format and footnote checks reject
drift. Package limits precede lexical reads. This is a reviewed source profile,
not an arbitrary-workbook process sandbox.

English month tokens are explicit and locale-independent. Dates use the bounded
2011–2026 sequence, not an implicit two-digit pivot. Each date cites both its
quarter header and A4's full year range. Literal period/numeric tokens, series,
scaling and units have lineage. Number-format provenance uses explicit
`@number_format` attribute coordinates, not invented cell text.

The source-specific package has 60 `economic_context_fact` rows, 900 lineage entries and 2,287
dispositions covering every nonempty cell across all three sheets. Blank styled
cells are not observations. Exact formatting and all ZIP members remain in
unchanged Bronze. Context and selected-value dispositions are distinct.
This is not canonical registry output. A future semantic projection may map
these observations to `fiscal_context_fact` under a separate reviewed contract.

Dry-run creates no directory. Explicit writes reserve an absent directory and
create `gdp_facts.parquet`, `field_lineage.parquet`, `cell_dispositions.parquet`,
then a hash-pinning manifest. Partial outputs remain without a completion
manifest. Source/output symlinks and existing outputs are rejected. Rights
remain `not_evaluated`; no canonical-schema semantic promotion is claimed.

## Assurance and bounded failures

- Initial red collection failed on absent module. Implementation passed 33
  initial tests, expanded to 44 lexical/property/closure tests.
- Parent review found locale-sensitive labels and missing token/scaling/format/
  date dependencies. Corrected; full closure and locale regression now pass.
- 45 tests, 100% of 90 statements/20 branches, Ruff and strict typing pass.
  Two initial test typing errors were fixed without weakening the gate.
- Cold unfiltered mutation: 37/37 killed, zero survivors/timeouts/errors/pardons,
  zero cache hits, two workers, all 45 tests, 36.11 seconds.
- Two exclusive local pilots match all four files (85,176 bytes), manifest
  `639b3c7da60f2afa1b860c5f6c8f1c4c0ae24bf17aa7af63bf8a06a1f6471b35`.
  Independent readback reconciles every nonempty cell, all lineage raw/normalized
  values, all selected amounts and periods. Original bytes unchanged. Script:
  `36c4bd2eecdf02fc8a817032879db2df5a3e9d76e1afdf53850f177ddf791b38`.
- Native `./scripts/validate.sh` passed at `41e7717`: 2,790 tests in 75.20s,
  97.07% overall coverage, eight existing resource-cleanup warnings, all typing,
  41 schemas/31 samples, 9/9 parity, standard mutation and supply-chain gates.
  Log SHA `cd0e89c8202eaaceca1bbff207ea5d46145512b68383901461c2abc8b1656656`.
  Hosted exact-head delivery remains pending.
- Main `c4d62ca` integrated afterwards at `f061961`, preserving the exact
  incoming ledger prefix. Source and test hashes are unchanged; 45 focused
  tests and the 74-track Conductor check pass. Native was not rerun on this
  integration commit; the earlier native receipt stays tied to `41e7717`.
- QES subsequently reached main `6c23ba8`; integration `76b709c` again
  preserves the incoming ledger prefix, unchanged GDP source/test bytes,
  45 passing focused tests and 74-track Conductor validation. No native rerun
  is claimed for either subsequent integration.
- Exclusively retained `silver/raw-stats-gdp-20260831-v1` after native assurance;
  all four files read back identical to the pilots, original hash unchanged.
  Both temporary pilots remain retained. No previous package was replaced.

Annual/fiscal aggregation, currency qualification, denominator methodology and
rights/publication remain separate future decisions.

## GDP hosted Windows benchmark failure

PR #302 head `d3f144e53d5204666ebc3c2027481ff9cdd57cf4` passed six checks,
but Windows job `99531122435` in run `33405251298` failed after test and mutation
stages at the CAS benchmark: 11.48 MB/s versus the unchanged 15 MB/s minimum.
No GDP-specific failure was reported. The failure is retained, not relabeled
as success; no benchmark threshold, source code or test was weakened. The
subsequent required main integration provides a new hosted validation run.
Main `3be3048` (JSON row-shape contracts) integrated at `8378666` with the full
incoming ledger prefix preserved. The unchanged GDP source passes 45 focused
tests and 74-track Conductor validation again; no new native pass is claimed.

## Prior Pharmac hosted delivery

Fresh REST observation found PR #295 already merged externally at
`2026-08-31T14:13:58Z`, exact head
`76693f64da664e87d98dc0eb38494ff0ae9e6fa0`, merge
`9e559799f441651e79d4109fcd28e5fa89be668e`, all seven checks successful.
This implementation agent issued no merge call. The observation grants no
publication rights or approval.

## Historical-reader main integration

All seven checks, including the unchanged Windows benchmark gate, passed on
head `3e526f3`; subsequent main `2061098` caused a ledger-only merge conflict.
Integration `22a1ca6` preserves the complete incoming ledger prefix followed by
the two existing GDP events. GDP production and tests are unchanged. An initial
focused invocation named a nonexistent Conductor test path and collected no
tests; the corrected invocation passed all 63 GDP/Conductor tests. Repository
Conductor validation was rerun. Prior native assurance is not relabelled as a
new integrated native pass; the new head requires fresh hosted checks.

The Windows attempt on `43b2704` also failed only at the CAS benchmark:
9.89 MB/s below the unchanged 15 MB/s threshold, run `33407966355`, job
`99540166938`. One unchanged-head failed-job rerun passed, yielding all seven
successful checks. No threshold, workflow or GDP code was changed. After PR307
merged, main `5fc7fc8` integrated at `a905e6e`; the full incoming ledger prefix
and both artifact links are preserved. The same 63 focused tests and 75-track
Conductor validation pass. This new integration again requires fresh hosted
checks; previous failures and the successful retry remain separately recorded.
