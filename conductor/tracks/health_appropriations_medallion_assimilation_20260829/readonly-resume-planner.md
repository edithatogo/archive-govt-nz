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
Cold unfiltered mutation passed: 95/95 killed, zero timeouts/errors/pardons,
zero cache hits, one worker, unchanged 30-second deadline; 102 tests in 170.21s.
Report SHA-256 `2acfb161d6ece7ab070805ba397ef3e73d5ec2f91e30665ac1e01ee5ea7a822f`.

The full native harness passed with exit 0 at
`ce9c8b8b538530afabd2f6c9710d52a6092ab56f`: 3,797 tests, eight existing warnings,
113.51s test time, 97.27863% overall coverage, 75 Conductor tracks, 42 schemas /
32 samples, 9/9 differential parity, all native mutation/hygiene/security gates,
and a validated 111-component SBOM. Runtime was CPython 3.14.6 / uv 0.11.8, with
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4` and an isolated
environment/cache. Only two generated timestamp-only legislation receipts were
restored after exit. No original or existing product bytes changed.

Native log SHA-256:
`809ae06436a4ead584c28e5a6bbf3af3b3ebc158e64ff1bca982f2dd8338f4f4`.
Native coverage SHA-256:
`a671ea4ef32622edf77798c2def4e3b5a9e79b4c9112204a6eb34124e0a80319`.
Receipts remain under `/tmp/health-resume-planner.k6fMec-*`, not source Git.

After native completion, ordinary merge `1139bca630fe56442fd2ebe817e155edb7f54324`
incorporated reviewed, not-yet-merged PR #319 head
`daa8a60c38a15fadb03ffbe16edfea00fc57c2ed`, including already delivered #318.
The complete incoming evidence-ledger prefix is preserved. Source/test hashes
above are unchanged; 155 focused planner/provenance tests passed in 14.68s,
typing and all 75 Conductor tracks passed. Delivery is queued after #319 with
fresh exact-head hosted checks; this is not a second full native run.
