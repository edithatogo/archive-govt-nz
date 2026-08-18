# Operational Cutover Runbook: `corpus-legislation-nz` → `archive-govt-nz`

**Baseline Date**: 18 August 2026

---

## 1. Pre-Cutover Verification

1. Confirm target baseline is green with all 19 quality gates passing (`tools/check.py`).
2. Verify all 68 historical batch checkpoints and seed inventory hashes match target CAS receipts.
3. Validate CLI subcommands (`archive-govt-nz legislation coverage`, `validate`, `replay`).

---

## 2. Cutover Execution Steps

1. **Disable Donor Scheduled Workflows**:
   - Deactivate all 25 active workflows on `edithatogo/corpus-legislation-nz`.
2. **Enable Target Scheduled Multi-Source Harvest**:
   - Confirm `.github/workflows/scheduled-multi-source-harvest.yml` contains `legislation` and `nz-gazette` source sets.
3. **Publish Redirect Notice on Donor**:
   - Update donor root `README.md` with official migration notice pointing to `archive-govt-nz`.
4. **Push Immutable Release Tag**:
   - Create and push final release tag `v0.9.0-archived` on donor.
5. **Reconcile Donor Issues**:
   - Close open donor issues with reference to target PRs and issue reconciliation ledger.
6. **Archive Donor Repository**:
   - Set donor repository to read-only Archive state on GitHub.
