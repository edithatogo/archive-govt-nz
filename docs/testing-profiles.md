# Testing profiles

The repository keeps the complete test suite as the promotion and CI gate.
For edit feedback, use `./scripts/test-focused.sh <path-or-node>` with the
affected test file or exact pytest node. The script verifies the worktree's
Python 3.15.1 interpreter and leaves pytest's cache enabled. After a failure,
`./scripts/test-focused.sh --failed` reruns only cached failures; an empty
failure cache selects no tests and is not evidence that tests passed.

Use `./scripts/test-fast.sh` when a broader local profile is useful; it runs the
registered `slow`-excluded profile and preserves any additional pytest
arguments. Keep the full `./scripts/validate.sh` gate for coherent milestones
and PR delivery, rather than repeating it during focused edit cycles.

Tests that require the `slow` marker must remain in the full suite and must not
be used to weaken coverage, mutation, schema, security, or publication gates.
The fast profile is deliberately dependency-free and deterministic: it only
selects by the registered marker and does not alter pytest configuration,
randomisation, workers, or coverage settings.

When comparing profiles, record the command, wall time, collected count, and
executed count. The full CI command remains authoritative for release claims.
