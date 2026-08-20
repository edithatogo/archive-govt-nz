# Evidence

## Focused protocol evidence

- Command: `uv run pytest --cov=archive_govt_nz.mcp_server --cov-branch --cov-report=term-missing tests/mcp/test_mcp_current_standard.py tests/cli/test_mcp_cli_contract.py tests/mcp/test_mcp_protocol.py`
- Result: 33 passed; `mcp_server.py` 228/228 statements and 84/84 branches,
  100.00% coverage.
- Both MCP conformance and disposition contracts validated independently.

## Repository gate

- Command: `bash scripts/validate.sh`
- Result: exit 0; lock, format, lint, types, 771 tests, schemas, all mutation
  lanes, hygiene, CAS benchmark, dependency audit, licences, secret scan, and
  SBOM passed. Overall test coverage was 95.72%.
- The primary OSV request timed out at 60 seconds. The repository's existing
  alternate vulnerability audit returned `No known vulnerabilities found`, so
  the audit stage completed successfully. This is bounded dependency evidence,
  not publication, rights, or operational authority.

No live MCP consumer, publication target, or donor operation was invoked.
