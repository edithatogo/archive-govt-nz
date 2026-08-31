# Plan

- [x] Verify both parents and pin latest successful target (828a751).
- [x] Implement no-overwrite merger and comprehensive integrity tests (828a751).
- [x] Execute initial local merge, reversed order and idempotence readback (828a751).
- [x] Run full quality gates and exact-head hosted checks (1f0417f; seven green checks).
- [x] Review scoped PR, record handoffs and prepare the exact-head guarded merge (#297).

The final documentation head must pass the live seven-check guard before delivery.
GitHub PR #297 and issue #292 are the authoritative post-commit merge readbacks.

## Review fixes

- [x] Reject conflicting descriptors for the same artifact; retain red-test evidence and regenerate the package with the fixed software revision (c4287a4).
