# Read-only Fiscal analytical access

The CLI command `health-appropriations-query-fiscal-gold` and MCP tool
`health_appropriations_query_fiscal_gold` share a bounded named-query adapter.
Supported tables are nominal, shares, per_capita and cpi_benchmark. Callers
provide the exact local Gold manifest digest. All four payload inventories,
byte hashes, row bounds and Arrow schemas are verified before querying.

DuckDB runs in memory with external access disabled. SQL is selected from two
fixed statements; table data is registered from verified Arrow, and limits are
bound parameters. There is no arbitrary SQL interface. Results sort by period
end and, where present, measure. Limits are 1–200 (default 50). Responses report
total rows and truncation so a bounded result cannot imply complete coverage.

Decimal values use exact strings and dates ISO 8601. Source IDs, qualifications,
original time statuses and exclusions remain in rows. Product fixity is the
verification scope; original-source re-verification, publication and rights
assessment are separate. Failures use bounded error codes without leaking paths
or exception details. MCP validates its closed input schema before I/O and
advertises read-only/idempotent/non-destructive/local-world annotations.

Example, after setting the retained package directory and independently pinned
digest in the two task-specific variables:

```sh
archive-govt-nz health-appropriations-query-fiscal-gold \
  "$FISCAL_GOLD_PACKAGE" "$FISCAL_GOLD_MANIFEST_SHA256" --table shares --limit 200
```

The real console command and initialized MCP protocol returned equal receipts
for all four native tables (324 rows). Every row matched an independent direct
Arrow read with exact JSON encoding, and all five package file digests remained
unchanged. A bad manifest digest produced bounded failure and console exit 2.
Ten focused tests cover all named views, ordering, exact Decimal strings,
truncation, CLI/MCP parity, schema/hints, invalid SQL/limits and missing packages.
The initial red collection failed on the absent adapter module. A protocol
regression also demonstrated that failed queries incorrectly had `isError: false`.
The adapter now participates in the server's failed-status handling, preserving
its bounded structured failure receipt while reporting `isError: true`. Native
invalid-pin protocol readback confirms this correction. The global and
focused coverage floor remains 80%; tests were selected for meaningful boundaries.

Plots/reports, broader contextual views, Platinum/federation projections,
scheduled analytical operations and final recovery/review remain open.
