# Read-only native workbook inspection

Status: implementation in progress after delivered PR #715.

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
actual-source native replay, full assurance or hosted checks, which remain pending.
