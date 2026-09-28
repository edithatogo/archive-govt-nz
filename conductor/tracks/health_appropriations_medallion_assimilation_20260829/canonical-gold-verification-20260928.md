# Read-only canonical Gold package verification

The Health CLI and MCP now expose a verifier for the canonical Gold manifest.
The caller supplies the local package directory and expected manifest SHA-256.
The verifier checks a bounded manifest, its canonical Gold schema version, the
exact output inventory, every declared direct-child output's size and digest,
and the presence of the temporal coverage report. It returns compact counts and
product names; parser, path, and fixity failures produce one redacted failure
receipt. It creates or changes no state.

This is a package fixity check. It does not reread Parquet semantics, establish
source completeness or rights, approve measures, or publish data.

## Verification

- Focused verifier tests: 17 passed with 100% statement and branch coverage.
- Contracts cover CLI/MCP and JSON-RPC parity, malformed manifests, duplicate
  keys, wrong pins, missing/extra/tampered outputs, byte limits, stable redacted
  failures, and no-write behavior.
- Full `./scripts/validate.sh` passed: 7,073 tests passed, 9 skipped,
  98.17% branch coverage; 52 schemas/42 representative documents and parity
  9/9 passed; mutation, hygiene, benchmark, dependency, license, secret, and
  SBOM gates passed.
- Hosted pull-request checks are recorded after delivery.
