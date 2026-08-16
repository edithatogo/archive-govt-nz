# Spec - NZ Government Archive - quality gates, observability, and CI/CD resilience

## Problem
Archive expansion will fail operationally unless adapter contracts, workflow inputs, publication metadata, and source-health records are validated consistently.

## Scope
Add tests and observability around discovery, resolver, capture, normalize, manifest, publish, and health-report stages.

## Required Outputs
- Adapter contract tests.
- Source-health schema validation.
- CI split between quick checks and scheduled live probes.
- Dashboard/report grouped by source type and failure class.

## Acceptance Criteria
- Failing sources have typed failures and next actions.
- CI remains fast for pushes and deeper for scheduled validation.
- Review findings become tracked tasks.
