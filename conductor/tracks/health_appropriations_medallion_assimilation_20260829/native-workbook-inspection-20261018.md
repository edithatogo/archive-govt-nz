# Read-only native workbook inspection

Status: native replay and original full harness qualified; hosted delivery pending.

Use the existing operation/CLI/MCP architecture and the qualified compound
source dispatch. The only source IDs are the two reviewed expense workbooks.
Caller inputs are CAS root, known source ID and explicit normalization observation
time. The source factory retains its reviewed locator/vintage/hash internally;
no source URL substitution, arbitrary source file or output directory is accepted.

Return compact closed JSON with physical selection, native result discriminator,
source/profile identity, native metadata/table schema IDs, exact row counts,
Parquet/native-manifest hashes, excluded-sheet descriptors and held-source reasons.
No native rows or caller paths are returned. Metadata admission and original
values/IDs remain owned by the existing source adapters/validator. Rights,
canonical promotion and publication remain unevaluated/unperformed.

One shared read-only operation powers the CLI and forced-read-only MCP tool.
Use the existing bounded regular snapshot reader and schema fingerprint helper.
Reject unknown sources, unsafe paths, changed bytes, invalid observation inputs
and incomplete siblings. JSON-RPC input failures use fixed redacted messages.
Meaningful focused checks cover helper/CLI/MCP parity, complete descriptors,
source identity/fixity, hold/refusal and no writes. Required actual-source replay,
original full harness and exact-head hosted delivery follow implementation.


## Implemented command and tool

`health-appropriations-inspect-native-workbook` accepts only `--cas-root`,
`--source-id` and `--observed-at`. The MCP tool is
`health_appropriations_inspect_native_workbook`, registered through the existing
domain-tool table. Its input/output schemas are closed; requesting writes is
invalid. JSON-RPC schema failures return a fixed message without caller values.
Inspected results return exit 0; held/failed results return exit 2 and MCP
isError. No raw rows, source locator strings or caller paths are returned.

The helper uses the qualified compound dispatcher, then projects complete
selection receipts, native metadata/table schema identities and fingerprints,
counts, original native Parquet hashes, complete native-manifest hashes and
excluded-sheet/physical-loss descriptors. Observation time is explicit caller
normalization context, not capture attestation. Unchanged native writers provide
independent fixture manifest/file-hash controls for both source families.

Fifteen focused operation cases pass, including actual CLI/JSON-RPC parity for
inspected/held/failed states under Python write/network denial and memory-only
Parquet destinations after dependency warmup. The broader protocol/CLI bootstrap
integration run passed 55 tests before the final extra argument split/network
assertions; the latest 15 operation cases cover those final test refinements.
Ruff/format and strict typing pass. These fixture-backed checks do not replace
actual-source native replay, full assurance or hosted checks; their evidence is recorded separately below.


## Actual-source replay and full assurance

The frozen implementation at `2aef585c35c89ec5c9aac1f7ace40558f80ef87c`
(tree `6649bf4b9bc49cd88744e1d8810d27103e2ff84b`) passed two actual-source
runs through the shared helper, actual CLI parser and initialized MCP JSON-RPC.
Both reports are byte-identical, with digest
`e482b6e0b573bf3b84f61cbcac69d5216c4a696b1123b5ea65fc6f3b577126a8`.
All 16 original native manifest/Parquet hashes match. The four overlapping profile
interpretations retain 180 facts, 1,784 lineage records, 4,833 dispositions and
four excluded-sheet descriptors. These counts are not unique worksheet coverage.
Each run reads only the two retained source objects, six times across the three
routes; source and reference bytes remain unchanged. After disclosed dependency
warmup, Python write APIs and network calls were denied and Parquet destinations
were restricted to memory. This is bounded Python instrumentation, not an OS
sandbox or a claim that every possible native-code side effect was denied.

The first full harness stopped at its test stage with 8,025 passes, 12 skips and
two timing failures: the existing Hypothesis 200 ms deadline and FIFO subprocess
10 s timeout. Both passed in bounded focused reproduction under the same limits.
An instrumented physical-path FIFO diagnostic proves readonly nonblocking open
and refusal before body reads; it does not conclusively explain the earlier
subprocess timing spike. Preserve that failure and its diagnosis separately.

On the same unchanged implementation, original full attempt 2 passed all 32
stages: 8,027 tests, 12 skips, 18 warnings, 295.98 seconds, both snapshots,
66 schemas/56 representative documents and all nine differential parity checks.
All original mutation, hygiene, CAS benchmark, dependency, licence, secrets and
SBOM gates passed. Runtime remained uv 0.13.1/Python 3.14.6, four workers and
original limits. Conductor verified exit 0, the clean exact head/tree, terminated
processes and kernel-slot release. The machine receipt binds the full log,
native proof and retained owner readback. Earlier failed evidence remains in
`assurance-1`; successful full evidence is retained in `assurance-2` under the
same evidence directory. Hosted exact-head assurance, review, merge and pruning
remain pending. No rights, canonical, global worksheet or publication gate is
closed by this operation.
