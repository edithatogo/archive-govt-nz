# Requirements: Testing Modernization and Performance Frontier

## Must

- **REQ-MUT-001:** Lock `pytest-gremlins` to the compatible `1.x` series in
  the development dependency group.
- **REQ-MUT-002:** Configure deterministic mutation targets, all supported
  mutation operators, JSON and console reporting, coverage-guided selection,
  incremental caching, and a fail-closed pardon budget.
- **REQ-MUT-003:** Provide a repository-owned runner and focused tests that
  emit a bounded machine-readable mutation receipt.
- **REQ-PAR-001:** Support race-free parallel pytest execution with explicit
  process isolation.
- **REQ-PROP-001:** Exercise URN, multihash, schema, and statutory-matcher
  invariants with property-based tests.
- **REQ-PROF-001:** Provide a bounded Scalene profiling harness and structured
  receipt for the Medallion pipeline.
- **REQ-GATE-001:** Integrate the new assurance stages and pass the full locked
  repository validation harness.

## Should

- **REQ-PERF-001:** Record comparable timing evidence without claiming a
  performance improvement that has not been measured on the same host.

## Could

- **REQ-CACHE-001:** Reuse mutation results for unchanged source and test
  content where cache integrity can be established.

## Acceptance criteria

1. Dependency and configuration contracts are machine-tested.
2. Mutation, parallel, property, and profiling lanes fail closed and emit
   deterministic receipts without secrets or host-specific paths.
3. Focused tests, formatting, linting, typing, schemas, supply-chain checks,
   and the full repository harness pass before track completion.
4. Local validation is reported separately from hosted execution or release.
