# Phase 8 exclusive resume concurrency contract — 2026-10-25

Two callers are released from the same read-only preflight together and compete
to claim one output directory. Exactly one creates and completes the attempt;
the other is rejected by exclusive directory creation. The test independently
verifies the winning receipt, asserts no failure marker was written by the
loser, and confirms every file that existed before the race remains byte
identical.

The test characterizes the existing local-filesystem claim mechanism; it does
not add a distributed lock or claim safety against a hostile filesystem. It is
not evidence of remote source freshness or any rights/publication state.

Validation on repo-local CPython 3.15.1:

- `uv run --locked pytest tests/domains/health_appropriations/test_resume_execution.py::test_concurrent_invocations_claim_one_exclusive_attempt -q --no-cov` — passed.
- `uv run --locked pytest tests/domains/health_appropriations/test_resume_execution.py tests/domains/health_appropriations/test_resume_operations.py tests/domains/health_appropriations/test_rebuild_resume.py -q --no-cov` — 217 passed.
- `uv run --locked ruff check tests/domains/health_appropriations/test_resume_execution.py`, `uv run --locked ruff format --check tests/domains/health_appropriations/test_resume_execution.py`, and `uv run --locked basedpyright tests/domains/health_appropriations/test_resume_execution.py` — passed after removing an unnecessary assertion inside the expected exception handler.
- `./scripts/validate.sh` — passed on the exact local tree: 8,423 passed,
  14 skipped, 97% coverage (above the repository's 80% floor), schema and
  representative-document validation, parity, mutation, hygiene, dependency,
  licence, secret-scan and SBOM gates all passed. Runtime was repo-local
  CPython 3.15.1. Hosted exact-head checks are pending PR creation.

Interruption, replay, stale-state, remote-drift, whole-phase review and final
hosted assurance remain separate Phase 8 gates.
