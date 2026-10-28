# Review Report: Parliament P7 Hub write cooldown

## Summary

The candidate preserves first failures and public durability while preventing
known Hub write-rate limits from causing repeated cleanup or claim writes.
Native delivery/recovery remain separate acceptance tasks.

## Verification Checks

- [x] **Plan Compliance**: source implements bounded exact native origin proofs,
  preclaim read-only deferral, no-cleanup-write behavior and publication hints.
- [x] **Style Compliance**: affected Ruff/format and strict types checked.
- [x] **New Tests**: early/expired/native-clock/malformed/transitive/cyclic and
  truncated proofs, all CLI operations, one-send publication and cleanup paths.
- [x] **Test Coverage**: new cooldown module measured91% in focused execution.
- [x] **Test Results**: initial207-test selection had205pass/two assertions to
  update for the new deferred semantics and case-sensitive fictional headers.
  Failure-cache rerun passed46cached nodes, including both corrected nodes.
  Full candidate assurance passed8695tests/14capability skips and all stages.
  Review then fixed unknown-deadline expiry and retained linked origin proof;
  affected209tests passed at91% new-module coverage. Hosted coherent-main
  assurance still gates delivery; no native early-deferral claim.

## Findings resolved

The prior cleanup path attempted pause/release after a Hub429. Checkpoints now
mark write-limited state and suppress subsequent writes. The CLI keeps the exact
first failed receipt nested under a deferred status instead of reporting capture
success or zero source work for a partially productive invocation.

One new CLI test initially omitted its fictional remote fixture, exposing native
read-only preflight. That execution was interrupted and retained; the fixture
and unchanged remote-head assertion are restored. No native mutation or source
request occurred. Exact native version/identity ownership remains separate from
fictional testing.

No rights, access-hold, public-target, immutable-original, README or acquisition
budget relaxation was found. Parent coverage/rights and natural recurrence remain
open. Required full local/hosted checks and post-deadline native recovery gate
activation; source review alone does not authorize claiming operational health.

A review correction removes an inferred24-hour expiry for missing Retry-After.
Unknown deadlines propagate their exact origin in sanitized failure artifacts,
and linked unavailable origin evidence also stays fail-closed. New native reads
never turn artifact age or retention loss into permission to write. This changes
only negative write eligibility, never payload/control authority or source rights.
