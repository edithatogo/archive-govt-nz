# Specification - Account Classification and Tenure-Linked Profiles

## Overview
Classify mapped social accounts so the registry distinguishes official government channels from party, campaign, office, and personal-public accounts. This track also links accounts to role tenures so account ownership changes remain auditable over time.

## Requirements
- Define account classifications:
  - `official`
  - `campaign`
  - `personal-public`
  - `office`
  - `party`
  - `inactive`
  - `deactivated`
- Define syndication classification:
  - `unique`
  - `syndicated`
  - `mixed`
  - `unknown`
- Populate `tenure_linked_profiles` for role-based accounts once taxonomy and evidence fields are accepted.
- Preserve current registry validation and strict reference integrity.

## Acceptance Criteria
- Schemas accept the taxonomy without weakening existing required fields.
- At least one representative person record demonstrates role-linked profiles.
- Classification can be applied without changing posting or mirroring behavior.
- Tests cover valid classifications, invalid classifications, and tenure-linked profile references.
