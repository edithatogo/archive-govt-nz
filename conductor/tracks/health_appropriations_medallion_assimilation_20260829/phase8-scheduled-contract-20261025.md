# Phase 8 scheduled Health discovery contract — 2026-10-25

The scheduled Health workflow is constrained to `contents: read`, has no
secret interpolation, and uses `cancel-in-progress: false` so an overlapping
run cannot discard in-flight evidence. Its named operational steps are metadata
discovery and the bounded heartbeat. The discovery step does not run capture or
normalization. The heartbeat remains evidence about workflow/discovery state;
it does not imply downstream completion.

This is a regression contract for the existing discovery-only workflow. It
does not implement or qualify scheduled capture/normalization, reconciliation,
or reconstruction. Those remain separate Phase 8 tasks, with source and rights
eligibility required before capture.

Validation on repo-local Python 3.15.1:

- `uv run --locked pytest tests/tools/test_workflow_policy.py::test_health_discovery_schedule_is_read_only_and_does_not_need_secrets -q --no-cov` — passed after correcting the initial test selector to account for the workflow's setup-python step.
- `uv run --locked ruff check tests/tools/test_workflow_policy.py` — passed.
- `uv run --locked ruff format --check tests/tools/test_workflow_policy.py` — passed.
- `./scripts/validate.sh` — passed: 8,408 tests, 14 skipped, 97.07% coverage
  against the 80% floor; 81 schemas/71 representative documents; parity 9/9;
  configured mutation, hygiene, dependency, licence, secret-scan and SBOM gates
  passed. The validation ran on this exact tree before commit.

The test characterizes the already-existing workflow; it does not change
workflow permissions, triggers, secrets, or collection behavior.
