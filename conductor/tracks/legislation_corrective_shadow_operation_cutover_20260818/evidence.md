# Evidence: Operational Continuity Cycles and Recovery Drill

## Evidence Receipts
- `evidence/migrations/corpus-legislation-nz/operational-continuity-recovery-receipt.json`
- `tools/verify_operational_continuity_and_recovery.py`
- `tests/canary/test_operational_continuity_and_recovery.py`
- `.github/workflows/scheduled-legislation-harvest.yml`
- `.github/workflows/monthly-legislation-reconciliation.yml`
- `.github/workflows/quarterly-legislation-recovery.yml`

## Operational Cycles
- Cycle 1: `sched-weekly-harvest-20260818-001` (`changed`, 500 works, 0 failures)
- Cycle 2: `monthly-recon-20260819-001` (`no_change`, 500 works, 0 failures)

## Recovery Drill Parity
- Reconstructed records: 5 / 5
- Manifest root match: `true`
- Mismatches: 0
- Remote publish attempted: `false`
