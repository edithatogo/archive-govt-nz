# Specification - NZLII Redundancy Reconciliation

## Overview

Add NZLII as an independent redundancy source for coverage comparison, missing
record triage, and possible text rescue. NZLII-derived evidence must be
secondary to official NZ Legislation records unless explicitly reconciled and
marked as non-canonical fallback content.

## Functional Requirements

- Inventory relevant NZLII legislation collections and URL patterns.
- Build or specify a candidate matcher from official work/version metadata to
  NZLII pages.
- Compare NZLII coverage against `seeds/work_ids.txt`, review reports, and
  failed/missing official records.
- Store NZLII provenance for candidate matches, including URL, title, date,
  retrieval timestamp, content hash, and confidence score.
- Emit reconciliation reports that classify matches as exact, probable,
  ambiguous, missing, or out of scope.
- Support text rescue only as a clearly marked fallback when official paths fail
  and policy permits.

## Non-Functional Requirements

- Respect NZLII access terms, robots policy, and conservative pacing.
- Treat NZLII as corroborating evidence, not the canonical source of truth.
- Preserve source-rights caveats and avoid overclaiming license scope.
- Keep ambiguous matches out of canonical records until manually reviewed.

## Acceptance Criteria

- NZLII source inventory and caveats are documented.
- Candidate matching has tests for exact, ambiguous, and no-match cases.
- Reconciliation reports can be generated without modifying canonical data.
- Any text rescue path records provenance and fallback status explicitly.

## Out of Scope

- Replacing official NZ Legislation as the primary source.
- Bulk scraping without an approved access and rate-limit policy.
- Treating NZLII formatting as equivalent to official XML/HTML without review.
