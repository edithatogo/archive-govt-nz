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
Cold mutation killed all 44 generated mutants in 38.08 seconds, with no
survivors, errors, timeouts, pardons or cache hits and no coverage filter.
Report SHA256: `68eea3a254d2b59b42276fec8d8353881c7a3b7a4846f18c50b3db4d75a74fd3`.
Main `9032f8f` (merged projection PR306) integrated at `32d6810` before native
validation. The whole incoming ledger matches byte-for-byte; existing projection
events were not duplicated. Source and tests remain unchanged. Native validation
passed at `f46e4b6`: 3426 tests, 8 existing resource warnings, 75.61 seconds,
97.20% coverage; all 42 schemas/32 samples, 9/9 parity, standard mutations,
benchmark and supply-chain gates passed, including the 111-component SBOM.
Log SHA256: `1652beba5db48150a1a90d5778a7af76e7e18b0d1a9925c1f5a225c12dcb3a8e`.
Two owned timestamp-only fixture diffs were restored after exit.

Initial absent-module tests failed before implementation. A subsequent red test
identified a failure-marker error masking the primary write failure. Review then
identified missing-parent creation, marker-before-readback, unchecked serializer
schema damage and output-error disclosure; four explicit red tests reproduced
those gaps before fixes. Three further red cases covered TypeError disclosure,
TypeError masking and pre-decode byte caps. All now pass. One critical-coverage
invocation used a mistaken slash-containing module name and collected no coverage;
the corrected unchanged-source invocation passed 100%.

Synthetic tests prove two-build byte determinism, input immutability, exact canonical
Parquet round trips, accounting closure, original/payload tamper rejection,
byte-cap boundaries, parent/symlink/overlap restrictions, exclusive-creation
races, partial writes, readback corruption, interrupted runs and redacted errors.

## Retained-input pilots

After full assurance, two exclusive temporary builds of each already retained
Budget package passed independent reconciliation. Each corresponding file is
byte-identical; source workbooks and all four input-package files remained
hash-identical. Independent checks cover literal labels/coordinates, null
identifier/version/intervals, canonical Parquet metadata and row counts, file
hashes and complete mapped/retained-only lineage accounting.

| Vintage | Files/build | Bytes/build | Dimensions | Mapped | Retained-only |
| --- | ---: | ---: | ---: | ---: | ---: |
| Budget-2025 | 5 | 1261253 | 215 | 215 | 3440 |
| Budget-2026 | 5 | 1089391 | 185 | 185 | 2960 |

Local marker hashes are respectively
`7e4d65d5bedfec72fe83d0882529d395a6401e816545286ab3fa9c8cfca8fcb3` and
`1a5aae6c79d79901c6bcaca9396fa6efa69e3572c9f382bbc011a427c5179c8d`.
The independent pilot script SHA256 is
`4c1e19be4115c953a1dce7a4f6be3e42173ee315c1a4dcec2a4ad1ecfbecb5d4`.
No published candidate was built or modified. Permanent retention and exact-head
hosted delivery are separate observations.

The preliminary local-assurance event had a manually rounded timestamp later
than its containing commit. A correction observation records the commit-time
upper bound without rewriting that event or changing any validation result.

### Exclusive local Silver retention

Following explicit retention approval, the verified builds were retained under
`silver/canonical-budget-classification-2025-20260831-v1` and
`silver/canonical-budget-classification-2026-20260831-v1`. Both destinations
were checked absent before exclusive creation. Each complete five-file closure
is byte-identical to both independently validated temporary builds, with the
marker hashes and byte totals above unchanged. All original workbook bytes and
all input package bytes were verified unchanged after retention. The four
temporary builds remain preserved. These local packages confer neither rights
eligibility nor candidate/publication approval; marker presence alone is not
verification.

Independent parent-agent readback also passed both retained packages: marker
pins, exact five-file closure, four payload sizes and hashes, both exact canonical
Arrow schemas including metadata, 215/185 rows and 3655/3145 accounting records.
It independently verified original CAS lengths and hashes plus input manifest
and all three payload pins, without writes. Its readback script SHA256 is
`40bf5bbf47863049e9e6072a3bb04c3ab568b731bbf5ba4480dc2be7b1b98634`.
