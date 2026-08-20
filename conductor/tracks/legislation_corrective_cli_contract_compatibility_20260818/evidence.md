# Evidence: CLI Contract and Non-Affirmative State Compatibility

## Executed Commands & Test Receipts

- `uv run pytest --cov=archive_govt_nz.cli tests/cli/test_cli.py tests/cli/test_mcp_cli_contract.py`: 23 passed in 1.61s, 99.43% branch coverage.
- `uv run python tools/validate_contracts.py`: All 15 YAML contracts validated.

## Invariants Verified

- **No Fictitious Statuses**: Removed simulated queue states, unconditional verification claims, and fabricated counts.
- **Negative Controls**:
  - `capture` returns exit code 2 and `status="not_configured"` on standalone invocation without daemon.
  - `archive` returns exit code 1 and `status="no_state"` when directory or WARC files are missing.
  - `replay` returns exit code 1 and `status="no_state"` when CAS store is missing, and detects corrupted objects.
  - `provenance` returns exit code 1 and `status="no_state"` when ledger file is missing.
  - `publish` returns exit code 2 and `status="not_configured"` when staging dir or publication tokens (`HF_TOKEN`, `ZENODO_TOKEN`) are absent.
- **Taxonomy Compliance**: Exit codes adhere strictly to documented 0–5 taxonomy. Diagnostics directed to `stderr`, structured data directed to `stdout`.
