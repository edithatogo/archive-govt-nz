# Plan: Corrective Legislation Corpus Consolidation

## Phases & Deliverables

### Phase 0: Corrective Control Plane & Invalidation
- [x] Create corrective track and GitHub parent tracking issue.
- [x] Invalidate unsupported PR #124 receipts with explicit audit metadata.
- [x] Add automated test enforcing no-future-dated-receipt policy.
- [x] Produce `docs/migrations/corpus-legislation-nz/corrective-audit.md` and `.json`.

### Phase 1: Exact Live Inventory & Lineage Preservation
- [x] Generate exact programmatic inventory of `corpus-legislation-nz` (`live-inventory.json` & `.md`).
- [x] Import full donor Conductor tree into `conductor/archive/imported/corpus-legislation-nz/749918c251da59dc890c19dfda2ab9a021fd8ca6/`.
- [x] Map all donor tracks and open issues with realistic evidence classes.

### Phase 2: Domain Assimilation & Safe XML/HTML Parsing
- [x] Port and refactor mature donor modules into `src/archive_govt_nz/domains/legislation/` (`api.py`, `discovery.py`, `identity.py`, `models.py`, `normalise.py`, `validate.py`, `manifest.py`, `coverage.py`, `changes.py`, `checkpoints.py`, `bootstrap.py`, `corpus.py`, `publication.py`).
- [x] Replace regex normaliser with safe `xml.etree.ElementTree` parsing extracting true statutory types, dates, sections, and schedules.

### Phase 3: Real CLI, MCP & Source-Set Execution
- [x] Implement real CLI command execution against actual manifests and checkpoints.
- [x] Connect `nzlc` compatibility shim and MCP server (`archive_legislation`) to real domain engine.
- [x] Enforce typed states in scheduled harvest workflow.

### Phase 4: State Reconcile, Differential Parity & Quality Gates
- [x] Reconcile 68 historical batches and 33,693 seed work IDs with actual checksums.
- [x] Generate executable differential parity receipts with run IDs, hashes, and mismatch lists.
- [x] Implement fine-grained rights classifications.
- [x] Verify 100% of 19 assurance stages pass with >=95% branch coverage and 100% patch coverage.
