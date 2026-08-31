# Read-only local canonical provenance verifier: bounded design

Initial inputs are at most four explicitly supplied package specifications,
one per reviewed historical-2024/historical-2025/Budget-2025/Budget-2026 profile.
Each specification supplies canonical root + exact local marker SHA256, original
object path, raw package root + exact raw manifest SHA256, and explicit kind.
No directory discovery, public URLs, publication settings, original acquisition,
file writes or missing-state creation. Roots/parents are caller-trusted; direct
root/original/child symlinks fail. This is not a hostile-filesystem/process sandbox.

## Proposed API and verification order

`read_local_provenance(tuple[CanonicalPackageInput, ...])` returns a JSON-ready
inventory plus a separate wrapper verification receipt; no full source rows.

1. Validate typed input count, exact pins, distinct roots and reviewed kinds.
   Check each canonical root's exact five-file allowlist, including its named
   `LOCAL_CANONICAL.json` or `LOCAL_CLASSIFICATION.json`, never `MANIFEST.json`.
2. Read bounded snapshots: marker at most 2 MiB; individual canonical payload
   at most 64 MiB; canonical package at most 128 MiB. Reject symlinks, malformed
   strict JSON, duplicate keys, non-finite numbers, unexpected file closure,
   and invalid descriptor counts/types before decoding table bodies.
3. Compose existing public raw readers (`read_historical_snapshot` or
   `read_verified_budget` plus `verified_snapshot` for the original). These
   independently bind original and raw package hashes and maintain their
   documented timestamp/header/bounds limits. Do not change those modules.
4. Recompute public pure historical or Budget classification projection from
   verified raw snapshots. Independently compare each retained canonical table
   to the recomputed table with exact schema/metadata/row equality, and compare
   accounting/receipt JSON with typed canonical JSON equality (so booleans and
   float counts do not alias integers). Verify local marker metadata, all
   declared file sizes/hashes, input pins, source identity/vintage, explicit
   no-publication/no-rights-grant states and recordset closure.
5. Bound Parquet metadata before reading: capped row groups/rows, thrift string
   and container limits, and 256 MiB declared expanded bytes per package; capped
   snapshots are not a process sandbox. Returned facts remain internal only.
6. Build pure ProductDescriptors for the actual canonical recordsets with the
   local marker SHA as package pin. Source nodes remain original SHA identities;
   lineage depends on explicitly present canonical fact/dimension products.
   Invoke unchanged `build_local_provenance` for graph/identity validation.

The nested pure inventory keeps `input_fixity=not_performed` because that
function did no I/O. The wrapper separately states scoped returned-snapshot
fixity and recomputed-projection equality. It must not claim capture truth,
later disk stability, broader source-semantic truth, rights eligibility,
DCAT/Croissant/RO-Crate/PROV conformance or complete Platinum/recovery. Errors
are stable/redacted; interrupts propagate. No Budget appropriation projection
is included before its separate reviewed delivery.

## Assurance contract

Red-first fixtures: missing root, wrong marker/raw pin, tampered original or
payload, unexpected/missing files, symlinks, malformed/duplicate/NaN JSON,
boolean/float count drift, schema/metadata/value drift, accounting divergence,
cross-vintage input mismatch and resource caps. Positive synthetic packages
must be made through existing public exporters, not fabricated success markers.
Verify no writes/no missing-root creation, deterministic metadata, original/raw
immutability, and both canonical families. Independent review precedes heavy
mutation/native gates; native and exact-head hosted delivery remain separate.

## Prior delivered task reconciliation

Read-only fresh GitHub REST checks confirmed PR302/295/318/274 merged before
the four matching narrow plan entries were marked complete. Their exact merge
IDs are attached to those entries. Broad source-family, phase, Platinum,
recovery and publication tasks remain open. PR319 was merged by this agent
after seven fresh exact-head successes and clean status at
`daa8a60c38a15fadb03ffbe16edfea00fc57c2ed`; method-merge/readback confirmed
`371a8ea555718659fbf5fdde5b60f5f1457518f3` at `2026-08-31T17:17:39Z`,
preserving the queued resume planner's ancestry. No hosted rules were changed.

## Implementation evidence in progress

The initial seven red tests failed because the new module did not exist. The
implemented reader then passed 64 focused tests with 100% coverage of 168
statements and 26 branches; production typing and Ruff passed. Boundary-test
expansion initially produced 68 passes and one failure: setting the shared
marker/Thrift-string cap to the small marker's exact byte length also rejected
the larger legitimate Arrow schema string. The fixture now pads the marker
with JSON whitespace above the independent schema-string size, repins those
synthetic bytes, and tests the exact marker limit and limit-minus-one. No
production limit or gate was weakened. Full assurance remains pending.

The final pre-mutation checkpoint passed 69 focused tests (14.65 seconds), then
a separate critical run passed all 69 (9.12 seconds), with 100% coverage of 168
statements and 26 branches. Production typing and Ruff passed. Parent independent
review of source `94da44ef8bb210a0c22cdd817013259f83592fb4cf4a7ce6cb2b1f3a59e03861`
and tests `2a9ef729f313473e5b05ca5f3e2cb11c13a5bd7bc99d2a579df8444fde98265f`
found no actionable issue within the stated snapshot scope. Cold mutation and
native assurance are queued behind the separate executor/Budget lanes.

The [future metadata standards route](./metadata-standards-route.md) is a
proposal only, not an expansion of this reader's implementation or claims.

Pre-mutation self-review investigated a possible deep-JSON parser exception.
On the pinned Python 3.14.6 runtime, 10,000 nested arrays decode successfully
and the reader rejects the non-object marker with its stable public error.
All seven strict-JSON cases passed (20.44 seconds); no production fix was needed.
The extra malformed-input boundary is retained, bringing the test count to 70.

Final 70-test critical coverage passed in 15.50 seconds with the same 100%
statement/branch coverage. Fresh main `efca467` was integrated without conflicts
at `2796c3e`; source/test hashes stayed unchanged and 76 Conductor tracks passed.
Cold mutation then passed all 96/96 mutants, zero survivors and zero cache hits,
with all 70 tests in 176.70 seconds. The retained JSON report SHA256 is
`fab4bd25072085df6c9db155c85bbe38acfb807a8a054362f93afc5014c2f7d5`.
Native validation follows this integrated checkpoint; no source/package writes
were involved in the synthetic tests or mutation run.

The unchanged repository-native harness completed successfully at `f6bcf14`:
4,082 tests, eight existing SQLite resource warnings, 166.27 seconds, 97.32%
coverage; 42 schemas/32 representative documents; parity 9/9; all native mutation,
hygiene, benchmark, dependency audit, licence inventory, secrets and 111-component
SBOM gates passed. Log SHA256:
`a32af6b6e90c7f22f02eb2b5c9587dbdc389f7b88a256f5482429e7b78ba81ed`.
Source `94da44ef8bb210a0c22cdd817013259f83592fb4cf4a7ce6cb2b1f3a59e03861`
and final tests `5e1fbeb556d2e02d0c492241f2deb0917b1d6c0e1d57534d613eda5912c948c2`
were unchanged. Two unrelated test-generated timestamp-only fixture changes
were restored after the harness ended. Hosted delivery and the independent
retained-package replay are separate, pending receipts at this checkpoint.

## Independent retained-package replay

Parent independently ran the reviewed driver after native assurance, exit 0.
The driver SHA256 is
`2fce2025be7c8190e48c414c849b73525ba1caf85392b80da649535ef25a34f3`;
the log SHA256 is
`55daeee55f8181abd4be93d7116b2bc2b29609dcc76e250a1b49dff2ff62c3ad`.
Both are retained under `/tmp/health-provenance-replay.LrHl3n/` as `replay.py`
and `replay.log`; this agent independently read both before recording this receipt.

Each of two fresh exclusive attempts rebuilt the four reviewed historical
2024/2025 and Budget classification 2025/2026 canonical packages from retained raw
packages plus original objects: 21 files and 3,115,847 bytes per attempt, including
`LOCAL_PROVENANCE.json` SHA256
`a983717ca7f6b5c3e15267fcd231b31ee568d034230eb4fc924985aec73ce9cd`.
All 20 canonical files exactly matched retained bytes. Metadata matched the
retained-input projection and was input-order independent; both attempt trees
were byte-identical. Original objects, raw packages and retained canonical files
remained unchanged. This proves only four raw packages → canonical packages +
local inventory, not complete Bronze-to-Platinum, standards or publication.

## Delivery integration

After frozen native assurance, ordinary merge `3bd9577` integrated executor PR323
head `232ed919406813ba63cfd730ea24b4bfa237d710`, including Budget PR322.
The only conflict was the append-only evidence ledger: all 117 incoming lines
were retained byte-for-byte before this reader's own append, verified with `cmp`.
All 123 reader/pure-inventory focused tests passed in 21.07 seconds and 76
Conductor tracks validated. Source/test hashes were unchanged. This is focused
post-integration evidence, not a relabelled native rerun; exact-head hosted checks
remain required before delivery.

Final executor replay receipt head `f866da40cdca0b8109b97cd3fad769e620eb471f`
was integrated at `fe857ae`: all 118 incoming ledger lines were preserved as an
exact prefix before the reader append. The 123 focused tests passed again in
11.84 seconds and 76 Conductor tracks validated; reader source/tests remained
unchanged. An intervening ancestry-only merge of delivered main `874f5bb` had
no tree changes. Hosted checks must refer to the final published reader head.
