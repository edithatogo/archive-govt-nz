# Specification - Courts of New Zealand Multi-Source Archive and Dataset Pipeline

## Overview
This track expands the Courts of New Zealand mirror from a Bluesky-to-X syndicator into a multi-source evidence archive and dataset pipeline. The system must archive historical and ongoing posts from official Courts of New Zealand channels, preserve raw source evidence where practical, normalize records into a shared schema, and publish reusable corpora to Hugging Face and Zenodo. Archive capture must run alongside the syndication workflow without causing historical records or fallback-source records to be reposted.

## Current Source Findings
- Courts of New Zealand identifies Bluesky and LinkedIn as current notification channels for judgments of public interest, case synopses, court announcements, and judicial announcements.
- Courts of New Zealand states the X account is no longer active and posts before 23 March 2025 remain available there as an archive.
- Courts of New Zealand pages expose RSS subscription links on relevant website sections, including notification and publication pages.
- The judgments of public interest subscription is email-based and should be treated as an additional first-party capture source.

## Requirements
1. Historical source archive:
   - Archive historical inactive X posts for `@courtsofnz` without triggering live syndication.
   - Archive historical Bluesky posts for `courtsofnz.bsky.social`; keep the existing Bluesky history archive as the seed and make the backfill idempotent.
   - Archive historical LinkedIn posts from the official Courts of New Zealand LinkedIn page when access is available and permitted.
   - Discover and archive available Courts of New Zealand RSS feeds, including page-level RSS links.
2. Ongoing capture:
   - Add archive-only source collectors for Bluesky, LinkedIn, RSS, and email notifications.
   - Run archive capture as part of, or in parallel with, the scheduled syndication pipeline.
   - Maintain separate per-source state so a source outage or fallback capture does not alter outbound syndication state unless explicitly approved.
3. Email ingress:
   - GitHub cannot directly receive email as a mailbox. Implement an inbound email bridge using one of:
     - Cloudflare Email Routing Worker that receives the subscription email and calls GitHub `repository_dispatch` or commits raw email payloads through the GitHub API. This is the default option because Cloudflare documents Email Routing as available on Free and Paid plans, and Workers Free includes enough request capacity for low-volume notification capture.
     - Mailgun inbound parse route that posts normalized email JSON to a small receiver which calls GitHub `repository_dispatch`. This is the fallback if Mailgun's parsing/routing features are needed and a trial or paid plan is acceptable.
     - Scheduled mailbox polling through Gmail or IMAP only if webhook-style inbound delivery is unavailable.
   - Store raw `.eml` or provider JSON payloads under an email-specific raw archive path before normalization.
4. Dataset publication:
   - Publish archive bundles to Hugging Face Datasets using `HF_TOKEN` and `HF_DATASET_REPO_ID`.
   - Publish citable release snapshots to Zenodo using `ZENODO_TOKEN` and `ZENODO_DEPOSIT_ENDPOINT`.
   - Include raw-source bundles, normalized JSONL/Parquet outputs, corpus manifests, and dataset cards/readmes.
   - Preserve provenance fields: source platform, source account/feed/email, source URL, captured timestamp, original created timestamp, canonical content hash, media references, and extraction method.
5. Safety and compliance:
   - Do not repost historical X, LinkedIn, RSS, or email records.
   - Respect platform access boundaries. Prefer official APIs and first-party RSS/email sources. Use browser/session capture only for user-authorized archival where no official export/API is available.
   - Keep secrets out of Git. Use GitHub secrets for API keys/tokens and store only redacted manifests.
   - Treat each source adapter as an explicit contract with inputs, outputs, auth requirements, rate-limit behavior, archive-only guarantees, and failure modes documented before implementation.
   - Defer additional outbound syndication accounts into separate conductor tracks. Each future platform track must be granular, committed task-by-task, reviewed after each phase and track, and must not share archive state with posting state.
6. Optimization requirements:
   - Use canonical IDs and content hashes to deduplicate the same Courts notice across Bluesky, LinkedIn, RSS, email, and website pages.
   - Shard archive outputs by source and month to avoid oversized Git diffs.
   - Store normalized records separately from raw payloads.
   - Add source health reporting so failures are visible without blocking healthy sources.
   - Publish compact Hugging Face artifacts from GitHub Actions rather than relying only on Git history as the dataset store.

## Acceptance Criteria
- A repeatable archive command can capture new records from each configured source without reposting them.
- Historical X, Bluesky, LinkedIn, and RSS backfills have explicit reports listing counts, date ranges, access method, and gaps.
- Email subscription messages can enter the repository through a documented bridge and are archived as raw and normalized records.
- Hugging Face publishing can be run from GitHub Actions and produces a dataset manifest with checksums.
- Zenodo publishing can create citable corpus snapshots from the same normalized archive artifacts.
- Scheduled syndication still mirrors new Bluesky posts to X via Buffer and does not duplicate posts because of archive-only source capture.
- No new syndication target is implemented in this track; future platform mirrors are represented as separate tracks with their own contracts and reviews.
