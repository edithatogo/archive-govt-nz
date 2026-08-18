# Requirements: MCP Disposition and Conformance

## Disposition Contract
- Retain one archive-oriented read-only MCP surface in `src/archive_govt_nz/mcp_server.py`.
- Distinct boundary: standalone `edithatogo/legislation` MCP owns interactive retrieval and citations.

## Implementation Requirements
- Stdio transport (`StdioServerTransport`) and JSON-RPC 2.0 framing.
- Operational `Server` supporting `initialize`, `tools/list`, `resources/list`, and `tools/call`.
- Dynamic resource and tool inspections without hardcoded constants.
