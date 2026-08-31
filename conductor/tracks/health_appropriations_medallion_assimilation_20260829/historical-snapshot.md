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

## Native assurance — 2026-08-31

The required `COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh`
passed at `b649de6` with exit 0: 2,918 tests, eight warnings, 68.44 seconds,
97.10% coverage; 74 Conductor tracks, format/lint/strict typing, 41 schemas/31
samples, 9/9 parity, all repository mutation/security/supply-chain gates and
111-component validated SBOM. CAS throughput was 512.18 MB/s. Log SHA-256:
`703d69135ac8fb84a2759303f36306fc1e26b738bf6b6636ac01d018789c4328`.
Two owned timestamp-only fixture diffs were restored after the process ended.
Hosted assurance remains pending; originals, derivatives and publication are
unchanged. This successful harness does not add a semantic or rights claim.

After integrating main `3be3048` at `f286de5`, 118 focused reader/JSON/Conductor
tests passed in 6.20 seconds and all 74 Conductor tracks validate. Incoming
machine evidence remains the exact prefix followed by two reader events.
Reader source and test hashes are unchanged; this focused post-integration
check is not a second full native run.
