# Specification - Cross-Source Comparison And Canonical Gazette Builder

## Overview

Build the canonical NZ Gazette layer from independent source archives by
matching, comparing, and reconciling records. The canonical layer is derived and
conflict-aware; it must never replace or mutate raw source archives.

## Functional Requirements

- Match records across source archives by notice ID, issue ID, date, page,
  title, exact content hash, normalized text hash, and fuzzy text similarity
  where deterministic thresholds are defined.
- Apply default precedence: official Gazette, then DigitalNZ corroboration,
  then Victoria/LexisNexis historical source, then NZLII fallback when usable.
- Build canonical records with canonical source, supporting sources, conflicts,
  confidence, normalization version, selected fields, and provenance links.
- Preserve source disagreements as reviewable conflict records rather than
  silently choosing one source.
- Maintain a durable conflict adjudication queue and reviewed override file,
  such as `gazette_conflict_decisions.jsonl`, with decision ID, affected
  canonical/source IDs, reviewer, timestamp, rationale, selected value, and
  supporting evidence.
- Allow historical-only canonical records only when source-tier and rights
  caveats are explicit.
- Emit comparison reports with matched, unmatched, conflicting, historical-only,
  and low-confidence record counts.

## Non-Functional Requirements

- Keep canonical generation deterministic and reproducible from raw source
  manifests.
- Keep source archives immutable.
- Make confidence rules transparent and testable.
- Fail closed on unacknowledged material conflicts, missing provenance, missing
  rights, or unstable canonical IDs.

## Acceptance Criteria

- Tests cover exact matches, metadata-only matches, source conflicts, missing
  source files, low-confidence matches, and historical-only records.
- Canonical review fails on missing provenance, missing rights, unstable IDs,
  or unacknowledged conflicts.
- Reviewed conflict decisions are reproducible from the decision queue and
  override file rather than one-off notes.
- Comparison output links every canonical record back to at least one source
  archive record.
- The builder can rerun without changing outputs when inputs are unchanged.

## Out of Scope

- Harvesting source records.
- Manually adjudicating every conflict.
- Public release of canonical outputs before Track 47 staging gates pass.
