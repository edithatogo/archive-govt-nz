# Track 15 Execution Plan: Consolidation Closeout and Operational Readiness

## Phases

### Phase 1: Re-Audit & Evidence Classification
- [x] Complete capability reconciliation in `docs/` and `evidence/`.
- [x] Complete evidence classification in `docs/` and `evidence/`.
- [x] Complete licensing and rights audit in `docs/migrations/sm-govt-nz/licensing-and-rights.md`.

### Phase 2: Workflow Route Table & State Normalization
- [x] Implement `config/migrations/sm-govt-nz/workflow-route-table.yml`.
- [x] Implement `evidence/migrations/sm-govt-nz/state-transfer-receipt.json`.

### Phase 3: Source Sets & Multi-Source Scheduling
- [x] Create `config/source-sets/` (`treasury.yml`, `government-web.yml`, `social-media.yml`, `newsletters.yml`).
- [x] Create `.github/workflows/scheduled-multi-source-harvest.yml`.

### Phase 4: CLI/MCP Parity & Contract Tests
- [x] Implement `src/archive_govt_nz/mcp_server.py`.
- [x] Add `tests/cli/test_mcp_cli_contract.py`.

### Phase 5: Real Operational Verification & Parity Reports
- [x] Generate `evidence/migrations/sm-govt-nz/parity/` receipts.
- [x] Generate `docs/migrations/sm-govt-nz/parity-report.md`.

### Phase 6: Core Architecture, Runbooks & Closeout
- [x] Update `README.md`.
- [x] Write `docs/architecture/` specs (`archive-architecture.md`, `source-adapters.md`, `publication-architecture.md`).
- [x] Write `docs/operations/` runbooks (`runbook.md`, `recovery.md`).
- [x] Write `docs/migrations/sm-govt-nz/consolidation-closeout-report.md` and `.json`.
- [x] Verify full 19-stage assurance suite and merge to main.
