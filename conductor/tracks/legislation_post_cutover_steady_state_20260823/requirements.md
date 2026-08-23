# Requirements: Legislation Post-Cutover Production Steady-State Operations

## Background & Rationale
With the migration, canary verification, and donor archival of `corpus-legislation-nz` successfully completed, the temporary safe-state (`dispatch_only` and transitional contracts) must be promoted to the intended production steady-state operational cadence.

## Cadence Invariants
| Function | Production Cadence | Trigger Modes |
| :--- | :--- | :--- |
| **Incremental Legislation Archive** | Weekly (`0 18 * * 0`) | `schedule` + `workflow_dispatch` |
| **Inventory & Publication Reconciliation** | Monthly (`0 6 1 * *`) | `schedule` + `workflow_dispatch` |
| **Disaster Recovery Rehearsal** | Quarterly (Operator-Gated) | `workflow_dispatch` only |
| **Generic Multi-Source Pipeline** | Excluded | Never run on 6-hour generic cron |

## Key Deliverables
1. **Contract Versioning**: Promote `contracts/schedule/legislation-archive-slo.contract.yaml` to Version `2.0.0`.
2. **Workflow Scheduling**: Add genuine weekly cron (`0 18 * * 0`) to `scheduled-legislation-harvest.yml` and monthly cron (`0 6 1 * *`) to `monthly-legislation-reconciliation.yml`.
3. **Source-Set Configuration**: Update `config/source-sets/legislation.yml` to declare `execution_mode: "scheduled_and_dispatch"` and `schedule: "weekly"`.
4. **Verification & Completion Evidence**: Update static workflow tests and verify independent completion evaluation.
