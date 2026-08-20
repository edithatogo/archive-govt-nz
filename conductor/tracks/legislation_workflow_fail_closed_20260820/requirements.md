# Requirements

- **WF-1** Remove recurring legislation schedules until the one-batch and canary
  gates have produced valid evidence.
- **WF-2** Require explicit confirmation, a non-empty batch identity, discovery
  search terms, and a positive bound for capture dispatch.
- **WF-3** Route acquisition only through `LegislationArchiveService.sync_works`
  discovery, adapter, cumulative manifest, and checkpoint logic.
- **WF-4** Never synthesize work, expression, or manifestation identities.
- **WF-5** Restore an explicitly identified prior full-state artifact for
  continuation and upload CAS, manifest, checkpoint, and receipts together.
- **WF-6** Treat partial, inconsistent, no-state recovery, and corrupt/unlinked
  state as non-zero failures.
- **WF-7** Use the canonical sharded CAS and streaming dual-hash verifier.
- **WF-8** Do not grant OIDC or expose publication/rights operations. Keep
  publication, rights, live schedule, recovery, cutover, and donor archival
  pending.

