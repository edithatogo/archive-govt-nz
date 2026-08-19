# Requirements: MCP Protocol Server Conformance

Track: `legislation_corrective_mcp_disposition_conformance_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issue: [#136](https://github.com/edithatogo/archive-govt-nz/issues/136)

## MoSCoW Requirements

### Must
1. **Operational JSON-RPC 2.0 Protocol Runtime**:
   - Implement `StdioServerTransport` and `Server` in `src/archive_govt_nz/mcp_server.py` supporting `initialize`, `tools/list`, `resources/list`, and `tools/call`.
2. **Read-Only Archival Inspection Tools**:
   - Expose `archive_doctor`, `archive_capabilities`, `archive_sources`, and `archive_legislation` tools.
3. **No Simulated Fixed Numbers**:
   - Compute tool results dynamically from real system state and registries.
