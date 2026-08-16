# Specification - Courts of New Zealand Bluesky Mirror Account

## Overview
Create and configure a dedicated Bluesky mirror account for Courts of New
Zealand content using the same systematic mirror identity rules as the X
mirror. This is an outbound platform track and must remain separate from
archive-only capture state.

## Requirements
1. Account identity:
   - Use an unofficial mirror name based on `Mirror: Courts of New Zealand`.
   - Do not post under Dylan Mordaunt, `edithatogo`, or any personal identity.
   - Use `edithatogo@gmail.com` for account administration where practical.
   - Include source attribution to `courtsofnz.bsky.social`.
2. Posting contract:
   - Source records must come from the approved Courts of New Zealand source
     feed/archive, not from personal accounts.
   - Mirror posts must preserve source text and attribution without commentary.
   - Duplicate-prevention state must be separate from archive state and any X
     posting state.
   - Historical corpus sync is required as a bounded Bluesky backlog mode because
     Bluesky/AT Protocol can represent posts as repository records and the
     source corpus can be read through public AT Protocol archive paths.
3. Guardrails:
   - No live posting until account identity, credentials, dry run, and review
     gates are complete.
   - Historical records may be posted to the Bluesky mirror only through the
     explicit backlog mode, bounded by `backlog_max_posts_per_run`, and tracked
     in `conductor/bluesky_backlog_state.json`.
   - LinkedIn remains source-only and must not influence this posting track.

## Acceptance Criteria
- The Bluesky mirror account exists with archived profile evidence.
- Required credentials are documented in `config/secrets.schema.json` and setup
  docs without storing secrets in Git.
- A dry-run plan demonstrates one source post mapping to one mirror post.
- A historical-sync dry run can map the archived Courts corpus, and live backlog
  batches can post in bounded oldest-first runs after credentials validate.
- A controlled live test posts only new content and records the resulting URL.
