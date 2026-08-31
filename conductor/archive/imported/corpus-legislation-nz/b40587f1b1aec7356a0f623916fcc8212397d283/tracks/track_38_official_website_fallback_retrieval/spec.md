# Specification - Official Website Fallback Retrieval

## Overview

Add a conservative fallback retrieval path for cases where official API metadata
or advertised XML/HTML URLs fail but the legislation page is still available on
the official NZ Legislation website. This track may use browser automation for
diagnostics and recovery, but it must not rely on stealth or access-control
bypass techniques.

## Functional Requirements

- Define the fallback order for official website retrieval after API XML,
  official HTML, and alternate dated URL attempts fail.
- Implement or specify a Playwright-based diagnostic/retrieval path for
  individual failed records.
- Capture rendered page HTML or text only when the source URL is public and
  retrieval is allowed by project policy.
- Store provenance for browser-derived captures, including source URL, retrieval
  method, timestamp, content hash, and failure reason from earlier steps.
- Emit browser fallback warnings that are visible in sync state and review
  reports.
- Keep browser fallback opt-in or narrowly scoped to failed items.

## Non-Functional Requirements

- Use identifiable, rate-limited, respectful access patterns.
- Do not use stealth mode, CAPTCHA circumvention, credentialed scraping, or
  evasion of site protections as a standard pipeline feature.
- Preserve deterministic output where possible, and isolate browser dependency
  setup from normal API-first sync paths.
- Fail closed when public page content cannot be retrieved without bypassing
  controls.

## Acceptance Criteria

- Tests cover fallback ordering, provenance fields, and warning/report output.
- Documentation states that browser fallback is non-canonical and only for
  recovery/triage.
- A manual or workflow-safe command can retry a small failed-record set.
- Review reports distinguish API/HTML fallback from browser-rendered fallback.

## Out of Scope

- Broad website crawling as the primary archive mechanism.
- Stealth scraping or anti-bot bypass.
- Replacing official API metadata with browser-discovered metadata without
  reconciliation.
