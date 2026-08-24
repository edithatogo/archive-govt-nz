# sm-govt-nz Donor Retirement Readiness Attestation

**Status**: READY FOR MAINTAINER ARCHIVAL AUTHORIZATION  
**Date**: 2026-08-25  
**Canonical Repository**: `edithatogo/archive-govt-nz`  
**Donor Repository**: `edithatogo/sm-govt-nz`  
**Attestation ID**: `attest-sm-govt-nz-retirement-20260825`  

---

## 1. Executive Summary

All technical, operational, and assurance gates required for the formal retirement of `edithatogo/sm-govt-nz` have been satisfied.

The original closeout claim was corrected via `evidence/migrations/sm-govt-nz/consolidation-closeout-correction.json` to reflect that parallel operations were ongoing. Following sequential activation and assimilation, all capabilities have now been absorbed and verified in `archive-govt-nz`.

---

## 2. Prerequisite Checklist

| Requirement | Verification Record | Status |
| :--- | :--- | :--- |
| **Multi-Source Capture Path Activation** | `archive-govt-nz capture` CLI runner & adapter dispatch in PR #188 | **PASSED** |
| **Differential Parity Certification** | 9/9 canonical source class fixtures verified with 0 divergences in PR #192 (`tools/run_differential_parity.py`) | **PASSED** |
| **Distribution Hub & Rollover Integration** | Multi-target publication hub (Hugging Face rollover, Zenodo, OSF, RO-Crate 1.1, Croissant 1.0) in PR #190 | **PASSED** |
| **Claim Drift Monitoring Lane** | Automated weekly GitHub Actions assurance workflow in PR #191 (`tools/check_claim_drift.py`) | **PASSED** |
| **Pinned Donor Commits** | Immutable donor SHAs pinned across track metadata and migration ledgers | **PASSED** |

---

## 3. Archival Execution Instructions for Maintainer

When ready, the solo maintainer may authorize and complete archival of `edithatogo/sm-govt-nz` by executing:

1. **Disable Workflows**: Disable all active GitHub Actions workflows in `edithatogo/sm-govt-nz`.
2. **Archive Repository**: In `edithatogo/sm-govt-nz` repository settings, select **Archive this repository** (read-only mode).
3. **Verify Claim Drift**: Run `uv run python tools/check_claim_drift.py` to record that `sm-govt-nz` is now archived and claim status is clean.
