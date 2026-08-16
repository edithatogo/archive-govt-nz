# Track 13 Specification: Observation, Donor Deprecation and Archival

## Purpose
Observe the stability of `archive-govt-nz` across multiple scheduled operational cycles and formally archive `sm-govt-nz` only after comprehensive stability criteria are met.

## Context & Objectives
1. Require at least two normal, uninterrupted operational capture and publication cycles in `archive-govt-nz`.
2. Verify that no parity regressions or dropped sources occur.
3. Conduct a full restore rehearsal from external publications.
4. Add redirection notice to `sm-govt-nz/README.md` pointing to `archive-govt-nz`.
5. Apply final Git tag `v0.1.0-consolidated-into-archive-govt-nz` and set donor repository to read-only archived state.

## Deliverables
- `docs/migrations/sm-govt-nz/consolidation-closeout-report.md`
- Final archival attestation receipt
