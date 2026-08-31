# Specification - Official Gazette Source Archive

## Overview

Archive the official NZ Gazette website as an independent source layer. This
track owns issue PDF discovery/download, notice-page capture, source manifests,
checksums, and extraction outputs for the official source.

## Functional Requirements

- Discover official Gazette issues from the canonical issue listing and avoid
  known problematic URL forms such as trailing-slash variants that trigger bot
  protection.
- Download issue PDFs from public official issue URLs and store raw PDFs,
  HTTP metadata, SHA-256 hashes, source URLs, retrieval timestamps, and
  manifest entries.
- Capture public notice pages referenced by official issue listings or
  DigitalNZ landing URLs when allowed by the source registry.
- Extract text and metadata from official PDFs/pages into deterministic
  source-specific JSONL records without discarding raw artifacts.
- Treat official Gazette evidence as the preferred canonical source when it is
  present and passes review.

## Non-Functional Requirements

- Use identifiable, rate-limited requests and fail closed when public content
  cannot be retrieved without bypassing controls.
- Keep source archives resumable and safe to rerun.
- Preserve raw files separately from extracted text and canonical outputs.
- Keep extraction deterministic so manifests and comparison outputs are
  reproducible.

## Acceptance Criteria

- A bounded smoke archive can retrieve at least one issue PDF and one notice
  page with manifest, HTTP metadata, hashes, and provenance.
- Tests cover issue URL normalization, manifest writing, hashing, and
  extraction output.
- Review output distinguishes official raw artifacts from derived canonical
  records.
- The implementation does not use stealth mode, CAPTCHA circumvention, or
  access-control bypass.

## Out of Scope

- DigitalNZ harvesting.
- Historical Victoria/LexisNexis or NZLII retrieval.
- Public publication of the official source archive.
