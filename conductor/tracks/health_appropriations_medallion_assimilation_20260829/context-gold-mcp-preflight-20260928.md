# Context Gold MCP preflight

Added `health_appropriations_preflight_context_gold` as a typed read-only MCP tool. It accepts the caller's Silver root, source CAS root and not-yet-existing output path, invokes the existing Context Gold builder only with `write=False`, and returns the builder's planned product hashes, sizes, row counts, input counts and source marker pins. The tool schema requires a dry-run receipt, source-family separation, no denominator selection, rights `not_evaluated`, and publication `not_performed`.

The focused test calls the actual MCP server JSON-RPC handler after initialization, compares its structured result with the tool result, checks read-only annotations and absence of a write parameter, and verifies that the planned output path remains absent.

Validation: `uv run --locked python -m ruff check src/archive_govt_nz/mcp_server.py tests/domains/health_appropriations/test_context_gold.py`; `uv run --locked pytest tests/domains/health_appropriations/test_context_gold.py -q` (11 passed). Full `./scripts/validate.sh` passed: 7,074 tests passed, 9 skipped; 98.18% branch coverage; schemas 52/42; parity 9/9; mutation gates, benchmark, vulnerability audit, licence inventory, secret scan and SBOM gates passed. Hosted checks will be recorded after delivery.
