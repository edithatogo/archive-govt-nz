# 2016/17 Vote Health overview: implementation review

## Scope reviewed

- One exact Budget 2016 Vote Health Estimates PDF, SHA-256
  `c997ffecb631e4dfd0ffd8a1e620585b6b963df11f94164adb2ac02cfa391b2e`.
- 24 phrase-anchored monetary statements from PDF pages 2–3; source categories,
  amount tokens, nominal `$ million` unit, period and percentage qualifiers are
  preserved. No totals are recomputed or mapped between editions.
- Existing source capture, WARC, source-census row and structural PDF baseline
  are reconciled in `vote-health-estimates-overview-2016-17-census.md`; no
  duplicate capture was made.

## Findings and boundaries

The test contracts cover exact values and names, source phrases, period, pages,
qualifiers, profile dispatch and committed/runtime schema equality. Independent
native output checks recorded earlier verify paired repeat builds and direct
lineage for all 24 facts. The correction in this slice adds the missing
2016/17 transformation identifier to the committed source-operation schema;
the runtime schema already contains it.

The other 100 PDF pages remain preserved-unreviewed. Fact-level rights,
currency-code admission, price base, cross-edition equivalence, downstream
analytical use, and publication rights remain unevaluated. Output remains local
validation evidence only. The wider annual Budget/BEFU/HYEFU/Pharmac and exact
context-series census is incomplete.

## Validation

- Focused source-operation and 2016/17 tests: 523 passed, 10 skipped.
- Required `./scripts/validate.sh`: 7,478 passed, 10 skipped; 97.80% coverage
  with the unchanged 80% floor; schemas 53/53; parity 9/9; configured mutation
  and supply-chain gates passed.
- Scoped Conductor `phase_7_gates` review passed; receipt is retained alongside
  this review.
- Census addendum checked against the existing capture manifest, including
  source SHA-256, URL, media type, publisher-declared licence and rights URL.

Exact-head hosted CI checks are separate follow-up evidence. This review does
not assert full Health track completion.
