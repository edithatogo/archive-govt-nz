# Requirements: Global CLI integrity correction

## Must

- **GCLI-M1** `replay` traverses the production sharded CAS layout and verifies
  objects through `ContentAddressedStore`, without loading whole objects into
  memory.
- **GCLI-M2** `archive verify` validates supported WARC/WACZ structure and
  fixity evidence; arbitrary filename-matched bytes never become `verified`.
- **GCLI-M3** `verify` executes real bitstream, schema, and provenance checks
  selected by explicit paths and never treats directory presence as integrity.
- **GCLI-M4** `provenance` accepts only a supported closed manifest or evidence
  ledger structure and rejects scalar or unrelated JSON.
- **GCLI-M5** `search` loads a real scope manifest, constructs the existing
  semantic index, executes the query, and returns non-zero for missing or
  corrupt index state.
- **GCLI-M6** `publish` uses the existing publication preparation backend and
  requires non-empty files, explicit destination identity, and unresolved
  rights/publication gates; token presence alone is not readiness evidence.
- **GCLI-M7** `doctor` enforces the repository Python 3.14 requirement and
  reports bounded runtime checks without claiming archive integrity.
- **GCLI-M8** JSON output remains deterministic, diagnostics use stderr, and
  public command exit codes remain within 0-5.

## Should

- **GCLI-S1** Preserve useful PR #150 command names, JSON fields, negative
  controls, and exit-code mappings where they remain truthful.
- **GCLI-S2** Keep legislation CLI work, MCP, workflow, publication authority,
  redistribution rights, live operation, recovery, cutover, and donor archival
  outside this track.

## Acceptance criteria

- Adversarial tests use production CAS writes, corrupt objects, garbage WARC,
  malformed provenance, missing/corrupt search manifests, empty staging, and
  token-only publication attempts.
- A full locked repository harness passes on the local successor branch.
- No successor PR is opened and no merge occurs while PR #156 remains open.
