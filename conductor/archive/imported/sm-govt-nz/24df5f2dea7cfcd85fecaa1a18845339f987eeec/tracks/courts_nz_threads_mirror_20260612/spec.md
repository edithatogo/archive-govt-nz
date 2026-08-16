# Specification - Courts of New Zealand Threads Mirror Account

## Overview
Create and configure a dedicated Threads mirror account for Courts of New
Zealand content. Threads posting is a separate outbound track and must not reuse
personal Instagram/Threads identity or LinkedIn credentials.

## Requirements
1. Account identity:
   - Use an unofficial mirror name based on `Mirror: Courts of New Zealand`.
   - The prepared account is `https://www.threads.com/@mirnzcourts`.
   - Do not post under Dylan Mordaunt, `edithatogo`, or any personal identity.
   - Use `edithatogo@gmail.com` for account administration where practical.
   - Include source attribution to `courtsofnz.bsky.social`.
2. Posting route:
   - Prefer official Meta/Threads API routes if free and suitable for the
     mirror account.
   - Meta documents a 250 API-published-posts-per-rolling-24-hour limit for
     Threads profiles; configure any launch/backlog rate below that platform
     ceiling.
   - Use Buffer only if it preserves account identity, attribution, and
     duplicate-prevention guarantees.
   - Do not use browser automation for unattended posting unless a later review
     explicitly approves that risk.
   - Treat Threads as ongoing-forward mirroring by default. The current official
     Threads API supports publishing posts but does not provide a true
     historical import/backdate route for a mirror corpus.
3. Guardrails:
   - No live posting until account identity, credentials, dry run, and review
     gates are complete.
   - Do not enable Threads posting until the Bluesky backlog mirroring run is
     complete or explicitly paused.
   - The scheduled pipeline may include a no-posting Threads readiness gate so
     the next platform is visible without creating side effects.
   - Historical records must not be posted as a backlog. Any historical replay
     to Threads must be a separate reviewed batch job because it would publish
     records as current Threads posts.
   - LinkedIn remains source-only and must not influence this posting track.

## Acceptance Criteria
- The Threads mirror account exists with archived profile evidence.
- Required credentials and platform limits are documented without storing
  secrets in Git.
- A dry-run plan demonstrates one source post mapping to one Threads post or
  thread.
- Historical corpus replay is explicitly marked unsupported for default launch
  and deferred unless a later reviewed batch-replay plan is approved.
- A controlled live test posts only new content and records the resulting URL.
