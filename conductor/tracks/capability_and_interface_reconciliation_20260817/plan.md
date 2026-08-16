# Track 3 Plan: Capability and Interface Reconciliation

## Phases

### Phase 1: Deep Codebase Capability Comparison
- [ ] Inspect storage, hashing, manifests, and ledger implementations in both systems.
- [ ] Inspect all 9 capture adapter families (Bluesky, Threads, X, YouTube, RSS, Email, CKAN, Browser, Video).
- [ ] Inspect publication and distribution endpoints.

### Phase 2: Matrix Construction & Schema Validation
- [ ] Construct `capability-matrix.json` and validate against `capability-matrix-v1.schema.json`.
- [ ] Generate `capability-matrix.md` with complete rationale columns.

### Phase 3: Interface Surface Analysis
- [ ] Define CLI subcommand grammar and exit code contracts in `interface-map.md`.
- [ ] Evaluate MCP server utility and record deferral decision.
