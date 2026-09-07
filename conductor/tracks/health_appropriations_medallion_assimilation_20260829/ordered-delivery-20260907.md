# Ordered health delivery

PR #421 merged through normal protected checks at 2026-09-07T05:15:14Z.
Reviewed head: `f0bf7db902b29fa6c0818edbb8bf731c407bbe6f`.
Merge commit: `2c76fc3c3d742da6cbf76abfa86db9b8ee55ca1d`.
Hosted assurance run: `34085350385`; Linux, macOS and Windows all passed.
Windows job `101628214067` completed in 11m45s. CodeQL, lint and patch
coverage passed; the optional supplemental job was skipped, not represented as
executed. All review findings were resolved; no bypass was used.

The exact-head full local gate passed 5,598 tests and all configured follow-on
checks. Earlier failed attempts and successful intermediate gates remain in
`evidence/assurance/pr421-local-coverage-20260907/`.

Independent acceptance audit supports two bounded functional transitions:

- Phase 2.1 Bronze integrity tests, including interruption/resume, transport
  length, WARC/source/CAS binding and strict framing.
- Phase 4.1 five-table/312-row parity oracle and source-coordinate repair ledger.

Neither transition approves the 29 restorations or precision difference,
completes whole-area normalization, clears source rights, authorizes publication,
or completes the track. The track remains in progress.

## Normalization boundary delivery

PR #422 merged at 2026-09-07T05:29:07Z as
`b82d1386dce15863b362c7638a9fc1717323ba62`, reviewed head
`b6065ceeed67df8f02e3ffc034bf3868514053c4`. All required checks passed,
including three OS checks in run `34086185534`; Windows job `101630562798`
completed in 12m20s. The ancestry update after #421 preserved the exact tree
`c33a7907d257e91b9fc86937417aa702b33e3172`.

This delivers the bounded donor SQLite reader, exclusive output boundary and
Budget layout-drift contracts. It does not close all normalization, mapping,
source coverage or analytical-selection requirements. No additional whole-phase
checkbox transition is inferred from this delivery.
