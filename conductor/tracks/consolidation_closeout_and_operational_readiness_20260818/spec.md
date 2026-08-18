# Track 15 Specification: Consolidation Closeout and Operational Readiness

## Goal
To conclusively finalize, verify, and document the entire consolidation of `sm-govt-nz` into `archive-govt-nz`.

## Key Interfaces & Deliverables
1. **Evidence & Audit**:
   - `docs/migrations/sm-govt-nz/capability-reconciliation.md` & `.json`
   - `docs/migrations/sm-govt-nz/evidence-classification.md` & `.json`
   - `docs/migrations/sm-govt-nz/licensing-and-rights.md`
   - `evidence/migrations/sm-govt-nz/state-transfer-receipt.json`
2. **Workflow Route Table & Source Sets**:
   - `config/migrations/sm-govt-nz/workflow-route-table.yml`
   - `config/source-sets/` (`treasury.yml`, `government-web.yml`, `social-media.yml`, `newsletters.yml`)
   - `.github/workflows/scheduled-multi-source-harvest.yml`
3. **Parity & Operational Verification**:
   - `evidence/migrations/sm-govt-nz/parity/` (`source-feeds.json`, `source-bluesky.json`, `source-threads.json`, `source-youtube.json`, `source-email.json`, `replay-summary.json`, `live-target-summary.json`, `aggregate-parity.json`)
   - `docs/migrations/sm-govt-nz/parity-report.md`
4. **CLI & MCP Surface**:
   - Enhanced subcommands in `cli.py` & MCP server in `src/archive_govt_nz/mcp_server.py`.
   - Contract test suite `tests/cli/test_mcp_cli_contract.py`.
5. **Architecture, Runbooks & Closeout Reports**:
   - `docs/migrations/sm-govt-nz/consolidation-closeout-report.md`
   - `evidence/migrations/sm-govt-nz/consolidation-closeout-receipt.json`
   - `docs/architecture/archive-architecture.md`
   - `docs/architecture/source-adapters.md`
   - `docs/architecture/publication-architecture.md`
   - `docs/operations/runbook.md`
   - `docs/operations/recovery.md`
