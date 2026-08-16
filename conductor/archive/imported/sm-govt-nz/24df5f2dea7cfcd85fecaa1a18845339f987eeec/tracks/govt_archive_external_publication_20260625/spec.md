# Spec - NZ Government Archive - external publication and storage hardening

## Problem
Raw archive payloads are too large for routine git commits. The repository should store reproducible state, reports, manifests, and publication metadata, while GitHub Actions publishes heavy bundles to external storage.

## Scope
Harden publication to GitHub artifacts, Hugging Face, Zenodo, and optional OSF. Preserve `commit_payloads=true` as an explicit escape hatch only.

## Required Outputs
- Workflow tests for publication targets and payload commit gating.
- Publication status report that distinguishes success, failure, missing secret, and not requested.
- Manual release lane for Zenodo DOI snapshots.
- Optional OSF target gated by `OSF_TOKEN` and `OSF_UPLOAD_URL`.

## Acceptance Criteria
- Heavy raw and normalized payloads are not committed by default.
- Publication status is machine-readable.
- CI verifies workflow wiring for targets and commit gating.
