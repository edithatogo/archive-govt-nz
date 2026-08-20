# Run log

- 2026-08-20: Confirmed scheduled harvest could return `no_change` without
  discovery, synthesize sequential 2024 targets, promote an unlinked
  checkpoint, and retain receipts without durable CAS/manifest/checkpoint state.
  Confirmed reconciliation and recovery false-success exits and flat recovery
  CAS assumptions. No workflow was dispatched.
- 2026-08-20: Replaced synthetic backfill targets with bounded service discovery
  through `sync_works`; partial and failed service outcomes now return non-zero.
  Reconciliation authenticates discovered inventory and linked CAS/checkpoint
  state; recovery streams verified sharded objects into a clean CAS.
- 2026-08-20: Removed all recurring triggers and OIDC permissions. Added an
  unconditional code-3 gate before checkout in every hosted legislation job so
  prepared artifact mechanics cannot distribute CAS bytes while sequence and
  redistribution authority remain pending.
- 2026-08-20: Focused workflow/service state suite passed (103 tests). Full
  repository validation completed with 773 tests, 95.72% coverage, all schema
  and mutation gates, direct OSV dependency audit, licences, secrets, and SBOM.
  No hosted job or source request was executed.
- 2026-08-20: Rebased the local workflow successor onto MCP head `58cd63d`.
  The exact stack passed 775 tests at 95.70% branch-aware coverage and every
  remaining harness gate. The hosted jobs remain unconditionally gated before
  checkout; no push, PR, dispatch, source request, publication, or rights
  action occurred.
- 2026-08-20T21:45:00Z: MCP PR #160 squash-merged as `086eb4f`. Rebased the
  four workflow correction commits onto exact `origin/main` without conflict.
  Confirmed all three legislation workflows remain manual-only, retain an
  unconditional code-3 gate before checkout, and preserve
  `rights_class: review_required`. Twenty-six focused tests passed; the full
  locked harness passed 781 tests at 96.20% branch-aware coverage and every
  remaining gate. Generated timestamp and donor-snapshot churn was restored.
  No workflow dispatch, source request, live batch, publication, rights,
  recovery, cutover, or donor action occurred.
