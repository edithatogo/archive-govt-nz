# Local normalization scheduler interface

The local plan runner accepts an explicit SHA-256-pinned JSON plan with schema
`archive-govt-nz.health-normalization-schedule/v1` and up to 32 jobs. Each job
has `id`, `source`, `profile`, `sha256`, `vintage`, `locator` and `observed_at`.
Jobs are processed in ID order. The CLI
`health-appropriations-run-normalization-plan` defaults to dry-run and accepts
`--no-dry-run` for local execution; a scheduler can invoke this command against
its own pinned plan and durable local job root. The MCP operation
`health_appropriations_preflight_normalization_plan` is read-only.

Each job retains failed and interrupted attempts. A kernel-released exclusive
lock prevents concurrent work on the same root. Completed receipts bind the
source, manifest and output hashes; replay checks them and the exact inventory.
Job identity includes application Python/JSON file hashes, installed dependency
names and versions, Python build, system and architecture. Dependency file bytes
are not independently verified by that fingerprint. Local receipt pins do not
independently authenticate the prior computation or detect coordinated rewriting
of the receipt and outputs. A changed identity creates
a separate job rather than reusing the prior result. The runner limits plan size,
job count, source and output bytes, receipt bytes and attempt count. It does not
perform capture, publish results, assert rights or activate a scheduler.

Focused fixture-based execution, replay, interruption, failed-attempt retention,
lock exclusion, changed-runtime separation, plan validation and CLI/MCP parity
passed. On Python 3.15.1 the final scheduler and MCP protocol selection passed
30 tests with 82.09% combined branch coverage for the two new modules, against
the 80% floor. Ruff and scoped type checks passed. The full repository harness
passed on Python 3.15.1: 8,764 tests passed, 14 skipped, schemas 95/85 and
parity 9/9 passed, along with mutation, hygiene, benchmark and supply-chain
gates. Temporary files were placed on PortableSSD. Hosted assurance and protected
delivery remain pending; these results do not close Phase 8 or the track.

PR #812's initial hosted Codecov patch check failed despite passing all three
platform assurance jobs. Additional focused tests reject changed receipts,
unexpected outputs and invalid scheduler state. The two affected test files
passed 15 tests with 86.49% combined branch coverage of the new modules; the
unchanged implementation retains the earlier full-harness evidence. Fresh
exact-head hosted checks remain required.
