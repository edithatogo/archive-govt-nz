# Specification

## Overview

Convert the existing one-off Internet Archive replacement search into a
scheduled redundancy and triangulation lane. The lane observes approved
government source URLs, discovers independent snapshots, captures bounded
backup bytes, verifies integrity, classifies relationships without overstating
identity, and retains evidence as GitHub Actions artefacts.

## Functional requirements

1. Run weekly and on manual dispatch with least-privilege permissions and
   bounded concurrency.
2. Discover Internet Archive timemap records for unresolved Treasury sources.
3. Download only HTTPS `web.archive.org` snapshot URLs emitted by discovery,
   enforce size and timeout limits, and hash captured bytes.
4. Produce deterministic JSON and concise Markdown triangulation reports with
   resource-level states.
5. Verify every captured object against its receipt before reporting capture.
6. Submit a small bounded number of missing, allowlisted official government
   URLs to Save Page Now; record outcomes without treating submission as
   successful capture.
7. Upload receipts and bounded backup objects as GitHub Actions artefacts.
8. Preserve previous evidence and never promote a mirror to original-source
   status solely because a snapshot exists.

## Non-functional requirements

- Fail closed for non-HTTPS archive URLs, non-allowlisted source hosts,
  redirects outside configured trust boundaries, excessive response sizes,
  malformed receipts, and hash mismatches.
- Do not retain credentials, signed URLs, cookies, response bodies from error
  pages, or sensitive payloads in logs or receipts.
- Keep network retries, request counts, duration, and storage bounded.
- Ensure deterministic receipt generation for identical inputs apart from the
  explicit observation timestamp.

## Acceptance criteria

- The scheduled workflow passes workflow-policy tests and has immutable action
  references, read-only repository permissions, concurrency, timeouts, and
  artifact retention.
- Unit, contract, property, metamorphic, and deterministic-simulation tests
  cover URL validation, classification, hashing, idempotency, and failures.
- The repository validation harness passes, or unrelated pre-existing failures
  are explicitly isolated with focused gates passing.
- GitHub parent issue #44 contains native subissues #45, #46, and #47.

## Out of scope

- Treating Internet Archive content as the authoritative original.
- Creating Zenodo releases from every scheduled observation.
- Accessing or integrating known illicit distribution services.
- Archiving non-government hosts without an explicit policy update.
