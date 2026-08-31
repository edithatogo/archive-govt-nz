# FOI ownership and shadow comparison

`archive_govt_nz.foi_ownership` provides pure validation for the planned P6
handoff. It performs no network request, source capture, publication, scheduler
activation or mutation. Successful tests do not establish hosted cutover.

An `OwnerFence` identifies a source, repository owner, monotonically increasing
epoch, opaque lease ID and exclusive Unix expiry. `require_owner` rejects a
wrong owner, stale epoch, replaced lease and expired execution. Each action must
read the authoritative current record; a cached record cannot fence a delayed
job. A lease for one source must never be used to authorize another source.

`ShadowSnapshot` compares hashes of nine canonical projections: cases, events,
attachments, raw hashes, revisions, queues, checkpoints, retries and takedowns.
Both sides must identify the same source and retained capture digest. Every
projection is required, with no duplicate or extra dimension. Reordering the
projection names does not change the parity digest. Counts alone are inadequate:
equal counts can hide different objects. Projection construction and hosted
replay of retained evidence remain separate work. No origin needs to be fetched
again to implement these comparisons.

`propose_transfer(current, expected, proposed, now, evidence)` checks the entire
expected fence, a different owner and lease, the same source and exactly the next
epoch. The evidence must identify that source and epoch, zero active jobs,
quiescence and anonymous-restore receipt digests, and matching shadow snapshots.
Receipt hashes are references, not authenticated claims: the calling operator
must verify their contents, freshness, source/revision binding, successful status,
and accountable eligibility decisions before invoking this function. A syntactic
hash or an empty synthetic projection is not hosted evidence. The function does
not authorize raw publication or prove a country complete.

Rollback uses the same transition checks and increments the epoch again. It
never reinstates the former epoch or lease, so delayed pre-cutover jobs remain
invalid. Expired owners cannot be revived or automatically stolen through this
API. Recovery of an expired shared authority needs its own evidence-bound
operation and is not implemented here.

## Required hosted integration

Both repositories must use one authoritative, transactional compare-and-swap
store. Persist a proposal only against the exact read revision; discard and
reconcile conflicts. A local SQLite state store or repository-local GitHub
concurrency group alone cannot provide shared cross-repository ownership.

Checking immediately before an external action still has a time-of-check race.
Acquisition must drain or cancel all admitted jobs before the transfer, and
publication needs a sink that rejects stale epoch/lease tokens atomically with
its write, or a single fenced executor that serializes transfer and writes.
Re-reading a fence without such a sink is not sufficient. Keep both schedulers
paused until that integration and delayed-job rejection have hosted evidence.

Acceptance still requires retained-input shadow replay, anonymous cold restore
of eligible raw data, exact donor/receiver/publication revisions, a measured
rollback window and a scheduled incremental cycle without duplicate dispatch.
The historical NZ cursor is not a raw-coverage ledger: older queue credit must
be reconciled against inventories and retained original bytes before it can
contribute to completeness. Reacquisition can only fill those gaps after the
source's access, retention, redistribution and privacy decisions are resolved.
