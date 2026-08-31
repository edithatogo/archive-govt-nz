# Historical package transport verification

`historical_snapshot.read_historical_snapshot(root, source, pin)` verifies
the explicit historical manifest, all three Parquet outputs and the matching
original workbook into bounded in-memory snapshots. It never executes or
parses the workbook, downloads a source, writes output or grants rights.

The manifest must use the reviewed historical v1 transformation, passed
status, zero rejected count and `not_evaluated` rights. Duplicate keys,
nonfinite JSON, missing/extra files, direct symlinks, wrong hashes, count or
exact physical schema drift fail closed. All byte hashes are checked before
any Parquet decoding. Limits cover manifest, original/file and aggregate bytes,
rows, aggregate declared expanded size and Parquet metadata containers/strings.
The two historical list fields explicitly expect Parquet's `element` child
name; no schema metadata or type check is disabled.

The caller chooses trusted parent directories. Direct root/source/child
symlinks are rejected, but this API is not a filesystem sandbox. Evidence
attests returned snapshots, not later disk state. It does not establish cell
values, source capture, rights eligibility, cross-record lineage, semantic
projection or complete workbook coverage. The pure canonical projection must
perform its own semantic checks. Full input metadata stays in the returned
local manifest; operational wrappers must redact it before display.

## Verification

49 focused tests pass with 100% critical coverage (76 statements, ten branches).
All 57 cold unfiltered source mutants are killed with no survivors, pardons,
timeouts, errors or cache hits. An independent read-only review found no
actionable issue within the stated scope; its suggested exact-cap and
all-hashes-before-decode tests were included. Interrupts propagate. Errors are
stable and do not echo source metadata. Native and hosted assurance are separate.

The local-only smoke read verified both retained original objects and packages:

| Package | Facts | Lineage | Dispositions | Verified bytes including original |
| --- | ---: | ---: | ---: | ---: |
| `raw-historical-20260830-v1` | 106 | 1,143 | 1,503 | 449,487 |
| `raw-historical-2025-20260831-v1` | 108 | 1,164 | 1,531 | 337,077 |

Manifest pins are respectively
`2f39ad4dbeb7cb872118ddc634985b5e21b18f2ef2421ca3c0a1e9bf90411288`
and `aee4578f1ee83f8c1ede63e36e840c6cd2140df8c6f463e71ec93da9e4e7d75a`.
Original sizes are 232,417 and 116,265 bytes. No original, package, candidate or
publication was changed. This is transport evidence, not historical rights
clearance or a replacement for source-semantic reconciliation.
