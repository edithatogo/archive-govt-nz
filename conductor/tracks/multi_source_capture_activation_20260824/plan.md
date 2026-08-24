# Implementation Plan: Multi-Source Capture Path Activation

### Phase 1: Disposition decision and routing map [ ]
- [ ] Task: Audit which domain pipelines already work in production and decide implement-vs-reroute per source set; record the decision with evidence.
- [ ] Task: Update `config/migrations/sm-govt-nz/workflow-route-table.yml` target commands to match the decision.

### Phase 2: Activation [ ]
- [ ] Task: Implement or re-route; keep fail-closed semantics for unimplemented sources.
- [ ] Task: Add/extend focused tests covering the chosen path.

### Phase 3: Verification [ ]
- [ ] Task: One green scheduled (or workflow_dispatch) cycle across all five source sets with receipts retained.
- [ ] Task: Conductor review and phase gate verification.
