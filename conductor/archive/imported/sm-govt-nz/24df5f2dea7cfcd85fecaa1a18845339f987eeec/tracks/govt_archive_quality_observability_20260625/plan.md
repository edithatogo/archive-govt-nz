# Plan - NZ Government Archive - quality gates, observability, and CI/CD resilience

## Dependencies
Depends on `govt_archive_external_publication_20260625` and `govt_discovery_self_learning_20260625`.

## Phase 1: Quality Gates
- [x] Task 1: Add tests for discovery, resolver, capture, normalize, manifest, and publish contracts.
- [x] Task 2: Use fixture/VCR tests for public endpoints and explicit live-smoke workflows for maintainers.
- [x] Task 3: Add schema validation for readiness and source-health artifacts.

## Phase 2: Observability
- [x] Task 4: Create health reports grouped by source type and failure class.
- [x] Task 5: Track last_success, last_failure, retry_count, next_retry_after, and publication status.
- [x] Task 6: Fail CI on schema regressions, not expected external access blockers.

## Phase 3: CI/CD
- [x] Task 7: Split quick push checks from scheduled live probes.
- [x] Task 8: Cache dependencies with uv.
- [x] Task 9: Add workflow tests whenever dispatch inputs or artifact paths change.

## Phase 4: Review and Handoff
- [x] Task 10: Run `$conductor-review` after each quality-gate family.
- [x] Task 11: Add git notes listing tests, fixed failures, and residual blockers.

