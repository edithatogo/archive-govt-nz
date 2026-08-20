# Requirements

## Must

- **LCLI-M1** Route `sync` through `LegislationArchiveService.sync_works`; do
  not duplicate acquisition, normalisation, manifest, or checkpoint logic.
- **LCLI-M2** Require an explicit bounded work list or discovery term and an
  explicit batch identity. Never inject a fabricated default work.
- **LCLI-M3** Validate manifests, authenticated discovered-inventory roots,
  checkpoint linkage, canonical records, and sharded CAS objects before
  reporting valid, ready, covered, or operational state.
- **LCLI-M4** Derive coverage from the authenticated discovered inventory and
  manifested unique work IDs. Empty or unauthenticated state is non-zero.
- **LCLI-M5** Treat discovery errors and empty inventories as non-success.
- **LCLI-M6** Do not call an unprobed runtime `healthy`, an absent change ledger
  `observed`, a manifest-only plan `staged`, or token presence `verified`.
- **LCLI-M7** Keep publication and redistribution-rights tracks unresolved;
  CLI planning and verification are read-only and fail closed.
- **LCLI-M8** Preserve JSON stdout, stderr diagnostics, and exit codes 0-5.
- **LCLI-M9** Preserve only truthful `nzlc` mappings; unknown legacy actions
  return usage error instead of silently invoking status.

## Acceptance

- Adversarial tests cover fabricated defaults, corrupt roots, manifest and
  checkpoint divergence, flat-CAS false positives, empty discovery, transport
  failure, token-only publication attempts, and unknown compatibility actions.
- Critical new CLI state logic reaches 100% line and branch coverage.
- The full locked repository harness passes locally.
- No push, PR, merge, live batch, publication, or donor archival occurs.
