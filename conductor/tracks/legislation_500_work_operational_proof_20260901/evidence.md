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


## Superseding durable-parent preflight — 2026-09-03

Prompt 15 merged at `d60ed58420d1fe39dc420bbe047b9bf901b0d66d` and Prompt 10 merged at `5745bf3e38924dc968af70842dc6ed7a776e9e05`. `config/legislation/parents/current.json` pins the public Hugging Face package by immutable revision, 71,776,346-byte size, outer SHA-256, inner manifest/inventory roots, and the separately verified public-rights authority.

The append-only `parent-preflight-20260903.json` retains two failed attempts before the successful no-write restoration. The successful attempt anonymously retrieved the exact package, verified outer and inner fixity, restored 555 files, and reproduced the expected roots and 552-record parent scope. It did not read the NZ legislation credential, acquire sources, write canonical state, publish, or dispatch GitHub Actions. Its receipt SHA-256 is `ff5ff6dbc6520c9b81be0cc621ed21a50700a5933d035360663b930a7ecb6a1b`.

The remaining gate is the authorized hosted exact-inventory execution after this PR merges and its exact-head checks pass.

## Remediation merge readback — 2026-09-04

PR #379 merged the Work-level document-identity correction to `main` at
`cbad1dd9fb5a89197cf37bd53a673b021685812e`. Its exact head passed the required
Ubuntu, macOS, Windows, CodeQL, workflow-lint, and Codecov checks. After merging
that `main` revision into PR #373, 90 focused tests and the complete repository
harness passed locally, including 4,593 tests at 97.52% coverage and the new
two-mutant legislation reconciliation lane.

This closes the repository remediation task only. The target-owned 500-work
execution and durable continuation/recovery tasks remain pending until an
explicit hosted retry is authorized and independently verified.

## Superseding operational evidence — 2026-09-05

The dated `evidence/migrations/corpus-legislation-nz/500-work-operational-proof/closeout-20260905/500-work-target-revalidation.json` and `operational-observation.md` bind the successful run 33800180992 and independent complete artifact verification. Original blocked records remain unchanged. Required no-write credential/endpoint preflight remains a precise blocker: the existing preflight_only lane validates state only. Issue #335 is reopened; no publication, workflow dispatch or state mutation is performed by this evidence correction.
