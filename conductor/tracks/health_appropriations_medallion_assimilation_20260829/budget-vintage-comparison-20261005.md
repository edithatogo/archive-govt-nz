# Budget estimate transitions — 5 October 2026

The library query compares Budget-2025 expenditure with Budget-2026 expenditure
for the two observed estimate transitions: FY2024/25 Estimated Actual to Actuals,
and FY2025/26 Main Estimates to Estimated Actual. It requires the exact reviewed
original hashes and separately pinned verified Budget-v1 Silver packages. The
original pins qualify workbook Explanation cells B3, B17, B21, B23 and B40–B42:
June year ends, thousands and the source amount-type meanings. Existing Silver
facts and their unverified-period flags are preserved; the derived diagnostic
adds the qualified June flow period without rewriting those inputs. These dates
do not claim the legal duration of a multi-year appropriation.

The official [2025 release](https://www.treasury.govt.nz/publications/data/budget-2025-data-estimates-appropriations-2025-26)
and [2026 release](https://www.treasury.govt.nz/publications/data/budget-2026-data-estimates-appropriations-2026-27)
were read again. Their coverage and restructuring warnings agree with the
retained workbook definitions. The workbook supports the official Estimates;
it does not replace them.

Each key includes every raw dimension except Year, Amount $000 and Amount Type.
This includes App ID, category, scope, periodicity, department, portfolio and
classification where present. There is no fuzzy matching or assumed mapping.
Unique literal pairs retain both record IDs, source rows, exact Decimal amounts
and an exact later-minus-earlier difference in NZD thousands. Duplicate groups
remain ambiguous even when their values agree; unmatched groups retain their
one-sided values and have no difference. No values are summed or substituted.
Other years remain counted outside these transitions.

Literal equality does not establish restated appropriation comparability.
Supplementary Estimates exclusions, agency restructuring, edition-specific
names/scopes and unestablished GST basis remain explicit caveats. Differences
are arithmetic diagnostics, not a claim about budget performance, complete
annual coverage or official appropriation reconciliation. Rights/publication
and whole-track completion remain unasserted.

Four focused tests cover exact transitions (including zero/negative amounts and
low ambient Decimal precision), ambiguous/unmatched identities, changed source
bytes/profiles and inconsistent amount-type/year combinations. Coverage measured
100% for this small module; the required target remains 80%. Fixture source pins
are explicitly replaced only for invented transport fixtures; native source
qualification uses the committed original pins.

The library writes nothing. The external replay recipe builds both Silver
packages directly from pinned Bronze twice, checks every selected field against
independent literal OOXML reads, verifies differences with integer thousandths,
and retains paired Parquet/receipt inventories. This is a bounded expenditure
comparison, not closure of all cross-source reconciliation or CLI/MCP delivery.

Native results: 60 groups (37 unique pairs, 11 earlier-only, 12 later-only, no
ambiguous groups). All 48 earlier and 49 later transition records are accounted
for; 167 earlier and 136 later records remain outside these transitions. Both
complete build inventories agree and originals are unchanged. All selected
source cells across the 215/185-fact packages and all 37 differences passed the
independent checks. Required harness: 7,466 passed, 10 skipped; scoped review
passed. See the paired machine receipt.
