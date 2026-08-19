# Evidence: Weekly Legislation Orchestration and State Management

## Test Receipts
- Command: `uv run pytest --cov=tools.run_legislation_harvest tests/tools/test_run_legislation_harvest.py`
- Result: 6 passed in 1.45s (100% orchestrator patch coverage)
- Full Gate: `uv run --locked python tools/check.py`
- Result: 580 passed, all 19 stages green, 95.38% total coverage.

## Invariant Proofs
1. **Durable Checkpoints**: State is restored and atomically promoted only upon successful validation.
2. **Outcome Classification**: Accurately distinguishes `changed`, `no_change`, `partial_retryable`, and `failed`.
3. **Recovery Rehearsal**: Quarterly workflow executes clean workspace restore and CAS byte-level fixity checks.
