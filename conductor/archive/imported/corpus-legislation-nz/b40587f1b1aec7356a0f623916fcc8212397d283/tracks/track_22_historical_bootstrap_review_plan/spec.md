# Specification - Historical Bootstrap Review Plan

## Overview

Turn the historical pilot into a reviewed bootstrap plan before any historical
publication workflow is enabled.

## Functional Requirements

- Retrieve and review the latest `historical-sync-pilot` artifact produced by a
  `historical_sync_pilot.yml` workflow run.
- Review `generated/historical-work-ids.provenance.json`.
- Review `data-historical-pilot/manifests/latest_manifest.json`.
- Review `data-historical-pilot/manifests/coverage_report.json`.
- Review `data-historical-pilot/_state/sync_state.json`, including
  failed-version state.
- Define batch sizes, pacing, resume checkpoints, and stop conditions for the
  historical bootstrap.
- Record the chosen publication target from Track 21.

## Non-Functional Requirements

- Keep historical publication gated until pilot evidence is reviewed.
- Preserve validation, manifest, coverage, and sync-state evidence.
- Keep failed-version and coverage caveats explicit.

## Acceptance Criteria

- Pilot artifact evidence is reviewed and summarized.
- Failed versions and coverage caveats are documented.
- Batch plan and publication target are approved before upload code is added.

## Completion Evidence

- Pilot workflow run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27138352849`.
- Artifact: `historical-sync-pilot`.
- Review document: `docs/historical_bootstrap_review.md`.
- Reviewed sample: 10 work IDs, 52 validated records, 0 failed records.
- Manifest SHA-256:
  `3a6e6abdccaa6a8124fece672a708a8f6e61389cd32b575ccc13367a5d23b0ae`.
- Historical target:
  `edithatogo/corpus-legislation-nz-historical`.
