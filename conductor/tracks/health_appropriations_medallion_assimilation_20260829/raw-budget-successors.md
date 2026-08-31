# Budget successor extraction and verification

## Scope

Budget 2026 is a separate source vintage, not a replacement for Budget 2025.
The already-captured original remains in Bronze. The pilot reuses the existing
named-column adapter after inspecting the actual 17-column header contract;
it does not enable a generic unknown-layout or revenue adapter.

Original SHA-256:
`3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0`.
Source: `https://budget.govt.nz/budget/excel/data/b26-expenditure-data.xlsx`.
The retained capture receipt records 918,842 bytes and WARC SHA-256
`94a9637ed1c1e363a5a0a0cab84268343982ae11fbba92c55cb3f20cd579ea55`.
This turn did not reacquire the source or independently re-audit that WARC.

## Local pilot receipt

Retained directory: `silver/raw-budget-2026-20260831-v1` beneath the external
Health archive. The four-file manifest SHA-256 is
`f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738`.

| Observation | Result |
| --- | ---: |
| Input rows accounted for | 6,451 |
| Selected Health facts | 185 |
| Non-Health rows preserved with out-of-scope disposition | 6,266 |
| Rejected rows | 0 |
| Source-cell lineage entries | 3,145 |
| Original columns linked per selected row | 17 |

Values cover Actuals 2022-2025, Estimated Actual 2026 and Main Estimates 2027.
Amount types, source labels and NZD-thousands units are retained; fiscal period
starts remain unknown and `financial_year_basis_unverified` is kept. Timestamp
`2026-08-31T05:50:00Z` is fixed local reproducibility context, not original HTTP
capture time.

Two independent builds match every file. An independent literal OOXML
comparison, separate from openpyxl extraction, reconciles every selected amount
and year exactly, all selected labels and all 3,145 lineage coordinates. Every
input row has a disposition. Original SHA-256 remains unchanged before/after.

Output SHA-256 values:

- `budget_facts.parquet`: `42781cb2723f9b1b32a536a46389b0c5a54431d9c600380c6058e740a96b6f9f`
- `field_lineage.parquet`: `917e14e0de9d5fc3f7c56d14da9cc103031aa475e59157da46824d63c06c9a4b`
- `row_dispositions.parquet`: `e4bad4ad0a92b80257526fddcf4d7b7e665d1eddee90cedf6706977e65260b0f`

## Versioned regression and consumer boundary

Synthetic Budget-2025/Budget-2026 full-layout fixtures exercise exact amounts,
zero/negative corrections, all-cell lineage, deterministic rebuild and source
preservation. Combined analysis keeps overlapping years, amount types and
vintages separate; a later Actual does not overwrite an earlier estimate.
Three tests pass. Invented fixture values are not copied source rows.

A bounded verified Budget-package reader (`07029cc`) consumes these packages
without treating the fixed four-profile raw-run wrapper as a universal source
registry. It checks exact file/schema sets, pinned bounded snapshots, strict
integer counts, fact/source identity, every input disposition and all selected
field-lineage closure. It accepts reviewed passed/nonempty Budget-v1 packages;
writer-produced empty packages remain preserved but outside this consumer
contract. It does not reopen originals or infer missing fiscal-year semantics.

The final 61 reader/vintage tests pass on CPython 3.14.6 with 100% reader line
and branch coverage (137 statements, 30 branches). Independent literal fixture
headers and producer-written Parquet schemas avoid coupling corruption tests
to consumer constants. Each test gets fresh copies of one immutable baseline;
this removes repeated XLSX setup without sharing mutable test state. The
retained live pilot reads back as 185 facts, 3,145 lineage entries and 6,451
dispositions with status passed and the manifest pin above unchanged.

The required native harness was run with ctrace, JIT disabled and four workers.
Lock, 70-track Conductor validation, formatting, lint and typing passed. The
test stage collected 1,972 items and reached 100% progress but exited 124 at
its unchanged 300-second deadline before a final summary/coverage result.
No failed-test marker was observed; this is not a full validation pass. Heavy
unrelated machine load was observed; no other actor's processes were changed.
At that local checkpoint reader mutation and hosted assurance were pending. Original files and
publication bytes were not modified. CLI/MCP operational exposure is a separate
follow-up; this pilot alone does not complete multi-vintage archival operation.

## Hosted delivery and interrupted local mutation

PR #273 is observed merged at 2026-08-31T10:59:47Z. All seven checks passed
on head `e1f4b2d3226cc70e62f8ac8caa86f3923f87b4b3`; Ubuntu CI run
33384338052 passed 1,972 tests (eight warnings), 9/9 parity and native
mutation/supply-chain gates, with a 112-component SBOM. Merge
`d0a36f1099fce30427927ebda4f735c3c9617a5a` leaves reader source and tests
unchanged; this does not retroactively turn the local timeout into a pass.

The subsequent cold, unfiltered 110-mutant reader run was interrupted when its
active worktree and interpreter disappeared. It exited 1 with 27 killed,
83 errored, no survivors and no cache hits; teardown also reported a readonly
SQLite cache. This is invalid/incomplete mutation assurance, not 110 kills.
The preserved report SHA-256 is
`7d3063a5fbe8315e1aab9c99af7834e0aa6925f0414a066d16a4a12e464adc3a`.
No cleanup was performed by this task. All implementation was already pushed.

Recovery uses a standalone no-hardlinks clone outside the shared worktree
registry, with the same reader source and tests. Reader source SHA-256 remains
`176858108215780f4672197d918757c4f7403251eececa86a05a9993b9c1b6a0`.
The recovered cold, unfiltered run killed all 110 mutants, with zero survivors,
timeouts, errors, pardons or cache hits (58 reader tests; 298.38 seconds).
Its report SHA-256 is
`0a71f54ebc5777211c234d57bd89fdbecfdb09f0f41c4805a634f33bb0ffb3b1`.
No test limit or gate was weakened. This completes the bounded reader assurance,
not the broader source-family or publication tasks.

## Remaining boundaries

The capture manifest records resource-level Treasury licence evidence; new
facts still have `rights_state=not_evaluated`. No implicit rights promotion or
Hugging Face upload occurs. Future publication must join exact source rights
evidence and receive exact-candidate approval.

Seven other sheets remain inventoried and excluded from this narrow Raw Data
Health selection. Revenue workbooks, other Budget years, remaining fiscal
sources and complete in-scope data-area normalization remain pending. Captured
HLFS working-age population is not a national-total denominator; unqualified
per-capita measures remain unavailable until a suitable, temporally aligned
population series is selected.
