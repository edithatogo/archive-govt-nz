# Read-only Gold metadata verifier through CLI and MCP

Phase 8 adds paired, non-interactive verification commands for an already
written local Gold metadata package. Both interfaces require explicit Fiscal
and Budget input directories and manifest SHA-256 pins, the metadata output
directory, and its manifest SHA-256 pin. The verifier reconstructs metadata
from the pinned inputs, checks the exact output inventory and bytes against the
metadata manifest, and returns the same structured receipt through CLI and MCP.

The MCP tool is annotated read-only, idempotent, closed-world, and non-
destructive. It exposes no write flag or credential input. A successful receipt
states `rights: not_evaluated`, `publication: not_performed`, and verification
scope `gold_reverified_metadata_reconstructed`; it is package verification,
not source re-verification or release approval. Missing, altered, or mismatched
inputs fail through the existing closed verifier contract.

## Verification

- Focused metadata, CLI/MCP contract, and dynamic-domain suites: 25 passed.
- The new contract test compares CLI and MCP receipts and confirms exact bytes
  in both Gold input packages and the metadata output are unchanged.
- Ruff format, Ruff lint, and basedpyright passed for the changed Python files.
- `./scripts/validate.sh` passed: 7,490 tests passed, 10 skipped; 97.77%
  coverage against the 80% floor; 56 schemas and 46 representative documents;
  parity 9/9; configured mutation, hygiene, benchmark, dependency, licence,
  secrets, and SBOM checks passed.
