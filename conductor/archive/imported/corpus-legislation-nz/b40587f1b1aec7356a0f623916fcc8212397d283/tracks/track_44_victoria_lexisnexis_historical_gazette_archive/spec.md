# Specification - Victoria/LexisNexis Historical Gazette Archive

## Overview

Archive the Victoria/LexisNexis historical NZ Gazette source as an independent
historical source layer after rights, robots, and access checks. This source is
primarily for 1841-2008 historical coverage, page/year cross-checks, and
canonical comparison support.

## Functional Requirements

- Confirm and record access, robots, copyright, licence, and permitted
  retrieval boundaries before any bulk retrieval.
- Discover available historical years, issues, pages, notices, or index entries
  from the Victoria/LexisNexis archive surface.
- Archive raw index pages and any permitted content artifacts separately from
  normalized records.
- Preserve historical source identifiers, year/page references, titles, dates,
  source URLs, rights caveats, retrieval timestamps, hashes, and artifact paths.
- Mark this source as historical/secondary unless Track 46 comparison evidence
  elevates a record with explicit caveats.

## Non-Functional Requirements

- Keep rights caveats attached to every historical source record.
- Use conservative retrieval, bounded smoke tests, and fail-closed behavior if
  access terms are unclear.
- Preserve raw historical artifacts even when normalized extraction changes.
- Avoid mixing historical source outputs with official or DigitalNZ raw
  archives.

## Acceptance Criteria

- Rights/access review is documented before retrieval beyond a bounded smoke
  sample.
- A bounded historical sample can produce raw artifacts, normalized records,
  manifest, hashes, and review output.
- Tests cover historical ID formation, year/page references, rights caveats,
  and manifest validation.
- Historical-only canonical candidates are flagged with source-tier and rights
  caveats.

## Out of Scope

- Unapproved bulk historical content retrieval.
- Treating Victoria/LexisNexis as an unrestricted canonical replacement.
- DigitalNZ or official Gazette harvesting.
