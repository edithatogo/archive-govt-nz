# Testing profiles

The repository keeps the complete test suite as the promotion and CI gate.
For local feedback, use `./scripts/test-fast.sh`; it runs the registered
`slow`-excluded profile and preserves any additional pytest arguments.

Tests that require the `slow` marker must remain in the full suite and must not
be used to weaken coverage, mutation, schema, security, or publication gates.
The fast profile is deliberately dependency-free and deterministic: it only
selects by the registered marker and does not alter pytest configuration,
randomisation, workers, or coverage settings.

When comparing profiles, record the command, wall time, collected count, and
executed count. The full CI command remains authoritative for release claims.
