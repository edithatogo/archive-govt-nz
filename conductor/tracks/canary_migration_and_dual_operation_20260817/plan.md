# Track 10 Plan: Canary Migration and Dual Operation

## Phases

### Phase 1: Canary Source Selection & Configuration
- [ ] Select low-risk canary candidate (e.g. Ministry of Health RSS feed and Bluesky public account).
- [ ] Configure shadow runner in GitHub Actions.

### Phase 2: Dual Operation Execution & Parity Monitoring
- [ ] Run 2 consecutive live capture cycles.
- [ ] Verify fixity and parity using `tools/differential_parity_harness.py`.

### Phase 3: Rollback Rehearsal & Signoff
- [ ] Execute rollback drill to prove zero-downtime recovery.
- [ ] Emit canary signoff report in `evidence/migrations/sm-govt-nz/canary-run-report.json`.
