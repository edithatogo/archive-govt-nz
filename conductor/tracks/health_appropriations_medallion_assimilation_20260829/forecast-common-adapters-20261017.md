# Reviewed forecast summaries through common dispatch

Two explicit registrations cover the reviewed `befu-2026/v1` and
`hyefu-2025/v1` literal Health-summary layouts. They reuse the existing
bounded workbook inventory, exact sheet/label/unit/year/type guards and literal
extractor through a shared in-memory snapshot parser. Legacy `befu`/`hyefu`
aliases are not registered as generic matches.

Common records preserve the complete existing Silver field shape, including
nullable fields normally supplied by Arrow. Field lineage retains all source
coordinates/raw tokens/rules. Every non-normalized cell disposition, including
context cells needed when an amount is rejected, and every adapter-scoped
excluded sheet remains represented. Actual/Forecast, source vintage, unit and
financial-year-basis gaps stay distinct. A selected adapter is not a passing
operation; rejected formula/error/invalid amounts remain explicit. No formula
evaluation, cached-total admission, currency qualification or Gold join occurs.

The filesystem normalizer retains its existing default-write and dry-run
contracts and all four native API profiles. Current source operations continue
using the native path for these profiles; common operational manifest adoption
is a separate task. Originals and existing packages are never rewritten.

## Native verification

[Exact native/common proof](./forecast-common-adapters-20261017.json) binds the
implementation atcb48363b to the independently pinned four retained reference
packages. Both new native builds reproduce all16 files per repeat, including
manifests and Parquet, across40 facts. This covers both legacy APIs as well as
both successors. Original observation tokens are bound to the retained legacy
PLAN or source census; their Z/+00 spellings are preserved for identity.

The two common successors match20 native facts and120 lineage entries exactly.
All non-normalized source cells and excluded sheets match their native
dispositions; both registrations are present during selection. Repeat dispatch
is identical and the filesystem normalizer is forbidden during common
extraction. Native dry runs create no output. Source/reference hashes and
original stat remain unchanged. No new source acquisition or external mutation.

## Focused validation and limits

The observed red phase failed because the new adapter did not exist. The first
implementation exposed sparse-parser versus canonical-null field differences;
that contract is now preserved explicitly.106 adapter/legacy/successor/preflight
tests pass; the broader source-operation/registry/dispatch/forecast selection
passed659 tests/10 skips before the four new fast-first snapshot refusal cases.
Ruff and full strict typing pass. The80% coverage floor and existing timeouts
remain unchanged; no coverage-only tests or dependencies were added.

Conductor independently reviewed implementation and native proof without
finding a blocking issue. Full final-tree validation and PR/hosted delivery
remain pending. The[partial donor-area metadata mappings](./donor-area-partial-mappings-20261017.json)
are assertion-only traceability, not output verification or global coverage.
Issue #210 and broader M07/AC03, operational adoption and phase gates stay open.
