# Durable FOI queue transactions

`QueueRepository` binds a source-scoped `OwnerFence` and its scheduling `Queue`
in the same versioned state document. The `QueueStore` protocol accepts the local
SQLite store or the shared [GitHub authority](foi-github-state.md). Each backend
validates its own storage integrity before reads require exact v1 fields, counters
(including rejection of booleans), strings, collection shapes, scheduler
invariants and matching source identities. Unknown fields or versions fail
closed; no implicit migration or country-completion inference occurs.

`initialize(owner, queue, now)` creates only an unseen store key under a live
owner fence. `transact(version, owner, now, transition)` requires the exact
stored owner and version before evaluating a **pure** scheduling proposal. It
then compare-and-swaps the combined document. The transition must be trusted
application code calling the scheduler; it must not perform network, filesystem,
publication or dispatch side effects. A callback is not a sandbox or proof that
its result has acquisition authority. Executable adapters must enforce the
source eligibility and verified receipt requirements separately.

`transfer(version, owner, proposed, now, evidence)` additionally requires that
no queue job is leased, then applies the ownership module's parity, restore and
quiescence checks. Queue contents remain unchanged during the atomic owner
transition. Rollback is another evidenced transition with an increasing epoch;
it does not restore an old token. An expired capture lease blocks transfer until
its terminal outcome is reconciled explicitly. Old versions and owner tokens
cannot mutate the newly persisted generation.

A process can reopen the store and recover the last complete committed state.
A concurrent writer causes a conflict instead of replacing its state. A crash
after persistence and before dispatch leaves a reserved job requiring exact
lease reconciliation, not automatic queue credit. A crash before commit has no
queue mutation. State history is bounded by `StateStore`; storage exhaustion
fails rather than discarding old evidence.

The wrapper itself is not deployment or cutover evidence. Both repositories
must consult the shared authority and enforce sink-side fences before actual
cutover. Local SQLite files copied between hosts do not provide that property.
Cumulative run/day quotas, live source capture execution, source
policy resolution, remote artifact verification and publication remain separate
integration work. Per-origin fairness across multiple source documents also
requires a shared dispatcher; this source-scoped wrapper cannot claim global
fairness or prevent remote duplicate capture by itself.
