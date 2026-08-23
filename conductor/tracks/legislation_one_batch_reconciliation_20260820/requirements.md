# Requirements

## Must

- **BATCH-M1** Remove the generator that fabricates fixture, historical,
  live-smoke, publication, and aggregate parity success.
- **BATCH-M2** Accept exactly one explicit donor batch file, its expected
  canonical SHA-256, a target cumulative manifest, the linked checkpoint, and
  the target CAS. Missing, empty, duplicate, malformed, or unauthenticated
  input fails closed.
- **BATCH-M3** Require every donor-batch work identity to be present in the
  authenticated discovered inventory, processed checkpoint, and target
  manifest with non-empty canonical work, expression, and manifestation
  identities.
- **BATCH-M4** Recompute manifest and discovered-inventory roots, verify their
  checkpoint linkage and counters, and stream-verify every selected target CAS
  object including SHA-256 and BLAKE3 agreement.
- **BATCH-M5** Report `passed` only when the named batch is completed and every
  selected work reconciles without mismatch. Failure writes a bounded failure
  receipt and returns non-zero; no missing input or offline state is success.
- **BATCH-M6** Perform no source fetch, synthetic normalization, publication
  preparation, remote readback, or other network/write side effect beyond the
  explicit local receipt path.
- **BATCH-M7** Preserve the merged generated receipts as invalidated historical
  evidence rather than treating them as current reconciliation proof.

## Should

- **BATCH-S1** Use versioned JSON Schema for the receipt and deterministic,
  sorted mismatch/error fields.
- **BATCH-S2** Keep the real-batch execution, canary, weekly cycles,
  publication, rights, recovery, cutover, and donor archival gates unresolved.

## Acceptance criteria

- Adversarial tests cover missing files, wrong batch hash, duplicate batch
  identities, corrupt manifest/checkpoint roots, incomplete batch accounting,
  missing FRBR identities, absent/corrupt CAS objects, BLAKE3 mismatch, and a
  valid cumulative-state reconciliation.
- Critical reconciliation logic reaches 100% line and branch coverage.
- The full locked repository harness passes on the local stacked branch.
- No branch is pushed, no PR is opened, and no live batch is claimed while the
  earlier ordered corrections remain pending.
