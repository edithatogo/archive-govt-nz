# Pure historical canonical consumer bridge

## Outcome

The public `bridge_historical_inputs` function now accepts the already defined
historical raw manifest and three raw Arrow tables together with the three
canonical projection tables and the canonical parent-receipt bytes. It reruns
the public historical projection and accepts the canonical inputs only when
table names, schemas (including Arrow metadata), row values, physical row order
and the canonical JSON receipt are exact.

The returned object contains copied analysis inputs, the complete canonical
lineage table, reversible canonical-to-source record identifiers, complete
consumer-field accounting and an assertion-only receipt. `year` and
`period_end_month` are transported only after the canonical `valid_time_end`
and annotated period token agree. No file is opened or written.

## Focused assurance

- Red phase: the focused test module failed collection because the consumer
  module did not exist.
- Green and hardening: 22 tests pass with 100% line and branch coverage over 98
  critical statements and 16 branches.
- Ruff and scoped basedpyright pass.
- Tests cover exact table/schema/order and typed-receipt rejection, raw-order
  independence, decimal representability, contradictory periods, hostile
  Decimal contexts, reversible field/identity accounting, interrupts, bounded
  rows/bytes, and public analysis equivalence for adjacent/gapped years,
  March/June periods, accounting-basis changes, and GDP period alignment.
- Source SHA-256:
  `a667c1b914a4bf89fd1234f3ef697242a38dcf0536f3d1af7c7bd711e045257f`.
- Test SHA-256:
  `fe29c9b7aa2e1245b78e3faabe480153e7ba691de2c4dea6a3ab4d21c270b618`.
- Functional commits: `02d36bc`, `13e8d85`.

## Boundaries

This is a pure in-memory compatibility bridge. It does not verify persisted
file fixity, reopen a canonical package, execute analysis, assert new semantics,
evaluate rights, grant publication approval, or publish any data. Decimal
source scale 17 and canonical scale 18 can produce different string encodings;
the tests compare exact numeric values and retain the reversible identifier
substitution instead of claiming byte-equivalent analytical inputs.

Cold mutation, full native validation, retained-package replay, persisted
canonical-reader support and hosted delivery remain separate evidence events.
