# Spec - NZ Government Discovery - self-improving heuristic search and learning loop

## Problem
Government account discovery remains incomplete and changes over time. Discovery should improve from evidence, false positives, and platform-specific search results rather than repeating static queries.

## Scope
Daily discovery with homepage probes, domain heuristics, sitemap/feed discovery, platform-native search where allowed, scoring, false-positive suppression, and auditable promotion to the registry.

## Required Outputs
- Heuristic library for `.govt.nz`, `.ac.nz`, `.mil.nz`, `.parliament.nz`, councils, Crown entities, and public-sector bodies.
- Daily candidate report split into new, already registered, rejected, and needs-review.
- Learning ledger recording promoted/demoted heuristics.

## Acceptance Criteria
- Daily discovery improves candidate reports without local downloads.
- Heuristics are auditable, reversible, and scored.
- No candidate is promoted to archive-live without evidence and readiness status.
