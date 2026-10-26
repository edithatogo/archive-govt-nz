# Source-faithful overview Gold query

The fixed DuckDB query re-extracts the supplied Bronze object and independently
verifies the complete pinned overview Silver package before loading its fact
bytes. The query preserves every source field and source record identity and
only orders records. External access is disabled and callers supply no SQL,
join, calendar interpretation, aggregation or conversion.

Every returned row is compared with its native Silver row before serialization.
Decimal amounts are emitted as exact strings; the retained raw source JSON and
parsed qualifier records preserve printed tokens and phrases. Rights remain
`not_evaluated` and publication `not_performed`.

Eight affected contracts cover the existing overview boundary, source qualifiers,
wrong manifest pins, changed fact bytes and modern repeated recovery. The real
five-edition replay is recorded in
`modern-vote-health-gold-query-recovery-20261026.json`: each edition builds twice
from its exact Bronze hash, passes pinned Silver readback, and returns identical
source-faithful Gold results. The existing integrated recovery runner invokes
this same helper, so future full runs include the query automatically.

The preceding 48-lane integrated recovery receipt remains an immutable earlier
checkpoint. Its other 47 lanes are unchanged by this query addition; their
existing successful evidence is reused rather than rerunning those unrelated
products. This bounded replay does not close whole-track recovery.

This adds a Gold query, not a new canonical mart, plot, Platinum package or
CLI/MCP command. It excludes cross-source/vintage totals, currency conversion,
real-spending/health-cost deflation, per-capita/GDP/Crown shares and reconciliation
of unreviewed source components. Other Phase 6 products and Phase 7-9 completion
contracts remain open.

The complete local validation harness passed on this query implementation:
8,454 tests, 14 capability skips, the unchanged 80% coverage gate, 81 schemas /
71 representative documents, parity 9/9, all configured mutation checks and
supply-chain gates. Measured coverage was 96.87%; no higher coverage target was
introduced. Only documentation gates are rerun for this evidence note.
