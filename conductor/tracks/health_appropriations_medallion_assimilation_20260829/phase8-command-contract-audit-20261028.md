# Phase 8 command contract audit — 2026-10-28

## Scope checked

Reviewed the Health CLI/MCP and scheduled-operation contracts against the
Phase 8.1 command matrix. The audit is deliberately a coverage report; it does
not treat existing tests as proof for commands or scheduled lanes that do not
exist yet.

The affected contract suites were run on repo-local Python 3.15.1:

```text
tests/cli/test_mcp_cli_contract.py
tests/cli/test_cli.py
tests/mcp/test_dynamic_domain_tools.py
tests/domains/health_appropriations/test_source_operations.py
tests/domains/health_appropriations/test_context_operations.py
tests/domains/health_appropriations/test_forecast_operations.py
tests/domains/health_appropriations/test_overview_operations.py
tests/domains/health_appropriations/test_rebuild.py
tests/domains/health_appropriations/test_resume_operations.py
tests/domains/health_appropriations/test_operation_context_gold_operations.py
tests/domains/health_appropriations/test_fiscal_analytical_operations.py
tests/domains/health_appropriations/test_operation_metadata_operations.py
tests/domains/health_appropriations/test_capture_checkpoint.py
tests/domains/health_appropriations/test_capture_process_recovery.py
tests/mcp/test_health_inspection.py
tests/health/test_scheduled_heartbeat.py
tests/tools/test_workflow_policy.py
```

Result: **820 passed, 10 skipped**. The skips are capability-gated in the
selected suites. `--no-cov` was used because this was a focused contract run,
not the integrated coverage/release gate.

## Evidence-supported coverage

- Status and inspect contracts cover CLI/MCP JSON, bounded inputs, redacted
  failures, and no-write behavior.
- Source and context operations cover typed source dispatch, preflight/dry-run,
  local writes, repeat builds, partial failures, and tamper rejection.
- Capture contracts cover interrupted execution, durable resume, retry history,
  exclusive ownership, and preservation of prior bytes.
- Rebuild/resume and Gold operation contracts cover plans, execution, readback,
  query receipts, and retained partial state.
- The scheduled-discovery policy test verifies `contents: read`, non-cancelling
  concurrency, no interpolated secrets, and that the scheduled job does not
  capture or normalize.

## Still open

- The existing scheduled job remains metadata discovery only. It provides no
  scheduled capture or normalization lane.
- The current workflow-policy test proves secrets are not interpolated in that
  discovery job; it does not exercise a missing-credential failure path for a
  credential-dependent operation.
- The broad Phase 8.1 checklist also names inspect, capture, normalize,
  reconcile, analyze, rebuild, candidate-build and status as one integrated
  command contract. This run does not establish that every family has matched
  CLI/MCP semantics, particularly capture-inventory reconciliation.
- This focused test run does not replace `./scripts/validate.sh` or the exact
  head hosted gates, and does not close Phase 8.

Next implementation remains a bounded CLI/MCP reconciliation surface for
already retained capture/layout evidence, followed by a separate design and
authority check for any scheduled capture lane. The existing scheduled
discovery workflow is unchanged.
