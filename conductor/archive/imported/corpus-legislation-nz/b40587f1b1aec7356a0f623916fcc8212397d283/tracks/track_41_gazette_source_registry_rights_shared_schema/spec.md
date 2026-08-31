# Specification - Gazette Source Registry, Rights, And Shared Schema

## Overview

Define the source registry and shared schema contract for a multi-source New
Zealand Gazette archive. Each source must be archived independently, while the
canonical Gazette layer remains a derived, reproducible comparison output.

## Functional Requirements

- Define stable source IDs for the official Gazette site, DigitalNZ via the
  local `dnz` CLI/resource repo, the Victoria/LexisNexis historical archive,
  and NZLII if access and rights checks permit use.
- Record source-tier, rights, robots/access notes, retrieval limits, expected
  record forms, and canonical eligibility for each source.
- Define a source coverage matrix keyed by year, issue ID, notice ID, page
  range, artifact type, and source ID so gaps and overlaps are visible before
  canonical comparison runs.
- Define the raw source archive record schema used by all source-specific
  tracks, including stable ID, source URL, retrieval method, timestamp,
  content hash, HTTP metadata where available, source-local identifiers, rights
  note, and raw artifact path.
- Define the canonical Gazette schema, including canonical source, supporting
  sources, conflicts, confidence, normalization version, and provenance links
  back to source archives.
- State that raw source archives are immutable evidence layers and canonical
  records are derived outputs that must be reproducible from source manifests.

## Non-Functional Requirements

- Preserve deterministic IDs, stable ordering, hashes, and manifests.
- Keep source-specific rights caveats attached to raw and canonical records.
- Preserve web-archive-quality capture evidence, such as request/response
  metadata and WARC/CDX-compatible fields where practical, for public web
  pages and PDFs.
- Use conservative, identifiable, rate-limited retrieval policies.
- Avoid broad scraping, anti-bot bypass, or publication claims before source
  rights and review gates are satisfied.

## Acceptance Criteria

- A documented and machine-readable Gazette source registry exists.
- Raw archive and canonical Gazette schemas exist and include provenance,
  rights, and conflict fields.
- The coverage matrix can report source coverage by year, issue, notice, page
  range, and artifact type.
- The registry identifies canonical precedence and source-specific caveats.
- Future source-specific tracks can validate their outputs against this shared
  contract.

## Out of Scope

- Implementing source harvesters.
- Publishing the Gazette archive publicly.
- Treating secondary-source material as canonical without comparison evidence.
