# Plan: MCP Protocol Server Conformance

1. **Phase 1: JSON-RPC 2.0 Protocol Engine**
   - Implement `StdioServerTransport` and request router.
2. **Phase 2: Tool Registry & Dynamic Dispatch**
   - Register inspection tools without fixed static constants.
3. **Phase 3: Automated Protocol Contract Testing**
   - Verify stdio request/response handling under `tests/cli/test_mcp_cli_contract.py`.
