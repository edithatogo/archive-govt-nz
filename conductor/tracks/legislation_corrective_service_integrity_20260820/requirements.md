# Requirements

## Must

- **SVC-M1** Remove the fixed 33,693 candidate denominator from executable
  service and reconciliation defaults; coverage denominators must come from the
  bounded discovered inventory supplied to the run.
- **SVC-M2** Preserve canonical work, expression, and manifestation identities
  supplied by discovery. Missing canonical identity data must be explicit and
  must not be replaced with fabricated discovery identities.
- **SVC-M3** Route manifestation acquisition through `NZLegislationAdapter` so
  transport, CAS preservation, and source status semantics have one path.
- **SVC-M4** Treat HTTP 304 as a successful `no_change` observation and retain
  the previously accounted manifestation.
- **SVC-M5** Merge new records into the cumulative manifest and retain
  cumulative checkpoint counts, work IDs, conditional request validators, and
  manifest-root accounting across runs.
- **SVC-M6** Fail closed on corrupt checkpoint or manifest state and on
  incomplete discovered FRBR identity structures.
- **SVC-M7** Pass `./scripts/validate.sh` before opening the corrective PR.

## Should

- **SVC-S1** Preserve existing explicit-target and compatibility behavior where
  it does not fabricate discovery evidence.
- **SVC-S2** Keep publication, rights, live-operation, recovery, donor archival,
  and cutover states unresolved.

## Acceptance criteria

- Focused tests demonstrate dynamic denominators, canonical discovered
  identities, adapter-only acquisition, 304/no-change, cumulative manifest and
  checkpoint accounting, and fail-closed corrupt-state behavior.
- The corrective PR targets current `main`, links #131 and #139 without using a
  closing keyword, and remains unmerged under the active freeze.
