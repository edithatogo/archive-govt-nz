# Donor detailed Health literals — 2026-09-07

This dedicated receipt does not change shared lifecycle status. The new
`donor_health_detail.admit_donor_health_detail(path, vintage)` is an in-memory
raw/context admission contract, not a new capture adapter or Silver/Gold writer.
Existing forecast extraction covers the ten literal summary cells per source,
not the eight detailed classifications. It deliberately rejects formula inputs.

## Verified originals and exact scope

| Vintage | SHA-256 | Bytes | Sheet | Literal range | Excluded formula totals |
| --- | --- | --- | --- | --- | --- |
| BEFU-2025 | dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6 | 207919 | Core Crown Expense Tables | F102:O109 | F111:O111 |
| HYEFU-2024 | 725399c09323594c921dbcc493206abe59bf7b91dd968b8c7f6f3a67d4707969 | 206997 | Expense Tables | F103:O110 | F112:O112 |

Replay used existing external `bronze-cas/sha256/<prefix>/<digest>` under
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations`. No new download,
HTTP observation, source payload in Git, publication or rights decision occurred.

Each range contains **80 literal numeric cells**, including zero values.
Exact XML numeric tokens and number formats are preserved; binary floats are
not used to construct amounts. Existing bounded inventory, verified snapshot,
OOXML token extraction and exact-decimal safety helpers are reused.

## Chained source headers, not cache admission

For each column F:O, BEFU year references are row99 → row34 → row4;
HYEFU references are row100 → row35 → row3. Their literal terminal labels are
2020–2029. BEFU K100 → K86 → K53 → K35 → K5 and HYEFU
K101 → K87 → K54 → K36 → K4 terminate in literal `Forecast`. Other selected
amount-type headers are literal. Actual covers 2020–2024; Forecast 2025–2029.

Only same-sheet single-cell reference syntax is supported, at most eight
visited cells, rejecting cycles, external references, names, ranges and
arithmetic. Every visited coordinate and original formula/text is retained.
This is explicit reference dereferencing, not formula-cache substitution.
The module never opens a data-only workbook. Unit text is `($millions)` at
D100/D101 respectively; row labels and three footnotes D113:D115/D114:D116
are retained verbatim as shared table context, including reform and
classification-change qualifications. They are not generalized analytically.

The ten SUM totals per workbook have stored caches but remain excluded.
No sum is recomputed or compared to assert equivalence with summaries.
No cache freshness evidence is available from these originals alone.
ISO currency and fiscal endpoints remain null; core/total consolidation,
cross-vintage equivalence, canonical projection and rights remain unasserted.
Bare years and a dollar sign do not independently settle those questions.

## Validation

- TDD: initial new-header tests failed collection because the module did not exist.
- 27 focused tests passed (synthetic fixtures explicitly not real replay).
- Cold, unfiltered mutation run: 33 killed, zero survivors, zero cache hits.
- Ruff checks and module Pyright: passed, zero errors/warnings.
- Separate retained-byte replay verified both SHA-256 values; independently
  parsed worksheet XML selected via workbook relationships and matched all
  160 literal tokens, with no `<f>` in selected cells. Confirmed 20 separate
  total cells contain formulas and caches. Repeat admissions were identical;
  original bytes remained unchanged.
- Canonical `encode_json(result)` SHA-256: BEFU
  `9c6ef9ad4dbe8fe50716146f59820cce1b6e0b546983e834592608930c6d4663`;
  HYEFU `deed6e5e61f2ec838136cde4de9ffe5a83e059e3e42238d9ccecd66d1b86867b`.

Focused command: `PYTHONPATH=src python -m pytest
tests/domains/health_appropriations/test_donor_health_detail.py -q`.
Mutation adds `--gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/donor_health_detail.py
--gremlin-report=json --gremlin-workers=2 --gremlin-no-coverage-filter
--strict-pardons --max-pardons=0 --no-cov`.

Proposed parent disposition: **Detailed donor Health literal raw/context
admission complete for these two exact ranges; formula-total admission and
analytical qualification remain separate, unclosed tasks.** No user analytical
choice is needed to preserve/admit these source literals.

## Independent MCP review checkpoint

Reviewed `9703852fc5434edea92cdc8d66c32392e1f547b9` against health-interfaces
HEAD `7f5c479fe35d2d5e62989e6551efcd581b319455`; relevant MCP implementation
files were unchanged. No actionable finding. Read-only focused inspection tests:
22 passed. No full harness or native-Windows assertion.
