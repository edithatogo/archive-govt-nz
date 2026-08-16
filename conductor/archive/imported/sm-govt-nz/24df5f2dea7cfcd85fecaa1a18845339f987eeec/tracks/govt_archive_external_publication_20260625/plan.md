# Plan - NZ Government Archive - external publication and storage hardening

## Dependencies
Depends on `govt_archive_noncredential_adapters_20260625`.

## Phase 1: Publication Contract
- [x] Task 1: Define artifact, Hugging Face, Zenodo, and OSF target semantics.
- [x] Task 2: Keep OSF explicit rather than part of default `all` until configured.
- [x] Task 3: Include raw payload checksums and normalized manifests in every publication.

## Phase 2: Workflow Hardening
- [x] Task 4: Default archive runs to commit reports/manifests only.
- [x] Task 5: Retain `commit_payloads=true` as an explicit debug/emergency path.
- [x] Task 6: Upload generated bundles as GitHub Actions artifacts when external secrets are absent.

## Phase 3: Cadence
- [x] Task 7: Schedule Hugging Face rolling updates for fresh non-credential captures.
- [x] Task 8: Keep Zenodo manual and DOI-oriented.
- [x] Task 9: Add OSF replication after secrets are configured.

## Phase 4: Review and Handoff
- [x] Task 10: Run `$conductor-review`, apply fixes, and rerun CI workflow tests.
- [x] Task 11: Add git notes with artifact locations and target status.

