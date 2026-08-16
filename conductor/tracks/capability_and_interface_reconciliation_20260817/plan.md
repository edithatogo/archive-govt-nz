# Track 3 Plan: Capability and Interface Reconciliation

## Phases

### Phase 1: Deep Codebase Capability Comparison
- [x] Inspect storage, hashing, manifests, and ledger implementations in both systems.
- [x] Inspect all 9 capture adapter families (Bluesky, Threads, X, YouTube, RSS, Email, CKAN, Browser, Video).
- [x] Inspect publication and distribution endpoints.

### Phase 2: Matrix Construction & Schema Validation
- [x] Construct `capability-matrix.json` and validate against `capability-matrix-v1.schema.json`.
- [x] Generate `capability-matrix.md` with complete rationale columns.

### Phase 3: Interface Surface Analysis
- [x] Define CLI subcommand grammar and exit code contracts in `interface-map.md`.
- [x] Evaluate MCP server utility and record deferral decision.
