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
- Green and hardening: 22 tests pass with 100% line and branch coverage over
  107 critical statements and 18 branches.
- Ruff and scoped basedpyright pass.
- Tests cover exact table/schema/order and typed-receipt rejection, raw-order
  independence, decimal representability, contradictory periods, hostile
  Decimal contexts, reversible field/identity accounting, interrupts, bounded
  rows/bytes, and public analysis equivalence for adjacent/gapped years,
  March/June periods, accounting-basis changes, and GDP period alignment.
- Source SHA-256:
  `f3883e9913a526dfc13b9ca09d58b09f1832f8f439f2fa55e9edec4a9bfdcb38`.
- Test SHA-256:
  `e2e7daeb6d50ef63e435599871728efad1e5d8ab47e5bed7d9c81d716d5d448f`.
- Functional and correction commits: `02d36bc`, `13e8d85`, `fbf710d`,
  `c867f97`, `50564fc`.

## Boundaries

This is a pure in-memory compatibility bridge. It does not verify persisted
file fixity, reopen a canonical package, execute analysis, assert new semantics,
evaluate rights, grant publication approval, or publish any data. Decimal
source scale 17 and canonical scale 18 can produce different string encodings;
the tests compare exact numeric values and retain the reversible identifier
substitution instead of claiming byte-equivalent analytical inputs.

The final cold-cache, one-worker, unfiltered mutation gate killed all 51 mutants
with zero survivors, errors, timeouts, pardons or cache hits (22 tests, 31.72
seconds). Its JSON report SHA-256 is
`fe3463021cfab67d0664679186e54793cac6895625bd13a7c07ae06f5944d14b` and
the retained log SHA-256 is
`b03da3b6179393e79a36292c3bc8c5117cb32a31023906b1384b4ea13656d6f0`.

The final native harness at `50564fc` exited zero: 4,615 tests passed with nine
existing resource warnings in 68.81 seconds and 97.53% overall coverage; 48
schemas / 38 representative documents, 9/9 parity checks, all repository
mutation and supply-chain gates, and the 111-component SBOM passed. Native log
SHA-256: `4b988cfe7a65ec04b6c166230303f84a091a1d65afba83e03f610087fa11e690`.

The preceding native attempt failed only at test-fixture static typing. Its
retained log SHA-256 is
`7d2dab72e4980c40aec1533a1e44f9787ffa33610089258650c0fb293abcbbba`;
full basedpyright and the final native harness pass after the annotation-only
correction. Retained-package replay, persisted canonical-reader support and
hosted delivery remain separate evidence events.
