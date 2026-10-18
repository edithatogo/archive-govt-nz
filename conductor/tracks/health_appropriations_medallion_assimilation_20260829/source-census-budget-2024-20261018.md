# Budget 2024 expenditure and revenue census

The [official release](https://www.treasury.govt.nz/publications/data/budget-2024-data-estimates-appropriations-2024-25)
identifies the two existing workbook locators. The release and native Explanation
B3 agree on June-year actuals 2020–2023, estimated actual 2024 and budget 2025.
Issue/signed date is 30 May 2024; page update is 21 June 2024. The workbooks
exclude 2023/24 Supplementary Estimates. Prior-year agency data is not restated
for restructuring, so detailed sums need not equal the restated Estimates.
Workbook data supports the official tabled documents; it is not their replacement.

A bounded preflight found no exact locator record in four retained inventories
and no candidate in 360 first WARC headers in the primary Health WARC directory.
That check does not establish global absence or alias equivalence. Both exact
URLs were subsequently captured privately with HTTP 200 through the existing
preservation core. CAS/WARC hashes, lengths, response binding and receipts pass.
The original capture-input census at 8d76b993/b7011bcf remains retained.

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| Expenditure | 943,456 | `891539afe9f5df4a7c7f73ac29695e19b6fb523a4947d305e1f4bd69ebcb3256` |
| Revenue | 104,606 | `bdaed462ac4f517a571c2f0e29a18bd4da726e25ca7be85ff6372f0a370d2eea` |

Repeated native inventories agree and source bytes remain unchanged. Expenditure
has 8 sheets and Raw Data 6,646 by 17; revenue has 7 sheets and Raw Data 1,005 by 8.
Every row below each header is occupied: 6,645 expenditure and 1,004 revenue rows.
Full raw headers, Intro notices and lower Explanation definitions are observed.
Native units are thousands (`$000`); Year is the June year end. ISO currency and
period starts are not inferred. Pivot/graph sheets remain inventoried; formulas
are not evaluated and cache freshness is not asserted. Decoded previews stay private.

Intro A10/A13/A14 state Crown copyright and CC BY 4.0, retaining restrictions on
emblems/logos/Coats of Arms and requiring written attribution. The sole embedded
PNG in each workbook is the same CC BY badge, visually inspected from unchanged
bytes. This records source declarations and image identity, not legal adjudication
or publication approval. Coordinates and decoded-text/media hashes are retained in
[the native definitions observation](./budget-2024-definitions-20261018.json).

The new 2024 revenue profile binds the captured hash and exact locator, preserves
the native 2020–2025 amount-type map and all 1,004 source-row dispositions, and
retains literal OOXML amount tokens. Its edition-specific bound does not change
the 2025/2026 1,000-row limits. Actual-source qualification emits 66 Health facts and 1,056 lineage entries,
with 938 explicit non-Health dispositions and zero rejected rows. Two complete
four-file builds are byte-identical and common dispatch agrees on facts,
lineage and losses. The revenue profile was delivered through PR #717 after corrected original
local assurance and all seven hosted checks. Expenditure now has its own
source-specific native qualification, described below. No Gold currency, denominator, deflator,
classification mapping, netting or analytical join is approved by this census.
The wider 2024 source families and the overall historical census remain incomplete.


The supported `budget-revenue-2024/v1` source-operation entry is now qualified
through the actual CLI parser and initialized MCP JSON-RPC preflight. Default
preflight creates no output package; explicit CLI writing reproduces all four
previously qualified files exactly. The corrected tree 89fdb3c9 passes all 32
original harness stages (8,038 tests, 14 skipped). Earlier direct-only evidence
is retained; PR #717 is merged at bde4f721 after all seven hosted checks, and
its clean topic refs are pruned.


The pinned2024 expenditure profile accounts for all6,645 rows:244Healthfacts,
6,401explicit non-Health dispositions, zero blanks/rejects and6,100lineage
entries. Actual CLI/MCP read-only preflight agrees; explicit CLI writing matches
all four direct package files exactly. Common dispatch facts, lineage and losses
agree. All17 native columns and parent/category/group/periodicity qualifiers
remain source-separated; no currency, period start or aggregation is inferred.
See [expenditure qualification](./budget-2024-expenditure-profile-20261018.json).

Three unchanged local full-harness runs did not qualify: four and two workers
hit unrelated Hypothesis timing checks; one worker hit the original900s cap.
The failures and terminal/kernel-release evidence are preserved. No check or
limit is suppressed. The focused PR will qualify the identical full checker on
clean hosted runners; seven exact-head successes remain required before merge.
This is not a local full-pass claim or final track completion.
