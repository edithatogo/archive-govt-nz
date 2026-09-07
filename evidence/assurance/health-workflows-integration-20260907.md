# Workflow integration review and validation

The first full gate at `d30a5d32` passed lock, Conductor, format, lint and types,
then exited 1: 6,271 tests passed but `test_foi_phase_validation.py` had one
collection error. Its new direct `tools` import was unavailable under the
repository pytest invocation. The correction reuses that test file's existing
explicit file-location `TOOL` loader rather than changing global import paths.
Coverage was 97.72%; no later gates ran in this failed attempt.

Independent eight-stage review reproduced both retained builds and all 34
files, but found three P2 gaps: a missing independently pinned Crown observation
receipt, inconsistent nested source-record identity being accepted, and
excluded formula areas accepting admitted record IDs. Those findings must be
fixed and re-reviewed before delivery; passing tests alone do not close them.

The catalogue-disposition validator, 108 chart literals and their distinct
semantics, and literal packaging have independent focused review evidence.
The original four-stage registry/resume/Gold paths remain unchanged. Neither
the historical PDF identity observation nor raw/context chart admission is
represented as canonical numerical extraction or whole-track completion.

## Corrected combined gate and independent review

The full locked gate passed at `1521071388394ad14bec9e5967e3e46e659a8ee4`:
6,396 tests, 98.03% statement/branch coverage, 48 schemas and 38 representative
documents, 9/9 differential cases, all configured mutation/hygiene gates,
CAS throughput 673.19 MB/s, dependency audit, licence inventory, secret scan
and validated 112-component SBOM. The process exited 0. Fifteen test warnings
remain disclosed in the run output; they did not become ignored failures.

The three eight-stage P2 findings were fixed in `aa6c47f7` and `ac85131b`.
Independent review passed 151 focused tests in the repository's importlib mode
and verified both retained 34-file builds. The Crown join is explicitly to a
pinned census observation, not a fabricated HTTP capture-time attestation.
Nested record contradictions and excluded-area identity claims now fail closed.
The residual six-chart slice also cleared independent 33-test/source replay.

Child-manifest review found a separate P2 exact-identifier gap: schema `$`
anchors accepted trailing newlines. Fix `15210713` uses strict full matches
without whitespace repair. Independent review passed 77 focused tests and
42 malformed-reference cases, then repeated all 42 through the publisher:
no added upload, commit or promotion, with existing catalogue state unchanged.
These mocked checks verify metadata handling, not remote raw objects or rights.

The first failed gate above remains part of the evidence. This completed local
gate does not substitute for exact-head hosted checks or protected merge.

## Late hosted verification-boundary finding

Hosted review identified malformed non-object PLAN JSON escaping the public
eight-stage verifier as TypeError rather than a structured CLI failure. Merge
was paused despite the earlier green checks. Fix `7910b0ab` adds the same
ordinary-exception redaction boundary as the legacy verifier; process interrupts
remain uncaught. Independent review passed 37 focused tests, actual malformed
CLI cases returned exit 2 with empty stderr, and both positive retained runs
returned exit 0 with all 34 file hashes per run unchanged.

The full locked gate at `7910b0abf21c33a059245ec181650efd00924f01` exited 0:
6,412 tests passed, 98.03% coverage, all schema/parity/mutation/hygiene checks,
CAS 686.37 MB/s, dependency audit, licence inventory, secret scan and validated
112-component SBOM. This supersedes the prior local result for final delivery;
the earlier result remains historically valid at its stated head. Exact-head
hosted checks must run again after this fix; no earlier green run approves it.
