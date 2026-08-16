# Plan - Courts of New Zealand Mirror

## Phase 1: Narrow Production Scope
- [x] Task: Restrict `config.json` to Courts of New Zealand as the only monitored account.
- [x] Task: Disable non-X syndication targets until those platform credentials and policies are ready.
- [x] Task: Seed `conductor/state.json` for `courtsofnz.bsky.social` to prevent a backlog repost.

## Phase 2: Mirror Identity
- [x] Task: Adopt `Mirror: Courts of New Zealand` as the systematic display-name pattern.
- [x] Task: Confirm and apply the live X display name and handle change.
- [x] Task: Archive the current source Bluesky profile and mirror X profile in the GitHub repository.
- [x] Task: Apply minimally modified mirror profile text that identifies the account as unofficial and links back to the Bluesky source.

## Phase 3: Controlled Launch
- [x] Task: Wait for CI to pass on the Courts mirror PR after profile archive and roadmap updates.
- [x] Task: Merge the Courts mirror PR into `master`.
- [x] Task: Confirm required GitHub X secret names exist for `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, and `X_ACCESS_TOKEN_SECRET`.
- [x] Task: Run an Actions-level X-only secret validation before any live syndication run.
- [x] Task: Run a controlled single-account, X-only live synchronization test.
- [x] Task: Verify the resulting X post on `@MirNZCourts` preserves source attribution and does not duplicate historical content.
  - Verified seed post: https://x.com/MirNZCourts/status/2065081275925557496
  - Note: the automated Tweepy path reached X but returned `401 Unauthorized`; the visible seed post was submitted through the logged-in X session after switching Chrome to `@MirNZCourts`.
- [x] Task: Fix unattended X posting authentication before enabling the scheduled workflow.
  - OAuth 1.0 API key/secret and access token/secret were rotated for `@MirNZCourts`.
  - Local identity checks now authenticate as `@MirNZCourts`.
  - API write probe now reaches the posting endpoint but fails with `402 Payment Required`: the enrolled X developer account has no credits.
  - Zernio is archived for this MVP and is no longer an active fallback path.
- [x] Task: Add usable X developer API credits or billing for account `2064702174668767232`.
  - After credits are available, run `python scripts/x_api_probe.py --write-probe` locally or dispatch `Validate Syndication Secrets` with `write_probe=true`.
  - Current Bluesky archive has 47 posts from 2026-03-23 to 2026-06-11, averaging 0.58 posts/day.
  - At current X API rates, URL-attributed mirroring would have cost about $2.20-$2.60/month for recent Courts of NZ volume.
- [x] Task: Re-enable the scheduled `Syndicate` workflow after the controlled test and X credits check pass.
  - Buffer-backed posting validated and a controlled live run posted the two new Courts of New Zealand Bluesky posts to `@MirNZCourts`.
  - Direct X API credits remain unnecessary for the MVP while Buffer posting is healthy.
- [x] Task: Monitor the first scheduled run and confirm `conductor/state.json` advances without duplicate posts.
- [x] Task: Pilot Buffer CLI as the preferred no-direct-X-credits posting path.
  - Installed `@bufferapp/cli`, connected `@MirNZCourts` in Buffer, set `BUFFER_API_KEY` and `BUFFER_X_CHANNEL_ID`, dispatched `Validate Buffer Syndication`, and completed a controlled Buffer-backed live run.

## Phase 4: Later Historical Archive
- [x] Task: Archive historical `@courtsofnz` Twitter/X posts into the GitHub repository without triggering syndication.
  - Moved to dedicated track `courts_nz_multisource_archive_20260612` so X, Bluesky, LinkedIn, RSS, email ingress, and Hugging Face publishing are handled together.
- [x] Task: Archive historical and ongoing `courtsofnz.bsky.social` Bluesky posts into the GitHub repository.
  - Historical Bluesky seed exists; ongoing multi-source capture is tracked in `courts_nz_multisource_archive_20260612`.
- [x] Task: Connect historical X records and current Bluesky records into one Courts of New Zealand timeline.
  - Moved to the multi-source archive track with canonical dedupe across sources.
- [x] Task: Package the GitHub archive as a Courts of New Zealand corpus/dataset for later Zenodo deposition and Hugging Face Dataset publication.
  - Moved to the multi-source archive track with Hugging Face dataset publication tasks.
