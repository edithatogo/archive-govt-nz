# Plan: Standards-Conformant Stdio MCP Server

1. **Phase 1: MCP SDK & Stdio Lifecycle Engine**
   - Add `mcp>=1.0.0` dependency to `pyproject.toml` or implement robust standards-compliant JSON-RPC 2.0 stdio server in `src/archive_govt_nz/mcp_server.py`.
   - Implement `initialize`, `notifications/initialized`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, protocol errors, and clean shutdown.
2. **Phase 2: Tool Registry & Dynamic Evidence Dispatch**
   - Implement `archive_doctor`, `archive_capabilities`, `archive_sources`, and `archive_status` without unconditional `active: true`.
   - Support `structuredContent` and `isError` on tool execution failures.
3. **Phase 3: Entrypoint Packaging**
   - Expose `archive-govt-nz-mcp` CLI script in `pyproject.toml`.
4. **Phase 4: Client & Subprocess Protocol Verification**
   - Implement comprehensive protocol test suite in `tests/mcp/test_mcp_server.py` and `tests/cli/test_mcp_cli_contract.py`.
5. **Phase 5: Full 19-Stage Gate & Evidence Generation**
   - Run `tools/check.py`, verify >=95% patch coverage, and record evidence receipts.


## 2026-08-30 record preservation

- [x] Preserve the original historical plan verbatim in [plan.original.md](plan.original.md) and record its hash.

The checkbox above records preservation only. Original phase prose has no individual task checkmarks; this reconciliation does not assert or reverify its historical completion. Existing completion claims remain attributable to the original record.
