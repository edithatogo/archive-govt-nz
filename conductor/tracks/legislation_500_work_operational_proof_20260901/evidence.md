# Evidence

The target observation is bound to target `main`
`2c15dcc35a70bf364c443d02a02c6ad281c86d4b`, donor archived head
`b40587f1b1aec7356a0f623916fcc8212397d283`, and reviewed seed SHA-256
`59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.

The bounded preflight is retained in
`evidence/migrations/corpus-legislation-nz/500-work-operational-proof/500-work-target-revalidation.json`.
It records a blocked, not-dispatched observation: Prompt 06 exact-inventory
custody, Prompt 10 durable recovery, an exact 500-work workflow, and a
compatible committed parent remain absent. No acquisition, publication,
credential read, continuation, or durable-recovery claim was made.

The adjacent `operational-observation.md` report explains why the discovery workflow's
50-work cap cannot be relabelled as exact-inventory execution. This evidence
closes only the preparation slice; issue #335 remains open until its factual
execution gates are met.

Local validation passed 4,393 tests at 97.48% repository coverage, 45 schemas,
35 representative documents, 9/9 parity checks, all repository mutation lanes,
dependency audit, licence inventory, the corrected secret scan, and the
111-component SBOM. The initial Conductor-state and secret-keyword failures are
retained in the run log rather than rewritten as success.

## Superseding repository preflight — 2026-09-03

The append-only
`evidence/migrations/corpus-legislation-nz/500-work-operational-proof/preflight-refresh-20260903.json`
and paired Markdown report bind the current observation to target
`e559d675c347615d64ae5e1c1f3ad5efd5d120f6`. They record Prompt 06 and
parent-v3 compatibility as passed in repository scope and verify the active
exact lane with 107 focused tests and clean actionlint.

Prompt 10 recovery, a committed compatible parent, live no-write checks, and
explicit dispatch remain blocked. No credential value, endpoint, state, or
workflow run was used.

The full repository harness passed 4,559 tests at 97.50% combined coverage,
48 schemas and 38 representative documents, 9/9 parity, all registered
mutations, dependency and licence checks, the credential scan, and the
111-component SBOM.
# Repository correction — 2026-09-03

PR #365 correction aligns the exact-inventory workflow's parent-state restore
and seal with the same GitHub Actions run identity recorded by the harvest
receipt. This removes the deterministic pre-seal mismatch without asserting
that the hosted lane has run. Batch IDs remain non-authoritative correlation
fields.
