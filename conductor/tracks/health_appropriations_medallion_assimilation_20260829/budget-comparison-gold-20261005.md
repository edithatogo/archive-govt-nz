# Budget comparison Gold and operations — 5 October 2026

The previously qualified Budget-2025/2026 estimate-transition query now has a
separate five-file Gold package: exact comparison Parquet, summary JSON,
README report, a discrete PNG diagnostic and a completion manifest. Source
packages and Bronze originals are verified at build time. Dry run writes
nothing; writes require a new output directory and reject input overlap.
Interrupted outputs remain preserved. Immediate readback verifies the package.

The Gold physical schema explicitly names Parquet list elements; it does not
change logical source values or rewrite the input comparison. Summary rows
retain exact Decimal strings, ISO dates, every literal dimension, both source
IDs and row coordinates. Reports identify deterministic group numbers for plot
drill-through. The PNG uses float conversion only for display, connects no
points, distinguishes June 2025/2026 and excludes unmatched/ambiguous groups.
Exact values and excluded records remain available in Parquet and JSON.

The reader requires exact manifest/payload pins, file inventory, bounded
snapshots, strict physical schema, row/expansion bounds and regenerated summary
and README projections. Plot verification is pinned byte fixity; it does not
re-render the plot or reverify originals. This reader uses synchronous decoding
for its small capped table: a sampled native console shutdown deadlocked an
Arrow worker releasing a Python-backed buffer after successful output. The
failure, stack and first package were preserved before the bounded fix. No
thread-pool global setting, dependency change, timeout extension or gate
exception was introduced.

`health-appropriations-build-budget-comparison` takes named original/package/
manifest arguments for both source vintages and an output directory; `--write`
is required to write. `health-appropriations-query-budget-comparison` takes a
package path, exact manifest SHA-256 and a limit of 1–200. The read-only MCP tool
`health_appropriations_query_budget_comparison` returns the same structured
receipt. Successful queries carry source bindings and all comparison caveats;
failed receipts set MCP `isError` and CLI exit 2. There is no arbitrary SQL,
network request, mapping, rights assessment or publication action.

Native paired builds consume the two separately qualified fresh-Bronze Budget
replay packages from the preceding task; this delivery recipe does not repeat
source normalization. Both five-file inventories agree. All 60 query rows match
CLI, initialized MCP and independent Arrow reads, and exactly retain the earlier
comparison values. The plot has 37 points with 23 excluded groups. Gold inputs
and originals remain unchanged. Manifest SHA-256:
`e8c7efda7773368bcee1b7f596f373c0aa6ec3f4453485b9b6fb9cc447ebd5fc`.
The plot was visually inspected for legible labels, qualifications and no lines.

Three focused tests cover exclusive/dry-run behavior, exact reports/console
readback, corrupt inventories and initialized MCP success/failure. The target
remains 80%; this small module measured 100%. Native checks cover actual build
commands and their process completion. Scope remains the two qualified Budget
transitions; wider comparisons, Platinum and final Health assurance remain open.

The initial full harness exposed the MCP dialect declaration required by the repository standard. The bounded failure log is retained; both schemas now declare JSON Schema 2020-12. All 21 combined focused delivery/MCP tests pass. The final v3 native receipt binds the corrected code and its packages are byte-identical to v2. See `budget-comparison-gold-20261005.json` for hashes and the dated scoped review receipt; this review does not close the final Health completion gate.

Final required harness passed: 7,469 tests and 10 skips, 97.93% aggregate coverage with the unchanged 80% floor. Format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates pass. Native v3 proves paired byte-identical packages and exact 60-row CLI/MCP/Arrow delivery. Scoped automatic review passed; broader Health completion remains open.
