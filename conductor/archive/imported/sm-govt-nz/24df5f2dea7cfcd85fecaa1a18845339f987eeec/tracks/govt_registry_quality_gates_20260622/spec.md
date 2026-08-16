# Specification - Registry Provenance and Batch Quality Gates

## Overview
Raise the standard for government registry expansion so new person and social-profile records are evidence-backed, reference-clean, and safe to append in batches.

This track does not add new MP/person coverage. It hardens the workflow used by coverage tracks.

## Requirements
- Extend profile schemas to support evidence metadata:
  - `source_url`
  - `verified_at`
  - `verification_method`
  - `verification_status`
  - optional `notes`
- Add strict batch validation before appending person records:
  - reject duplicate `person_id` values;
  - reject unknown role `organization` values against agency and party IDs;
  - reject malformed evidence metadata;
  - allow explicitly marked unverified accounts only when `verification_status` says so.
- Ensure the reference-integrity gate can recompute from current registry files rather than relying only on the checked-in gap report.
- Keep batch JSON files under `scripts/data/` as auditable source inputs.

## Acceptance Criteria
- Current strict gap gate is clean before schema changes begin.
- `scripts/add_person_record.py --validate-only` fails on unknown role organization IDs.
- `scripts/check_parties_persons_gaps.py --strict --allow-leaders 0 --allow-presidents 0` recomputes or verifies current registry state and exits 0 for the accepted registry.
- Focused tests cover schema evidence metadata, batch rejection, and recomputed gap behavior.
