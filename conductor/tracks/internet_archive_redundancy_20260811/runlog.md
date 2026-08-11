# Run Log

## 2026-08-11 — track initialization

- Confirmed the existing Internet Archive utilities were one-off commands and
  were not referenced by a scheduled workflow.
- Created GitHub parent issue #44 and native phase subissues #45–#47.
- Began Phase 1 with security and deterministic-contract tests.

## 2026-08-11 — Phase 1 contracts and hardening

- Observed the required red phase: redundancy tests initially failed because
  `archive_govt_nz.redundancy` did not exist.
- Implemented exact HTTPS Internet Archive host validation, official-source
  allowlisting, bounded configuration, object size/hash verification, closed
  classifications, and canonical deterministic reports.
- Added unit, property, metamorphic, contract, deterministic simulation, and
  mutation testing. Focused coverage is 100% line and branch; six of six
  targeted mutants were killed.
- Hardened the existing snapshot downloader so discovery receipts cannot direct
  it to arbitrary schemes or hosts.

## 2026-08-11 — Phase 2 routine workflow

- Added weekly Wednesday 04:17 UTC and manual workflow dispatch.
- Added resource-level verification and Markdown/JSON reports, 90-day artefact
  retention, and bounded Save Page Now submission for five missing official
  URLs per run.
- A local enabled probe submitted one allowlisted data.govt.nz resource with
  HTTP 200 and retained the state as `submitted-pending-verification`.
- Initial hosted run `31455815690` was cancelled during read-only discovery
  because sequential external timeouts threatened the job budget.
- Added deterministic two-worker discovery/capture concurrency and reduced the
  hosted run to bounded 15/30-second per-request timeouts.

## 2026-08-11 — Phase 3 assurance and hosted verification

- Full local harness passed: 295 tests, 95.77% overall branch coverage, 100%
  redundancy-module coverage, schemas, 17 total targeted mutations, dependency
  audit, licence policy, secret scan, and CycloneDX SBOM.
- Removed two secret-scanner test-fixture false positives rather than accepting
  them as baseline noise.
- Hosted read-only run `31456041007` succeeded and retained 47 classifications,
  seven objects, and zero object-verification failures.
- Hosted enabled run `31456550945` succeeded on revision `cb84ae6`: three
  archive objects were captured in that observation, thirteen capture attempts
  failed, twenty URLs were unavailable, two of five Save Page Now requests were
  accepted, and three failed. All outcomes remain explicit and retryable on the
  next schedule.
- CI, CodeQL, and workflow-policy lint passed on revision `cb84ae6`.
