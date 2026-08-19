# Requirements: Standards-Conformant Stdio MCP Server

Track: `legislation_corrective_mcp_disposition_conformance_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issue: [#136](https://github.com/edithatogo/archive-govt-nz/issues/136)

## MoSCoW Requirements

### Must
1. **Official MCP Specification & Stdio Lifecycle Conformance**:
   - Implement standard MCP 2024-11-05 protocol lifecycle:
     - `initialize` (protocol version negotiation, server info, capabilities)
     - `notifications/initialized` (post-initialization notification handling)
     - capability negotiation (`tools`, `resources`)
     - `tools/list` (with JSON Schema `inputSchema` properties)
     - `tools/call` (with `structuredContent` or standard content blocks and `isError` flags)
     - `resources/list` and `resources/read` (with MIME types and text payloads)
     - structured JSON-RPC 2.0 protocol error codes (`-32600`, `-32601`, `-32602`, `-32603`)
     - clean process shutdown and EOF handling.
2. **Eliminate Fabricated/Affirmative Constants**:
   - Remove unconditional `active: true` and fake statuses.
   - Dynamically compute storage statistics, seed counts, and health status.
3. **Executable Entrypoint**:
   - Expose executable stdio MCP entrypoint (`archive-govt-nz-mcp` and `archive_govt_nz.mcp_server:main`).
4. **Tool Scope Boundaries**:
   - Preserve read-only archival inspection tools (`archive_doctor`, `archive_capabilities`, `archive_sources`, `archive_status`).
   - Do not add uncontracted legislation tools or mutation/publication tools in this tranche.
5. **Rigorous Client/Subprocess Test Harness**:
   - Test full lifecycle and tools using standard JSON-RPC subprocess and stream client harnesses.
