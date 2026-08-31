# Specification - Source Redundancy Resolver and Provenance

## Overview

Define the shared resolver and provenance contract that coordinates official API
downloads, feed-triggered refreshes, official website fallback retrieval, and
NZLII redundancy. This track provides the policy and implementation spine for
Tracks 37-39.

## Functional Requirements

- Define the source priority order:
  `API XML -> official HTML -> alternate dated URL -> official website fallback -> NZLII candidate`.
- Store per-record retrieval attempts with source name, URL, method, timestamp,
  status, content hash, warning/error message, and canonical/fallback flag.
- Expose resolver decisions in sync state, review reports, manifests, and
  coverage or reconciliation artifacts.
- Support confidence classifications for non-canonical fallbacks.
- Keep canonical records tied to official NZ Legislation when available, with
  fallback sources used for redundancy, triage, or clearly marked rescue.
- Provide a single review surface showing which records depend on fallback or
  secondary sources.

## Non-Functional Requirements

- Preserve deterministic hashing and reproducible manifests.
- Avoid rights overclaiming by carrying source-specific rights/provenance notes.
- Keep fallback source adoption auditable and reversible.
- Maintain compatibility with the shared NZ corpus core provenance model.

## Acceptance Criteria

- A resolver policy document and machine-readable provenance schema are added.
- Tests cover resolver priority, fallback warnings, confidence classification,
  and review-report counts.
- Review reports distinguish canonical API records from fallback-assisted or
  secondary-source records.
- Documentation explains how Tracks 37-39 plug into the resolver.

## Out of Scope

- Implementing every source adapter in this track.
- Promoting secondary-source text without manual review policy.
- Changing public coverage claims before reconciliation evidence supports it.
