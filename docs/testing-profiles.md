# Testing profiles

Both PR and release profiles keep the complete test suite and existing coverage
policy. The default `./scripts/validate.sh` uses the 13-stage PR profile.
`./scripts/validate.sh --profile release` retains all 32 original stages; only
mutation campaigns and the CAS benchmark are additional to PR assurance. Linux
CI runs release assurance, while macOS/Windows run PR assurance.
For edit feedback, use `./scripts/test-focused.sh <path-or-node>` with the
affected test file or exact pytest node. The script verifies the worktree's
Python 3.15.1 interpreter and leaves pytest's cache enabled. After a failure,
`./scripts/test-focused.sh --failed` reruns only cached failures; an empty
failure cache selects no tests and is not evidence that tests passed.

Use `./scripts/test-fast.sh` when a broader local profile is useful; it runs the
registered `slow`-excluded profile and preserves any additional pytest
arguments. Keep the full `./scripts/validate.sh` gate for coherent milestones
and PR delivery, rather than repeating it during focused edit cycles.

The full harness runs each named stage once. If one stage fails and the source
tree and that stage's inputs have not changed, rerun the failed gate directly
with `./scripts/validate-stage.sh <stage>`; pass multiple stage names to rerun
only those gates. For example, after a secrets receipt write failure, rerun
`./scripts/validate-stage.sh secrets` after storage recovers instead of
repeating pytest, coverage, mutation and schema checks. After changing code or
configuration, rerun the failed stage and the other gates affected by that
change. Do not treat a focused profile as full release evidence.

Tests that require the `slow` marker must remain in the full suite and must not
be used to weaken coverage, mutation, schema, security, or publication gates.
The fast profile is deliberately dependency-free and deterministic: it only
selects by the registered marker and does not alter pytest configuration,
randomisation, workers, or coverage settings.

When comparing profiles, record the command, wall time, collected count, and
executed count. The release profile remains authoritative for release claims.

`uv run --locked python tools/check.py --list --profile release` lists every
stage. Named `--stage` selection can run release-only stages directly, regardless
of the default profile. Shell and PowerShell validation wrappers forward profile
arguments. No new dependency or test-selection plugin is required.
