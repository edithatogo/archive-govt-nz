# Source-derived compatibility projection

Status: persistent export validated locally; exact-head hosted delivery remains
separate. This is not a replacement for the donor-derived publication.

`raw_compatibility.project_record` maps canonical records to the five legacy
table shapes. It requires known profile/measure/unit combinations, exact integer
years, source identities and finite Decimal amounts. INTEGER columns reject
fractional and out-of-range values; REAL conversion flags every exact binary
representation difference. Original decimals are retained as strings alongside
the full source context. The pure projection never reads or writes files and
does not substitute for verification of the containing run or field lineage.

The existing verified raw run projects to:

| Table family | Rows | Binary representation differences |
| --- | ---: | ---: |
| Recent appropriations | 215 | 0 |
| BEFU Health | 10 | 0 |
| HYEFU Health | 10 | 0 |
| Historical Health | 53 | 15 |
| Historical GDP | 53 | 0 |

There are 341 raw facts, compared with 312 donor-derived records. The existing
historical reconciliation explains 29 restored annotated-year observations and
one exact source/donor decimal difference. The 15 binary representation flags
are a separate storage property, not 15 source disagreements or corruptions.

## Persistent export and verified live result

`health-appropriations-export-sqlite` verifies the enclosing raw run and original
CAS, validates pinned Parquet snapshots, and checks unique IDs, source context
and exactly one matching amount-lineage row per fact. Dry-run is the default;
`--no-dry-run` creates a new exclusive directory, never overwriting existing or
partial outputs. Failures retain partial bytes and an error-class-only receipt.

The retained output is `gold/raw-compatibility-20260831-v1` under the external
health-appropriations archive. Its four files match an independent build byte
for byte. Manifest SHA-256:
`fb405a2fdbb2809093cb03d62ddbe1fcb1a1f6f91d304666e8ef0964813f73fb`.

| Output | SHA-256 |
| --- | --- |
| compatibility.sqlite | `89d0c13fc385676eb9b6ba394d817ba8febc289eec7fd6bc97b4199253e4449c` |
| records.jsonl | `3feb8a836cc98aac61acb0e5ebe31595ff9ece75f8e59d1ee46a99b1175019f1` |
| field_lineage.jsonl | `67acefc1dbc70e5dd5885ad63b5bf1b01a52bb5869771d40aeeecf4d0a74f8d1` |

The export contains 341 facts and all 4,918 field-lineage records. Schema and
multiset comparison retains all 312 donor SQLite rows with zero omissions;
only historical Health adds 29 observations. Row ordering is deterministic by
table and record ID, with explicit SQLite row numbers in the record sidecar;
donor insertion order is not claimed. SQLite's REAL conversion can obscure the
one source/donor exact-token difference, so the prior historical reconciliation
and exact decimal sidecars remain necessary evidence.

The source raw-run manifest remains
`da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
The donor database hash was verified before and after read-only comparison.
No original or HF publication bytes were changed.

Example (substitute the retained archive root):

```sh
uv run --locked archive-govt-nz health-appropriations-export-sqlite \
  --raw-run ARCHIVE_ROOT/silver/raw-orchestrated-20260830-v1 \
  --store-root ARCHIVE_ROOT/bronze-cas \
  --manifest-sha256 da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269 \
  --output-dir NEW_OUTPUT_DIRECTORY
```

Add `--no-dry-run` only to create a new local export. Compressed Parquet is
limited to 64 MiB per file, with 100,000 rows and 256 MiB declared uncompressed
row-group bytes. These are resource bounds, not parser-process isolation.

## Integration contract

- Verify the raw run against its exact manifest and original CAS, then parse
  capped, hash-verified snapshots of each stage's facts and lineage.
- Require unique record identities and matching amount lineage; retain every
  source fact and exact decimal in sidecars. Do not silently deduplicate.
- Reserve a new exclusive output directory outside both Bronze and the input
  run. Never reuse the old export helper's unlink/overwrite behavior.
- Write the five fixed-schema SQLite tables, check integrity, and produce a
  versioned manifest pinning the raw input, policy, output hashes and counts.
- Preserve failures without a completion claim. Test interruption, existing
  output rejection, tampering and independent deterministic rebuilds.
- Compare with the unchanged donor oracle using explicit repair dispositions.
  Do not describe the 341-row product as exact 312-row donor parity.
- Continue source-derived analytics with period/basis and denominator guards.
  New candidate publication needs its own exact-manifest approval.
