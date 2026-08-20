# Evidence: Real Legislation CLI Service Integration and nzlc Compatibility

## Test Receipts
- Command: `uv run pytest --cov=archive_govt_nz.cli --cov=archive_govt_nz.cli_compat tests/cli/test_cli.py tests/cli/test_mcp_cli_contract.py`
- Result: 33 passed in 2.59s (96.42% CLI coverage)
- Full Gate: `uv run --locked python tools/check.py`
- Result: 590 passed in 31.13s (95.49% total branch coverage, all 19 stages green)

## Invariant Proofs
1. **Dynamic Coverage Sensitivity**: Manifest alteration directly changes candidate counts, retrieved counts, and coverage percentages.
2. **Missing State Honesty**: Absent manifests/checkpoints return `status="no_state"` and exit code 1 instead of fabricated 0% or 100%.
3. **Capture Redirection**: `capture --source-type legislation` rejects standalone queues with exit code 2 and redirect guidance.
4. **nzlc Parity**: `nzlc` entrypoint supports legacy commands with deprecation notice to stderr.
