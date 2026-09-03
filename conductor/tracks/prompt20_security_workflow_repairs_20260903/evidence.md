# Evidence

## Local evidence

- Baseline: `dcc8f37f5642fc6b4337c49bd482b126325e6b6c`.
- Functional commit: `4040f79`.
- `uv run pytest tests/test_notifications.py
  tests/tools/test_workflow_policy.py -q`: 10 passed.
- Notification-focused coverage: 100% line and branch coverage.
- Ruff, Ruff format, Pyright: passed.
- actionlint 1.7.12 across all workflow YAML: exit 0, `[]`.
- First full harness attempt: failed solely on two Hypothesis timing flakes
  after 4,543 passing tests; failure retained in the run log.
- Isolated retry of both failed tests: 2 passed.
- Second `./scripts/validate.sh`: passed with 4,545 tests and 97.50% coverage;
  all schemas, parity, registered mutations, dependency, licence, secret, and
  SBOM gates passed.

## Hosted evidence

Pending exact-head GitHub Actions and CodeQL readback. Local success does not
close CodeQL alerts until GitHub analyzes the exact PR head.
