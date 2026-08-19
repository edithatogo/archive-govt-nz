# Review: Standards-Conformant Stdio MCP Server

## Review Verdict: VERIFIED

- **MCP 2024-11-05 Specification**: Full lifecycle implemented, including handshake, notifications, tool invocation, and resource access.
- **Error Taxonomy**: Complies with standard JSON-RPC 2.0 error codes (`-32700`, `-32600`, `-32601`, `-32602`, `-32603`) and `isError: true` tool execution failure formatting.
- **Packaging & Entrypoint**: `archive-govt-nz-mcp` registered in `pyproject.toml` pointing to `archive_govt_nz.mcp_server:main`.
- **Quality Gates**: All 19 assurance stages in `tools/check.py` passed with 96.98% patch coverage.
