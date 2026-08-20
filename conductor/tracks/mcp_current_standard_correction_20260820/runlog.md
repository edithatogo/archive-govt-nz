# Run log

- 2026-08-20: Audited the stacked base at `5c7ae9c`. Confirmed stale protocol
  advertisement, permissive initialization, pre-initialization service, invalid
  notification handling, absent cursor validation, incorrect resource errors,
  flat CAS discovery, and affirmative empty-store status.
- 2026-08-20: Added adversarial stable-protocol controls. The red run stopped at
  collection because the implementation did not define the MCP `-32002`
  resource-not-found error, before reaching the remaining expected failures.
- 2026-08-20: Implemented stable MCP 2025-11-25 initialization, lifecycle
  gating, notification silence, cursor and argument validation, JSON Schema
  2020-12 input/output contracts, protocol/domain error separation, and exact
  resource errors. Replaced flat CAS counting with canonical sharded discovery
  and streaming fixity verification.
- 2026-08-20: The first full harness run reported all 771 tests passing but
  crossed the fixed 180-second subprocess limit by 0.55 seconds before later
  gates. Raised the bounded gate ceiling to 300 seconds and added a harness
  policy test.
- 2026-08-20: Exact rerun completed all stages. The primary OSV request timed
  out at 60 seconds; the existing alternate audit returned no known
  vulnerabilities and the audit stage passed. Generated evaluator timestamps
  and donor snapshots were restored rather than committed as implementation
  evidence.
- 2026-08-20: Rebased the local MCP successor onto legislation CLI head
  `50bae20`. The exact stack passed 774 tests at 95.70% branch-aware coverage
  and all remaining harness gates. No branch was pushed and no PR, merge, live
  consumer, publication, rights action, or donor operation occurred.
- 2026-08-20T21:25:00Z: After legislation coverage PR #159 merged as
  `c16ad20`, rebased all six MCP correction commits onto exact `origin/main`
  without conflict. Rechecked the authoritative stable MCP 2025-11-25
  lifecycle and tools specification. The focused protocol suite passed 33
  tests with 100% line and branch coverage of `mcp_server.py`; the full locked
  harness passed 780 tests at 96.20% overall coverage and all remaining gates.
  Generated timestamp and donor-snapshot churn was restored. No live consumer,
  publication, rights, workflow, recovery, cutover, or donor action occurred.
