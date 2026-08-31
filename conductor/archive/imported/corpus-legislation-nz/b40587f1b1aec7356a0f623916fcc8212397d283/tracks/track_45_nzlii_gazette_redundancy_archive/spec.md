# Specification - NZLII Gazette Redundancy Archive

## Overview

Evaluate NZLII as an independent Gazette redundancy source and archive it as a
separate source layer only if robots, access, rights, and coverage checks pass.
If NZLII access is blocked or unsuitable, the track must record that evidence
and define revisit criteria.

## Functional Requirements

- Confirm whether NZLII hosts usable New Zealand Gazette material and record
  robots/access behavior for candidate URLs.
- Document coverage, URL patterns, identifiers, rights notes, and source-tier
  status before retrieval.
- If usable, archive NZLII raw pages or records independently with manifests,
  hashes, source URLs, timestamps, rights notes, and normalized JSONL output.
- If not usable, record NZLII as an unavailable or blocked source with evidence,
  impact, and revisit criteria.
- Keep NZLII as a secondary corroboration/fallback source, not the default
  canonical source.

## Non-Functional Requirements

- Respect robots/access controls and avoid circumvention.
- Keep retrieval bounded, identifiable, and rate-limited.
- Preserve NZLII source outputs separately from official, DigitalNZ, and
  historical archives.
- Make blocked/unavailable states explicit and reviewable.

## Acceptance Criteria

- NZLII coverage and access decision is documented with evidence.
- Usable NZLII samples, if allowed, produce raw artifacts, normalized records,
  manifest, hashes, and review output.
- If blocked, a source-state record documents the blocker and revisit criteria.
- Tests cover usable and unavailable source states.

## Out of Scope

- Bypassing NZLII access controls.
- Promoting NZLII records to canonical without Track 46 comparison.
- Relying on NZLII as the only historical source.
