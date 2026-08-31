# Bounded FOI queue foundation

`archive_govt_nz.foi_scheduler` provides pure, immutable state transitions. It does
not dispatch capture, publish bytes, or activate a schedule. No live source is
made eligible by these functions.

A `Job` is one historical or incremental batch with a stable, caller-defined ID
and hard ceilings for requests, bytes and seconds. Revisions and changed objects
must receive new batch IDs; old verified jobs remain preserved. Withdrawn,
restricted, unsupported and exhausted jobs remain visible but cannot dispatch.
`SourcePolicy.disposition` must be exactly `eligible` to reserve work. A caller
must derive this from the reviewed registry and retain the source-specific rights,
privacy, adapter and pacing evidence. A public directory listing is insufficient.

`reserve` returns a new `Queue` with at most one reservation. Sources with the
oldest service sequence go first, then readiness time and job ID provide stable
ordering. One leased batch occupies its origin until explicitly reconciled,
including after expiry. Request, byte and runtime ceilings include every active
reservation. These are **concurrent reservation budgets**, not a rolling daily or
whole-run quota. An executor must enforce each batch ceiling and its cumulative
run budget before dispatch and while streaming. A batch that never fits requires
explicit resharding; it must not be silently skipped or credited.

`retry` requires the exact job/lease identity and externally verified terminal
failure evidence. Age alone never releases a lease. Retry delays double with a
bounded exponent; the source attempt limit leads to an explicit exhausted state.
Lease tokens remain in the queue history and cannot be reused after a retry.
`credit` requires an unexpired exact lease, retained artifacts, an anonymous
restore verification, manifest digest and public revision. These arguments are
trusted evidence inputs from the verified publisher, not checks performed by the
scheduler. No counter or country-completion claim is inferred from queue length.

`record_capture` records a trusted executor's verified local package and cold
restore under an exact unexpired lease. Its terminal `captured` state retains
the manifest digest but clears the active job lease and has no publication
revision. Lease history remains intact. This releases concurrent resource
reservations without granting public coverage credit. It does not verify files
itself: the executor must preserve and verify originals before proposing this
transition. Subsequent publication requires separately admitted work and its
own eligibility and anonymous verification evidence.

Integration must load an authoritative shared ownership fence, validate the
current owner/epoch/lease with `foi_ownership.require_owner`, apply a transition,
and atomically compare-and-swap the durable state before any external operation.
A failed CAS means the candidate must not dispatch. Persist `dataclasses.asdict`
output with a versioned state store; validate and rebuild dataclasses on read.
Never replace the authoritative shared fence with a local cached file or assume
GitHub concurrency across two repositories supplies that fence. Publication needs
an atomic sink condition on its epoch/lease or a single executor serializing
transfers and writes. A fresh check alone leaves a time-of-check race.

Still required: the production registry-to-policy evidence resolver, authenticated
capture executor, cumulative quotas, production checkpoint/version migration,
durable shared owner deployment, dispatch/receipt reconciliation, monitoring,
source-specific pacing and anonymous raw restore evidence. This foundation does
not complete P5 or authorize donor/receiver cutover.

Persisted numeric counters and resource ceilings must be nonnegative integers;
JSON booleans, fractional values and numeric strings are rejected. Verification
gates require the boolean `true`, not merely a truthy value. Queue sequence and
lease history are validated on reconstruction, and malformed runnable lease
states are rejected before transition. Origin pacing folds hostname case and
explicit default ports; source policies must contain bare HTTP(S) origins.
These structural checks do not authenticate evidence supplied by the caller.

Pin the policy revision, including each origin, for the lifetime of active leases.
The pure scheduler derives active origins from its supplied policies; replacing
that map mid-lease would invalidate origin exclusion. A future shared dispatcher
must persist the policy revision with admitted work and reconcile changes before
using a new policy generation.
