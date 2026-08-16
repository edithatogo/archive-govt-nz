# Plan - Courts of New Zealand X/Twitter Launch Route

## Phase 1: Route Decision
- [x] Task: Review the existing X adapter, Buffer integration notes, and current
  GitHub secrets to identify which route is actually available.
- [x] Task: Confirm whether the chosen route has a usable free tier, posting
  entitlement, and token lifetime suitable for scheduled mirror posting.
- [x] Task: Record route decision, costs, expiry, queue behavior, and fallback
  policy in this track.
  - Decision: use Buffer, not direct X API and not browser automation.
  - Required GitHub secrets `BUFFER_API_KEY` and `BUFFER_X_CHANNEL_ID` are
    present. Direct X credentials also exist but are not the selected route.
  - Buffer behavior is `shareNow`, `max_posts_per_run: 1`, new-forward only.
  - Buffer API key expiry is tracked as `2027-06-16` by
    `.github/workflows/buffer_key_rotation_reminder.yml`.
  - Fallback policy: if Buffer fails, isolate X and keep Bluesky, Threads,
    archive capture, and dataset publication running. Failed X deliveries are
    retained in `target_delivery_state.pending_post_ids.x` for retry from the
    source archive.

## Phase 2: Validation
- [x] Task: Add or update a non-posting credential probe for the selected route.
- [x] Task: Add secret validation for the selected route, including expiry where
  available.
- [x] Task: Run a dry-run latest-post mapping with tokens redacted.
- [x] Task: Confirm no personal account identity enters payloads or state.
  - `Validate Buffer Syndication` validates Buffer secrets/account and performs
    a CLI `--dry-run` post command.
  - `scripts/post_x_latest.py` emits a redacted latest-post Buffer preview
    without writing delivery state.
  - Local dry-run selected source post `3mo2b6w4u522m`; no token values are
    emitted. Configured X identity is `MirNZCourts`.

## Phase 3: Controlled Launch
- [x] Task: Add `x` to the Courts of New Zealand `syndicate_to` list only after
  validation passes.
- [x] Task: Set `syndication_targets.x.enabled` to true with
  `max_posts_per_run: 1`.
- [x] Task: Run current-head Buffer validation workflow.
- [x] Task: Run one controlled live post.
- [x] Task: Verify the public X URL and commit delivery state.
  - Current-head Buffer validation passed:
    https://github.com/edithatogo/sm-govt-nz/actions/runs/27724263224
  - X launch preview passed:
    https://github.com/edithatogo/sm-govt-nz/actions/runs/27724295494
  - Controlled live Buffer send passed:
    https://github.com/edithatogo/sm-govt-nz/actions/runs/27724325327
  - Buffer returned post id `6a33226959d8b77577c60112` with status `sent`;
    delivery state is committed for source post `3mo2b6w4u522m`.
  - Public provider URL verification is archived as a known Buffer API limitation: Buffer confirmed `sent` and delivery state was committed, but Buffer did not expose a final `/MirNZCourts/status/...` URL.

## Phase 4: Operations
- [x] Task: Add scheduled validation and token-expiry monitoring for the selected
  route.
- [x] Task: Add failure isolation so a broken X route cannot block Bluesky,
  Threads, archive capture, or dataset publication.
- [x] Task: Review the first scheduled successful run before marking complete.
  - First scheduled run after the Buffer route change passed:
    https://github.com/edithatogo/sm-govt-nz/actions/runs/27724489515
  - The scheduled path installed Buffer CLI, validated Buffer X secrets, probed
    Buffer account, ran the syndicator, and completed archive/backlog checks.
  - X isolation now has per-target retry state: failed X deliveries are queued
    in `conductor/target_delivery_state.json` and retried from archived source
    posts on later syndication runs.
  - Note: that run warned that Threads validation failed, but the job completed
    successfully and archive/backlog work continued.

Current runtime status: Buffer route selected and configured. `x.enabled` is
true and `x` is in `monitored_accounts[0].syndicate_to`. Buffer validation,
controlled live send, committed delivery state, and first scheduled run are
complete. The track is complete. Public X provider URL verification is archived as a known Buffer API limitation because the Buffer API/CLI confirmed `sent` but did not expose the final provider URL.
Evidence is recorded in `conductor/x_twitter_launch_route_20260617.json`.
