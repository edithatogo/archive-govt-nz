# Archive evidence ledger

Generated: `2026-08-18T11:22:48.970185+00:00`

| Stage | State | Evidence |
| --- | --- | --- |
| discovered | observed | evidence/phase-2-live-observation.json |
| eligible | policy-implemented | src/archive_govt_nz/resource_policy.py |
| captured | original-and-datastore-fallback-captured | evidence/phase-6-capture-summary.json, evidence/phase-10-closeout-checkpoint.json |
| validated | software-gates-passed | build/pip-audit.json, build/sbom.cdx.json |
| transformed | derivative-foundation | src/archive_govt_nz/derivatives.py |
| uploaded | uploaded-remotely-verified | conductor/tracks/treasury_archive_mvp_20260731/evidence/phase-9-release-reconciliation.json |
| remotely-verified | remote-readback-verified | conductor/tracks/treasury_archive_mvp_20260731/evidence/phase-9-release-reconciliation.json |
| released | reconciled-release | conductor/tracks/treasury_archive_mvp_20260731/evidence/phase-9-release-reconciliation.json |
| unavailable | tombstoned | evidence/phase-10-closeout-checkpoint.json |
| restricted | rights-restricted | src/archive_govt_nz/resource_policy.py, evidence/phase-10-closeout-checkpoint.json |

## Treasury resource outcome reconciliation

- Original source captured: 12
- DataStore fallback captured: 44
- Authoritative replacements evidenced: 31
- Unavailable/tombstoned: 1
- Rights-restricted: 2
- Counts overlap; see the checkpoint and do not sum them.
