# Specification - Courts of New Zealand Mirror

## Overview
Prioritize a single public-service mirror for Courts of New Zealand posts from Bluesky to X before expanding to other agencies or platforms.

## Functional Requirements
1. Monitor only `courtsofnz.bsky.social` for the initial live synchronization scope.
2. Syndicate only to X until additional platform credentials and account policies are configured.
3. Seed `conductor/state.json` from the current Bluesky feed so the first scheduled run does not repost historical Bluesky content.
4. Use the systematic display-name pattern `Mirror: Courts of New Zealand` for the mirror identity.
5. Identify the X mirror as unofficial and link back to the source Bluesky profile.
6. Archive the current source and mirror profile records in the repository as date-stamped evidence.
7. Document the future action to archive historical `@courtsofnz` Twitter/X posts and `courtsofnz.bsky.social` Bluesky posts into the GitHub repository before packaging them as a reusable corpus/dataset for Zenodo and Hugging Face.
8. Treat the GitHub `Syndicate` workflow's manually disabled state as the final launch safety gate until a controlled X-only test succeeds.

## MVP Acceptance Criteria
- `config.json` contains only the Courts of New Zealand source account and X as the enabled outbound target.
- `conductor/state.json` is seeded so the first run does not mirror historical Bluesky backlog.
- The X mirror profile is configured as `Mirror: Courts of New Zealand` at `@MirNZCourts`, with unofficial profile wording and a Bluesky source link.
- Current source and mirror profile evidence is committed under `profile_archive/courts-nz/2026-06-11/`.
- CI passes on the PR branch after the profile archive and roadmap updates.
- A controlled run posts only genuinely new Courts of New Zealand Bluesky content to X and advances repository state.
- The scheduled `Syndicate` workflow is re-enabled only after the controlled run is verified.

## Operational Notes
- Public Bluesky author feeds are fetched through the unauthenticated public AT Protocol endpoint, so a Bluesky account is not required for public feed reads.
- The live X mirror identity is `Mirror: Courts of New Zealand` at `@MirNZCourts`.
- The mirror bio must not describe the account as official. It should preserve the source account's public-information scope while clearly saying it is an unofficial mirror and linking to `courtsofnz.bsky.social`.
- Historical import work must write to GitHub archive files first and keep backfilled records separate from outbound syndication state so archived historical posts are not reposted.
