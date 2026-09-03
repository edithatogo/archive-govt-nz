# Budget canonical appropriation export

## Delivered boundary

`export_budget_appropriations(package, manifest_sha256, original, output,
*, dry_run=True)` creates or plans one exclusive local-only Silver derivative.
It composes the public verified Budget reader and pure appropriation projector;
it never reopens the workbook, changes an original, grants rights, approves a
mapping, or publishes a candidate.

A successful package contains exactly six files: three canonical Parquet
tables, the complete unchanged pure projection receipt, the complete lineage
accounting JSONL, and `LOCAL_BUDGET.json`. The outer marker binds the verified
raw-package manifest and payloads, original digest and byte count, vintage,
transformation, output hashes and lengths, and Parquet row/schema identities.
The pure receipt continues to state `input_fixity: not_performed`; its scope is
not silently broadened by the outer snapshot verification.

## Safety and boundedness

- Dry-run is a literal boolean and defaults to no writes while performing the
  same deterministic preparation and validation as persistence.
- The output must be absent and disjoint from retained inputs. Reservation is
  exclusive. Subsequent writes and reads are anchored to a no-follow directory
  descriptor, so replacement of the pathname cannot redirect output bytes.
- Parquet expanded tables have a conservative pre-serialization bound. Each
  serialized file is capped at 64 MiB, JSON is assembled incrementally, and a
  running 128 MiB aggregate budget is enforced as payloads are admitted.
- Payloads are read back before the marker; the marker is written last; exact
  six-file closure is then checked. Any partial bytes remain evidence. A
  redacted best-effort failure marker cannot replace the original exception.
- This protects reviewed local parent paths. It is not a hostile-filesystem
  transaction, a publication package, a rights finding, or a self-contained
  archive.

## Validation receipt

The missing-module red phase failed during collection before implementation.
After implementation and review corrections, 31 focused tests passed with 100%
line and branch coverage across 157 statements and 24 branches. Cold,
unfiltered mutation testing killed 63/63 mutants with zero survivors, timeouts,
errors, pardons or cache hits. Ruff and scoped Pyright passed.

The required native harness then exited zero on CPython 3.14.6: 4,624 tests
passed with nine existing warnings in 46.60 seconds; overall coverage was
97.54%; 48 schemas and 38 representative documents validated; differential
parity was 9/9; repository mutation, hygiene, audit, licence, secret and SBOM
gates passed; the SBOM contained 111 components. The retained log SHA-256 is
`6355ac9739a96c63c2278ada72f1ec26554de5889c5c6b5f9b74da1fa38804be`.

An independent review found output-root replacement, pre-allocation bounds,
acceptance-test coverage, and failure-marker exception-precedence gaps. All
four were corrected and revalidated. The final review also tightened the
anchored path contract so a replaced output pathname fails without redirecting
bytes. No retained package, original, candidate,
Hugging Face object, rights state, or publication state was changed.
