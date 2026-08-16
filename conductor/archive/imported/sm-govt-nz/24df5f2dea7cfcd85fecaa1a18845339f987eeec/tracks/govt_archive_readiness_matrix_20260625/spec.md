# Spec - NZ Government Archive - source readiness matrix and dependency sequencing

## Problem
Credentialed mirroring and account creation cannot be assumed for every government platform. The project needs an archive-first readiness model that maximizes public capture now while keeping credentialed platforms explicit, safe, and sequenced.

## Scope
Create the canonical readiness model that tells a less capable implementation agent what is discovered, registered, resolvable, capturable, normalized, published, blocked, or credential-gated.

## Dependency
Completed registry quality gates, account classification, refresh cadence, and existing archive reports.

## Non-Goals
- Do not automate personal-account login, cookie reuse, or unsanctioned platform access in GitHub Actions.
- Do not claim source coverage where only candidate discovery exists.
- Do not commit large raw archive payloads by default when artifact publication is available.

## Required Outputs
- `conductor/govt_archive_readiness_matrix.json`.
- A markdown summary grouped by agency and source type.
- Source-type readiness counts for total discovered, registered, capturable without credentials, captured, published, blocked, and stale.
- Tests for schema validation and dependency sequencing.

## Acceptance Criteria
- A less capable agent can choose the next archive task by sorting the readiness report.
- No credential-gated platform is reported as archive-live unless a tested adapter and credential path exist.
- The readiness matrix can be regenerated in CI without mutating source registry records.
