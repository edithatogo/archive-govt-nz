# Plan - NZ Government Archive - source readiness matrix and dependency sequencing

## Purpose
Create the canonical readiness model that tells a less capable implementation agent what is discovered, registered, resolvable, capturable, normalized, published, blocked, or credential-gated.

## Dependencies
Completed registry quality gates, account classification, refresh cadence, and existing archive reports.

## Implementation Rules for Less-Capable Agents
- Work phases in order; do not skip dependency gates.
- Prefer repo-local scripts, schemas, and workflow tests over ad hoc edits.
- After each phase, run `$conductor-review`, apply findings, rerun focused tests, then commit.
- Add a git note to every phase commit summarizing scope, tests, residual blockers, and next action.
- Never mark credential-gated platforms live unless secrets, adapters, and live validation pass.

## Phase 1: Inventory Contract
- [x] Task 1: Define one machine-readable readiness row per agency/source/profile with stable IDs.
- [x] Task 2: Represent status as discovered, registered, resolver_ok, capture_ok, normalized_ok, published_ok, blocked_credential, blocked_legal, blocked_technical, stale, or retired.
- [x] Task 3: Add source-type required fields for website_page, rss, bluesky, youtube, newsletter, facebook, instagram, threads, linkedin, and x.

## Phase 2: Dependency Model
- [x] Task 4: Encode dependency sequencing so adapter work cannot claim success before registry and resolver gates pass.
- [x] Task 5: Separate archive-only sources from outbound-mirror sources.
- [x] Task 6: Preserve credential-gated platforms as explicit pending/onboarding records rather than failed captures.

## Phase 3: Reports
- [x] Task 7: Generate `conductor/govt_archive_readiness_matrix.json`.
- [x] Task 8: Generate a markdown summary grouped by agency and source type.
- [x] Task 9: Expose counts for total discovered, registered, capturable without credentials, captured, published, and blocked.

## Phase 4: Review and Handoff
- [x] Task 10: Run `$conductor-review` after the matrix schema and first generated report exist.
- [x] Task 11: Apply review fixes before marking the track complete.
- [x] Task 12: Record commit notes that identify the next dependent track to run.

## Acceptance Criteria
- [x] A less capable agent can choose the next archive task by sorting the readiness report.
- [x] No credential-gated platform is reported as archive-live unless a tested adapter and credential path exist.
- [x] The readiness matrix can be regenerated in CI without mutating source registry records.

## Commit and Review Protocol
- Commit after each phase with a concise hyphenated message.
- Add `git notes` describing implementation evidence and review status.
- Run `$conductor-review` after each phase and auto-apply review fixes before starting the next phase.
# Plan - NZ Government Archive - source readiness matrix and dependency sequencing

## Purpose
Create the canonical readiness model that tells a less capable implementation agent what is discovered, registered, resolvable, capturable, normalized, published, blocked, or credential-gated.

## Dependencies
Completed registry quality gates, account classification, refresh cadence, and existing archive reports.

## Implementation Rules for Less-Capable Agents
- Work phases in order; do not skip dependency gates.
- Prefer repo-local scripts, schemas, and workflow tests over ad hoc edits.
- After each phase, run `$conductor-review`, apply findings, rerun focused tests, then commit.
- Add a git note to every phase commit summarizing scope, tests, residual blockers, and next action.
- Never mark credential-gated platforms live unless secrets, adapters, and live validation pass.

## Phase 1: Inventory Contract
- [x] Task 1: Define one machine-readable readiness row per agency/source/profile with stable IDs.
- [x] Task 2: Represent status as discovered, registered, resolver_ok, capture_ok, normalized_ok, published_ok, blocked_credential, blocked_legal, blocked_technical, stale, or retired.
- [x] Task 3: Add source-type required fields for website_page, rss, bluesky, youtube, newsletter, facebook, instagram, threads, linkedin, and x.

## Phase 2: Dependency Model
- [x] Task 4: Encode dependency sequencing so adapter work cannot claim success before registry and resolver gates pass.
- [x] Task 5: Separate archive-only sources from outbound-mirror sources.
- [x] Task 6: Preserve credential-gated platforms as explicit pending/onboarding records rather than failed captures.

## Phase 3: Reports
- [x] Task 7: Generate `conductor/govt_archive_readiness_matrix.json`.
- [x] Task 8: Generate a markdown summary grouped by agency and source type.
- [x] Task 9: Expose counts for total discovered, registered, capturable without credentials, captured, published, and blocked.

## Phase 4: Review and Handoff
- [x] Task 10: Run `$conductor-review` after the matrix schema and first generated report exist.
- [x] Task 11: Apply review fixes before marking the track complete.
- [x] Task 12: Record commit notes that identify the next dependent track to run.

## Acceptance Criteria
- [x] A less capable agent can choose the next archive task by sorting the readiness report.
- [x] No credential-gated platform is reported as archive-live unless a tested adapter and credential path exist.
- [x] The readiness matrix can be regenerated in CI without mutating source registry records.

## Commit and Review Protocol
- Commit after each phase with a concise hyphenated message.
- Add `git notes` describing implementation evidence and review status.
- Run `$conductor-review` after each phase and auto-apply review fixes before starting the next phase.

