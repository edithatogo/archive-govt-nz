# Read-only partial-rebuild planning

`rebuild_resume.plan_resume` is a library-only, non-writing inspection of a
caller-reviewed failed/incomplete attempt. It accepts explicit donor-manifest,
old `PLAN.json` and per-stage SHA-256 pins, a source CAS root and observation
time. It recomputes the exact four-profile plan from the pinned donor rows;
the previous plan cannot self-assert its own source identity. The four selected
original snapshots are capped and hash-verified before derivative inspection.
This is not verification of all 23 preserved donor objects.

For each of Budget 2025, BEFU 2025, HYEFU 2024 and fiscal historical 2024, a
missing/unpinned/incomplete/corrupt stage receives a bounded `reextract` reason.
Only a pinned, passed, exact four-file stage with matching source/time/vintage,
transformation and forecast profile, exact Parquet transport schemas, declared
row counts and zero rejected inputs receives `reuse_verified`. The term means
stage fixity and transport structure, not renewed source-semantic validation,
normalization approval, rights clearance or publication authority. Extra donor
metadata is not promoted into claims. Unknown roots, unsafe paths or conflicting
contexts fail closed rather than silently choosing another input.

Limits are 4 MiB per metadata snapshot, 64 MiB per original or Parquet snapshot,
100,000 rows per table and 256 MiB declared expanded bytes per stage. Parquet
Thrift limits are independently 4 MiB strings and 100,000 container entries.
Directory iteration stops at five stage entries or seven attempt-root entries,
one beyond the allowed closure. Trusted reviewed roots are required; these checks
are not a hostile-filesystem sandbox or a snapshot isolation guarantee.

No directory is created, original or partial file rewritten, exception receipt
copied, extraction executed, or publication candidate produced. Expected stage
diagnostics contain machine reasons only. Global input failures may still raise
low-level library exceptions; this is not a CLI exception-redaction boundary.
Any future executor must reverify pins and use a fresh, exclusive attempt,
preserving all old bytes. Complete v1 roots remain under `verify_rebuild` and
are deliberately rejected here. A future attempt envelope should keep resume
provenance outside its unchanged v1 `run/` closure.

## Development receipts

- Initial import failed before implementation; then three focused tests passed.
- Eleven red count-agreement/input-pin receipt tests failed before the checks
  were added. A malformed donor object exposed its existing store exception;
  explicit object-ID validation now precedes store lookup.
- Independent review found missing transformation/profile and rejected-count
  checks. All 22 new negative cases reproduced the defect before correction.
- Parent review found uncapped directory enumeration and Parquet metadata
  parsing; three adversarial tests reproduced both before correction.
- Initial critical coverage was 99.48% (finite extra JSON metadata untested);
  that boundary is now exercised. A later mistyped coverage module selector
  collected no data and failed; the corrected command reported 102 tests and
  100% coverage across 160 statements and 36 branches.
- A command tried an unavailable `ty` executable (exit 127); repository
  `basedpyright` subsequently passed with no errors or warnings. Two test-spy
  typing corrections did not alter production behavior.
- Parent and independent sibling re-review found no remaining actionable
  issue in the reviewed fixity/transport-only scope.

Frozen source SHA-256:
`f20b88a26ebb740c41116085146a931a7f5e370b29e5328426f8d2a01d3dd407`.
Frozen test SHA-256:
`7c7d5713baba0cd1f1f272b7c7f6eb74fce5b4e06db2571ee5e6d5a3961f642f`.
Cold mutation and native harness receipts remain pending.
