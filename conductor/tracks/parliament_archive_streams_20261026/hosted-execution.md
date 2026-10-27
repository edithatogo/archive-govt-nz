# GitHub Actions continuation

User direction, 27 October 2026: move eligible Parliament backfill to continuous,
batched and interruptible Actions execution. This extends the active parent;
it does not qualify unrestricted submissions or declare the archive complete.

## Current verified boundary

Collection currently executes on the PortableSSD worktree. GitHub Actions has
provided CI, not Parliament acquisition. The existing repository HF_TOKEN secret
is present; its exact-target write permission from an Actions runner is not yet
proved. No self-hosted runner is registered. Do not install a public-repository
runner on the user's workstation as a shortcut.

The local state remains authoritative until an explicitly verified handover.
Readiness inventory is `build/parliament/hosted-handoff-20261027/readiness.json`.
All 877 CAS objects referenced by the 799 report records (798 originals and one
metadata-only record) have existing verified, pinned public batch references,
covering 250036289 bytes. Another 119 unreferenced CAS objects were excluded from
the inventory; they include unqualified author/source evidence. These counts are
a dated observation, not a fixed export allowlist or full-archive denominator.

## Required behavior

- Use actual repo-selected CPython 3.15.1 and the locked environment on hosted
  runners. Keep immutable action references, trusted-main execution and the
  existing required-check/solo-maintainer delivery policy.
- Run serially under one Parliament workflow concurrency group. Set
  cancel-in-progress false. Cancellation must stop acquisition and leave a
  recoverable state; an interrupted invocation must never claim completion.
- Preserve each acquisition bound: at most 100 observed records, 262144000 bytes,
  900 acquisition seconds; retained state plus verification headroom below8GiB.
- Execute multiple checkpointed batches per finite job, then resume in another
  scheduled/explicit run. GitHub-hosted job limits make one unlimited job
  unsuitable. A stop/pause must be honored at the next safe checkpoint.
- Keep all eligible output and public control state in the PUBLIC, UNGATED
  edithatogo/archive-govt-nz-global repository. Never create/select a private
  fallback. Keep README/YAML and other archive namespaces intact.
- Use a typed report-only state projection, validated field-by-field, plus
  content-addressed references. Never recursively upload the local state root,
  raw SQLite file, unqualified author HTML, local rights research or SDK logs.
- Bootstrap report object references from existing verified public batches.
  Preserve exact original bytes, observation/version associations, immutable
  receipts, publication state and cursor semantics. No invented URLs or payloads.
- Durability is an acceptance boundary: cursor/accepted-capture promotion must
  follow durable immutable object storage and independent anonymous pinned hash
  verification. Keep incomplete/unaccepted transfers explicit. Process-local
  success or an expiring Actions artifact is not durable acceptance.
- Register a prepared publication checkpoint before mutation; recover unknown
  outcomes by immutable namespace/hash readback, without blind write retries.
  Recover pending publication before any new discovery.
- Fence ALL source/publication writers, including local continuations, with a
  shared generation/owner lease and parent-bound writes. Concurrency within
  Actions alone does not exclude the existing desktop worker.
- Keep disk bounded through qualified retirement of hosted working copies only
  after exact remote restore proof. Keep original immutable remote objects and
  local SSD history. Never delete unverified spool to obtain more capacity.
- Alternate historical/recent lanes. Keep forward cursor and deep reconciliation
  cursor separate; a page-one anchor must not reset the deep sweep. Periodically
  revisit the known attachment-free business with an explicit page-one query.
  Exhausted cursors are observations, not completeness assertions.
- Stop on genuine failures, access restrictions, exhausted disk/budgets or rights
  uncertainty. Record sanitized failure evidence. No automatic permission
  expansion, blanket submissions clearance, section59 publication or repeated
  unchanged-denial probes. Exact selective submissions qualification remains a
  distinct reviewed lane, not an unrestricted hosted crawler.

## Acceptance and delivery

1. Qualify report-only projection and reject adversarial/unqualified state.
2. Prove cold restore, hashing, missing-object failure, cursor/version retention
   and pending-publication recovery using isolated fixtures and a disposable
   local restore. Do not mutate the authoritative SSD state during tests.
3. Prove interruption at discovery, object durability, prepared/uploaded/verified
   publication and checkpoint promotion; fence stale concurrent writers.
4. Prove spool accounting/qualified working-copy retirement and preserved card.
5. Complete focused tests, required milestone assurance and Conductor review;
   apply fixes and deliver only through green required GitHub checks.
6. Bootstrap the exact reviewed checkpoint to the approved public target. Verify
   anonymous pinned state/object hashes. Then perform a bounded native Actions
   pilot and interruption/resumption proof with actual HF secret binding.
7. Compare runner proof with native readback, pause local mutation, atomically
   hand over authority and only then enable continuous scheduled batches.
8. Keep manual dispatch, natural scheduling, interruption recovery and coverage
   acceptance distinct. Keep this parent active until its remaining rights,
   coverage, reconciliation and operational acceptance requirements are met.

Hosted collection is NOT configured or enabled at this planning checkpoint.

## Implementation candidate, 27 October 2026

The candidate uses one ten-record catalogue page per small attempt, alternating
recent and historical lanes. Eight of every ten historical attempts advance the
forward cursor; one continues the separate deep sweep and one revisits the known
attachment-free title from page one. Recent pages1–10 cycle independently. A
pending queue drains before new discovery. These are bounded observations, not
coverage or completeness claims.

A parent-bound public pointer fences ownership. Each immutable gzip snapshot
contains typed report rows, sanitized events, exact candidate shards and public
object references. New objects and the uploaded snapshot pointer commit together;
fresh anonymous pinned hash/length readback precedes a verified pointer. Unknown
outcomes recover from that pointer rather than replaying native mutations.
Originals checkpoint individually, before accepted capture promotion. Interrupted
acquisition attempts close with their full byte/time budget conservatively charged;
accepted originals publish before any new bounded attempt drains the remaining
queue. Immutable snapshots retain accounting and publication checkpoints.

The SSD marker freezes its original state at bootstrap. Legacy CLI acquisition
checks the shared pointer before source access; native publication checks the
current owner even from another local state root. Only restored hosted working
copies with qualified immutable remote references can retire scratch files.

Native acceptance requires a cold-verification run, a deliberately cancelled
pilot after its durable discovery checkpoint, and a successful recovery whose
receipt references that exact cancelled run/attempt. All three must use the
current main head. Only then can the operator enable the public pointer. Workflow
schedules remain harmless no-ops before bootstrap/enable. The existing HF secret
value is never handled in evidence. This remains an unmerged implementation
candidate; native handover and schedule acceptance are pending.

Operational recovery: `verify` may inspect/accept a paused uploaded checkpoint
without source access. After reviewing and fixing the recorded cause, the local
operator command `resume` clears pause while retaining the prior enabled flag
and authority. It cannot enable a bootstrap or bypass the three native proof
requirements. Failed source records remain held; resume does not requeue them.
An unknown first bootstrap-pointer outcome may resume only from the matching
frozen SSD marker. Use fresh hosted restore directories; never reuse a populated
restore target or delete the authoritative SSD history.
