# Plan - Courts of New Zealand Instagram Launch Reconciliation

## Phase 1: Runtime Audit
- [x] Task: Compare `config.json`, `conductor/target_delivery_state.json`, recent
  workflow runs, and Instagram track notes.
- [x] Task: Determine whether the earlier launch notes reflected a temporary
  branch/run, an uncommitted reversal, or stale documentation.
- [x] Task: Update the older Instagram track with a reconciliation note.
  - Outcome: earlier launch-complete notes are treated as stale relative to
    committed runtime truth. `config.json` keeps Instagram disabled,
    `instagram` is not in `syndicate_to`, no Instagram delivery exists in
    `conductor/target_delivery_state.json`, and no recent `Validate Instagram`
    workflow run exists.

## Phase 2: Credential and Identity Check
- [x] Task: Run `validate_instagram` or the local Instagram probe without
  posting.
- [x] Task: Confirm the profile URL and account handle are the dedicated Courts
  mirror account.
- [x] Task: Confirm no personal Instagram identity is used for posting.
  - Probe result: blocked before any API request because GitHub and local
    environment lack `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_USER_ID`.
  - Configured identity remains the dedicated mirror handle `mirnzcourts` at
    `https://www.instagram.com/mirnzcourts/`, but it is not API-verified.
  - No personal Instagram identity is configured for repo-side posting.

## Phase 3: Relaunch or Defer
- [x] Task: If credentials and identity are valid, run a dry-run latest-post
  payload review.
- [x] Task: If approved, enable Instagram with `max_posts_per_run: 1`, add it to
  `syndicate_to`, and run one controlled live post.
- [x] Task: If blocked, leave Instagram disabled and record the precise blocker.
  - Deferred. The dry-run/live-post lane is blocked until Instagram Graph API
    credentials are added and the non-posting probe confirms `@mirnzcourts`.
  - `config.json` is intentionally unchanged: Instagram remains disabled and
    excluded from `syndicate_to`.

## Phase 4: Closeout
- [x] Task: Verify public delivery URL or defer status.
- [x] Task: Commit config/state/track changes.
- [x] Task: Update `conductor/tracks.md` and platform status review.

Current runtime status: deferred. `instagram.enabled` is false and `instagram`
is not in `monitored_accounts[0].syndicate_to`, so Instagram is not live. The
closeout evidence is recorded in
`conductor/instagram_launch_reconciliation_20260617.json`.
