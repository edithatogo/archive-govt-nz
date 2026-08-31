# Specification - DigitalNZ Gazette Source Archive

## Overview

Archive DigitalNZ New Zealand Gazette records as a separate source layer using
the local `dnz` DigitalNZ CLI/resource repo where practical. DigitalNZ metadata
and full text are preserved as source evidence and comparison input, not as a
direct replacement for official Gazette artifacts.

## Functional Requirements

- Reuse or harden `C:\Users\60217257\OneDrive - Flinders\repos\legal-nz\dnz`
  for DigitalNZ search/export rather than adding a duplicate DigitalNZ client
  inside this repository.
- Create or link a `dnz` repo issue/track for Gazette export mode, public API
  credential behavior, deterministic paging, JSONL/page manifest output, and
  validation evidence.
- Query DigitalNZ for `primary_collection=New Zealand Gazette` with resumable,
  deterministic paging and stable JSONL output.
- Preserve complete DigitalNZ records, including IDs, titles, dates,
  descriptions/full text, landing URLs, source URLs, rights/licence fields, and
  DigitalNZ collection metadata.
- Record DigitalNZ API request metadata, query parameters, page numbers,
  timestamps, and hashes in source manifests.
- Provide a compatibility decision for public anonymous API access versus
  `DIGITALNZ_API_KEY` when the `dnz` CLI requires a key.

## Non-Functional Requirements

- Keep API use rate-limited and resumable.
- Avoid overclaiming DigitalNZ as canonical when official Gazette artifacts are
  available.
- Keep raw API JSON pages and normalized JSONL outputs reproducible.
- Track dependency boundaries between `corpus-law-nz` and `dnz`.

## Acceptance Criteria

- A bounded DigitalNZ Gazette smoke export produces raw JSON/page evidence,
  normalized JSONL, source manifest, and review report.
- Tests cover query construction, paging state, provenance fields, and rights
  preservation.
- The track records whether changes are required in `dnz` and how they are
  validated.
- Any required `dnz` work is tracked in the `dnz` repository and referenced
  from this track before this repository depends on it.
- DigitalNZ records can feed Track 46 comparison without mutating raw official
  source archives.

## Out of Scope

- Official Gazette website retrieval.
- Historical archive scraping.
- Treating DigitalNZ text as canonical without comparison evidence.
