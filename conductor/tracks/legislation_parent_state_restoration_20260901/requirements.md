# Requirements

## Must

- Pin and independently verify complete parent metadata, bytes, roots, source identity and receipts before promotion.
- Reject missing, partial, expired, wrong-origin, corrupt, unsafe and orphaned state.
- Require separate recorded authority for initial bootstrap or legacy adoption.
- Preserve parent evidence and link every continuation to exactly one verified parent (or explicit bootstrap).
- Share one fail-closed interface across legislation workflows; no latest-run or empty fallback.
- Prove integrity controls with negative, property, integration and mutation tests; meet native gates and 100% critical coverage.

## Should

- Provide bounded, sanitized failure receipts and downstream interface documentation.

## Will not

- Acquire sources, merge canonical donor/target state, choose durable storage, publish, change discovery semantics or execute recovery drills.
