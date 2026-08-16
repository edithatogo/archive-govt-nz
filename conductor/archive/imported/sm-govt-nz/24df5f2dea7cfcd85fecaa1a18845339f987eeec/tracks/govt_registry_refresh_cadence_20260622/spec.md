# Specification - Registry Verification Refresh Cadence

## Overview
Define how the government social media registry remains current after initial mapping. The cadence must handle normal monthly checks and high-risk change events such as elections, by-elections, Cabinet reshuffles, party leadership changes, agency restructures, and platform deactivations.

## Requirements
- Record when profiles were last verified and last seen.
- Distinguish current, inactive, deactivated, historical, and unknown verification states.
- Define refresh windows:
  - monthly for sitting MPs, parties, agencies, and public sector leaders;
  - event-triggered after elections, by-elections, reshuffles, leadership changes, and agency restructures;
  - annual for historical figures and inactive accounts.
- Produce a machine-readable report showing stale records and records needing manual review.

## Acceptance Criteria
- Registry records or companion metadata can identify stale verifications.
- A script or documented command can produce a refresh report without mutating registry data.
- The report separates current operational gaps from historical/inactive records.
- Conductor status names the next refresh cohort and blocker, if any.
