# Evidence: Standards-Conformant Stdio MCP Server

## Test Receipts
- Command: `uv run pytest --cov=archive_govt_nz.mcp_server tests/cli/test_mcp_cli_contract.py tests/mcp/test_mcp_protocol.py`
- Result: 15 passed in 1.95s (96.98% MCP patch coverage)
- Full Gate: `uv run --locked python tools/check.py`
- Result: 587 passed in 34.78s (95.38% total branch coverage, all 19 stages green)

## Invariant Proofs
1. **Stdio Subprocess Handshake**: Real subprocess client successfully executes `initialize`, `notifications/initialized`, `ping`, and tool execution over stdin/stdout.
2. **Dynamic Inspection Without Fixed State**: `archive_status` dynamically inspects CAS storage and seed counts without hardcoded `active: true`.
3. **Structured Protocol Errors**: Malformed JSON yields `-32700`, missing method yields `-32601`, invalid parameters yield `-32602`, and tool runtime errors return `isError: true`.
4. **Clean Process Termination**: Subprocess gracefully exits with returncode 0 upon stream close (EOF).
