# Implementation Plan: Multi-Source Capture Path Activation

### Phase 1: Disposition decision and routing map [x]
- [x] Task: Audit which domain pipelines already work in production and decide implement-vs-reroute per source set; record the decision with evidence.
  Decision (2026-08-24): implement a config-driven capture path in the CLI
  (`archive-govt-nz capture`) that loads `config/source-sets/<set>.yml`, performs
  real bounded URL captures into CAS, reports non-URL adapter capabilities as
  explicit `capability_pending` entries, and redirects source sets with dedicated
  verified workflows (nz-gazette -> `scheduled-gazette-harvest.yml`). Legislation
  keeps its existing redirect to `legislation sync`.
- [x] Task: Update `config/migrations/sm-govt-nz/workflow-route-table.yml` target commands to match the decision.
  Route-table `verification_evidence` pointers must reference parity receipts;
  completion is tracked alongside Phase 2 activation follow-ups and
  `assimilation_parity_gate_hardening_20260824`.

### Phase 2: Activation [~]
- [x] Task: Implement or re-route; keep fail-closed semantics for unimplemented sources.
- [ ] Task: Point each updated route's `verification_evidence` at a real parity receipt rather than adapter source files.
- [x] Task: Add/extend focused tests covering the chosen path.

### Phase 3: Verification [ ]
- [ ] Task: One green scheduled (or workflow_dispatch) cycle across all five source sets with receipts retained.
- [ ] Task: Conductor review and phase gate verification.
