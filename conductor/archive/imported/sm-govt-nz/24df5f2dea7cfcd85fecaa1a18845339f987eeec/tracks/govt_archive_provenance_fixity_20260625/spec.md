# Spec - NZ Government Archive - provenance, fixity, and reproducible research packaging

## Problem
External publication removes heavy payloads from git, but the archive still needs durable proof that each published file corresponds to an observed public source capture. Without fixity and reproducible package metadata, later users cannot audit whether a dataset is complete, altered, or reproducible.

## Scope
Add archival-grade provenance and fixity for raw captures, normalized shards, manifests, and published bundles.

## Required Outputs
- Per-file SHA-256 checksums for raw and normalized payloads.
- Capture provenance fields: source URL, resolved URL, source type, fetch timestamp, HTTP status, content type, capture tool version, normalization tool version, and source-health classification.
- Package-level manifests suitable for Hugging Face, Zenodo, OSF, and GitHub artifacts.
- Citation metadata for dataset users, including version, capture window, license/terms notes, and DOI linkage when available.

## Acceptance Criteria
- A reviewer can verify a published bundle against repo manifests without downloading every historical raw payload locally.
- Re-running packaging over the same captured inputs produces stable manifests.
- Missing or mismatched checksums fail validation before publication.
