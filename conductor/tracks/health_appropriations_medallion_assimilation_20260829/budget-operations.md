# Standalone Budget-package operational verification

## Contract and boundaries

`archive-govt-nz health-appropriations-verify-budget --package-dir PACKAGE
--manifest-sha256 SHA256` and MCP `health_appropriations_verify_budget` consume
the same previously reviewed `budget-expenditure/v1` package. Both require an
exact external manifest pin and return the same compact receipt (the CLI adds
its command name). The existing capped reader verifies the package snapshots;
this wrapper does not open the source workbook, fetch sources, write output,
create missing state, or return fact/lineage payloads.

Success reports the manifest and original-object digests, source locator,
vintage, observation timestamp, typed table counts and typed disposition
counts. Context strings are capped at 2,048 characters. These values describe
the reviewed package, not an independent original-source audit. Empty writer
packages are not supported by the reader's passed/nonempty scope. The receipt
always states `verification_scope=reviewed_package_only`,
`rights_state=not_evaluated`, and `publication_state=local_validation_only`.
Verification does not authorize redistribution or certify source semantics.

Failure returns only the fixed envelope and `invalid_budget_package`, never
exception messages, caller paths, rejected pins or source contents. The CLI
returns 2; the MCP wire response sets `isError=true` and preserves its structured
receipt. Invalid MCP request shape is separately rejected by protocol validation.
Interrupts are not swallowed. The shared schema rejects extra properties,
boolean counts, rights promotion and failed receipts containing source fields.

## Medallion alignment

Bronze originals remain immutable and external to Git. This is a read-only
Silver package-consumer surface, not a new normalization, Gold calculation or
Platinum publication path. Its manifest pin can support future scheduled
monitoring/recovery acceptance without treating a four-profile raw rebuild as
a universal source registry. Multi-vintage aggregation, wider adapters and
rights-qualified exact-candidate publication remain separate work.

## Validation and recovery record

Initial red contracts failed on the absent command/helper. Six initial tests
then passed. A separate negative MCP-wire test exposed `isError=false` on a
failed receipt; the server now marks failures only for this new tool. Expanded
contracts cover package tampering, missing roots/manifest, wrong/malformed pins,
source/derived-byte immutability, no-state creation, context limits, redacted
unexpected exceptions, schema parity and the real initialize/tools-call flow.

Before external worktree removals, 52 focused operation/protocol tests passed
at 100% helper line/branch coverage. Two test-style issues remained at that
point. Checkpoint `59a265d` preserved all implementation files before recovery
into an independent no-hardlinks clone; no worktree or original was removed by
this task. Subsequent validation is recorded below without conflating focused
success with the complete repository or hosted gates.

The independent clone rerun passed 52 tests in 65.88 seconds at 100% line/branch
coverage for `budget_operations.py`. Ruff formatting/lint and basedpyright
passed. Schema validation passed 41 schemas and 31 representative documents;
Conductor validation found no errors across 70 tracks.

Read-only live verification of the retained Budget-2026 package, pinned to
manifest `f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738`,
passed: 185 facts, 3,145 lineage rows and 6,451 dispositions (185 normalized,
6,266 out-of-scope, zero blank/rejected). Its original-object digest is
`3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0`.
This is a package receipt, not a fresh original-workbook acquisition or audit.

The native full gate and hosted delivery remain pending at this checkpoint.

## Population blocker retained explicitly

A prior bounded browser attempt returned `No browser is available`; the
documented diagnostic listed zero available browsers. No navigation, profile
access, download or source mutation followed. The exact official national
all-ages/all-sexes ERP saved query/series remains unresolved, not proven
unavailable. The captured HLFS working-age population remains preserved context
and is not selected for unqualified national per-capita calculations. An
available supported browser or official verified query metadata is the next
technical unblocker; no population series identifier is invented here.
