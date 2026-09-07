# Local real-state resources and hosted security readback

Reviewed software: `e015a059c88e605dd43b6127d1e7a9d81d37f574` (PR414).
This is a local read-only benchmark, not an Actions execution or final integrated
assurance claim. No Actions environment was fabricated. No full harness,
package reproducibility builds, acquisition, publication or remote mutation ran.
`uv run --locked` installed the locked environment and its normal editable project;
this is not wheel/sdist reproducibility evidence. Parent owns builds and hosted
supplementary artifact collection.

## Result

- Authenticated artifact 9970365066, run 33968609350, matches the reviewed parent
  reference's metadata, repository, successful workflow, run attempt and expiry.
  Download: 10,628,850 bytes; ZIP SHA-256
  `9f9b9bd856de05ba2a9481781564e0a49d368d1c6c2770b74b807a4845adc318`.
- Native bounded unpack and parent verification passed, including roots and
  continuation seal. Linked SHA-256/BLAKE3/size checks passed for 904 CAS objects.
- Reconciliation: 500 works, 852 scoped records, zero mismatches. All 909 state
  files (68,770,413 bytes) were byte-identical after verification/reconciliation.
- Wall time: 2.010673083 seconds. Process peak RSS: 242,434,048 bytes; child peak
  RSS: 134,643,712 bytes. Both are below the declared 512 MiB individual budgets;
  elapsed time is below 60 seconds. These are observed local acceptance budgets,
  not an inherited SLA or hard OS memory limit. Network time is excluded. RSS
  values are lifetime high-water marks; child measurement includes earlier
  gh/git calls. They are not additive concurrent-memory measurements.
- At 2026-09-07T02:15:57Z all paginated open CodeQL, Dependabot and secret-scanning
  alert lists were empty. Ruleset 22180861 is active on the default branch with
  strict three-OS/analyze/lint/Codecov gates, PR/review-thread resolution,
  deletion and non-fast-forward protection. Maintainer always-bypass is retained
  and disclosed. These are current hosted policy observations, not exact-head CI.

## Reproduce

In an isolated checkout of the reviewed software commit, copy this evidence probe
into the same relative location and invoke from the repository root:

```sh
uv run --locked python evidence/assurance/ordered-integration-20260907/resource-probe.py.txt
```

The probe refuses another HEAD, optimized Python, or Actions context. It requires
existing authenticated `gh` read access and an unexpired artifact; it never
requests new authorization or dispatches anything. `gh api --paginate --slurp`
follows each alert endpoint's pagination convention. Its fixed commands and
source-response hashes are recorded in the receipts. API bodies containing
opaque identifiers are projected to relevant public fields; original response
digests remain recorded. No tokens, signed download URLs or stderr are retained.

The source is executable Python retained as text, matching the earlier forensic
probe convention. Source ZIP and extracted data stay under ignored
`.tmp/ordered-resource-*`; they are not committed. Each invocation creates fresh
scratch and refreshes the output receipts. The source must remain frozen during
execution. Artifact expiry requires explicit selection of new authenticated
evidence, not bypassing metadata checks.

## Fixity and verification

`receipt-index.json` binds the probe, both attempt records and all JSON receipts.
Probe SHA-256: `e0c203df6bb3018e2d9fd4c2624eef13ea9b678c1d050fa04c66c9ba4e8aa450`.
Resource receipt SHA-256: `55679f298a871a6d3a2804370fd56c756e09edd0fa90bce460892095648fad7c`.
Security/ruleset receipt SHA-256: `2ec61d15c9124885eb9245524cc47c9fcdb942fb94e07da99f64826281b14b31`.

Initial wrong batch-label failure and subsequent unsupported Dependabot page
parameter failure are retained in attempt-01/02. Neither is represented as a
successful final run. Final source and receipt hashes were checked separately.
The targeted detect-secrets scan with the repository's unchanged receipt-line
exclusion and all plugins found zero candidates. An initial scan without those
receipt exclusions flagged only hex commit/digest values. No scanner rules were
changed. This targeted scan is not the parent's full supply-chain harness.
