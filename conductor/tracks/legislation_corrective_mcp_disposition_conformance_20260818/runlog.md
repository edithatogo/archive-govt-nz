# Run Log: Standards-Conformant Stdio MCP Server

- Implemented full MCP 2024-11-05 protocol lifecycle in `src/archive_govt_nz/mcp_server.py`:
  - Standard JSON-RPC 2.0 transport with error code taxonomy (`-32700`, `-32600`, `-32601`, `-32602`, `-32603`).
  - Handshake: `initialize` and `notifications/initialized`.
  - Tools inspection: `tools/list` with JSON Schema Draft 2020-12 input definitions.
  - Tools execution: `tools/call` with `structuredContent` and `isError` handling.
  - Resources: `resources/list` and `resources/read` for `archive://capabilities`, `archive://sources`, and `archive://status`.
  - Clean stdio process shutdown on EOF.
- Removed unconditional `active: true` in `archive_status` tool; replaced with dynamic storage state inspection.
- Registered executable entrypoint `archive-govt-nz-mcp` in `pyproject.toml`.
- Added comprehensive subprocess client and protocol suite in `tests/mcp/test_mcp_protocol.py` and `tests/cli/test_mcp_cli_contract.py`.
- Passed all 19 validation stages in `tools/check.py` (587 passed, 95.38% total coverage, 96.98% MCP patch coverage).
