# Exclusive local classification occurrence packages

`export_budget_classification(package, manifest_sha256, original, output,
dry_run=True)` composes the existing pinned Budget package reader and reviewed
pure source-label projection. It verifies capped original bytes against the
source hash without parsing or executing the workbook. Existing packages and
originals remain unchanged; no acquisition or publication interface is called.

The output contains two canonical Parquet tables, complete source-lineage
accounting JSONL, the unchanged pure projection receipt and
`LOCAL_CLASSIFICATION.json`. It is explicitly a local descriptor, not a
publication manifest or a self-contained archival package. The original and
input package remain separately retained and hash referenced. No spending-fact
classification IDs, authoritative crosswalk or valid-time interval is invented.
Rights remain not evaluated and publication approval is not granted.

## Verification and failure boundary

Both modes require an existing non-symlink output parent. Only literal boolean
`False` enables writing. Default dry run serializes and caps every planned file,
including the complete local marker, without creating directories or files.
Its returned hashes are explicitly planned, not persisted. Parquet bytes are
checked against the exact original canonical table, including schema metadata,
before output creation. Per-file cap is 64 MiB, aggregate cap 128 MiB and
original-source cap 64 MiB. These are bounded buffer contracts, not a hostile
Parquet/process or filesystem sandbox; ancestors must be trusted.

Output creation is exclusive and never creates parent chains. Payload hashes
and exact file closure are checked before writing the local marker; all files
are checked again afterwards. Only successful final readback returns persisted
verification. A partial or full marker may remain after a failed final readback:
its existence alone is never proof of success. All partial bytes are preserved,
with a bounded best-effort `FAILURE.json`; no evidence is deleted. A directory
creation race never writes a failure record into another run's directory.

Known input/reservation/write failures use stable public codes rather than
exception messages or caller paths. KeyboardInterrupt and SystemExit propagate
after best-effort failure recording. The unchanged pure projection receipt
still says it did not perform fixity verification; the exporter separately
records the package/original snapshots it verified.

The Budget reader's documented v1 limits remain: original timestamp spelling
and original XLSX header ordering are not reconstructed. Hashing the original
does not independently re-prove those semantic relationships or grant rights.

## Current assurance

54 focused tests pass with 100% critical line and branch coverage (93 statements,
16 branches). Ruff and basedpyright pass. Source SHA256:
`c6c8108e98b1d9872215d082c4898ac88b54407988ffde259d3fc05af918a254`.
Test SHA256: `2ac17ea2601a73e83d895be163130202f19c698699f014dd406071f81916ee88`.
Independent read-only re-review found no actionable issue within the stated
scope. Subsequent test-only strengthening independently checks metadata,
nullability, row-count and value corruption; production is unchanged.
Critical mutation and native validation are pending.

Initial absent-module tests failed before implementation. A subsequent red test
identified a failure-marker error masking the primary write failure. Review then
identified missing-parent creation, marker-before-readback, unchecked serializer
schema damage and output-error disclosure; four explicit red tests reproduced
those gaps before fixes. Three further red cases covered TypeError disclosure,
TypeError masking and pre-decode byte caps. All now pass. One critical-coverage
invocation used a mistaken slash-containing module name and collected no coverage;
the corrected unchanged-source invocation passed 100%.

No retained-input pilot or permanent package is claimed yet. Synthetic tests
already prove two-build byte determinism, input immutability, exact canonical
Parquet round trips, accounting closure, original/payload tamper rejection,
byte-cap boundaries, parent/symlink/overlap restrictions, exclusive-creation
races, partial writes, readback corruption, interrupted runs and redacted errors.
