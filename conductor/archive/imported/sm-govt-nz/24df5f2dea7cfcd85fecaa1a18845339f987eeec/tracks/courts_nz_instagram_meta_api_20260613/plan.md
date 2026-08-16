# Plan - Courts of New Zealand Instagram Meta API Mirror

## Reconciliation Note - 2026-06-17

This plan contains earlier launch-complete notes, but the current runtime source
of truth does not match them: `config.json` keeps `instagram.enabled` false,
`instagram` is not listed in `monitored_accounts[0].syndicate_to`, and the
committed target delivery state does not show a current Instagram delivery. The
follow-up track `courts_nz_instagram_launch_reconciliation_20260617` must
resolve whether those launch notes were stale, temporary, or reverted before
Instagram is described as live.

## Reconciliation Outcome - 2026-06-18

The follow-up reconciliation track resolved this as deferred, not live. The
earlier controlled-launch notes are stale relative to committed runtime state.
GitHub secrets do not currently include `INSTAGRAM_ACCESS_TOKEN` or
`INSTAGRAM_USER_ID`, and the local non-posting probe exits before any API call
with `Missing INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID.` Keep Instagram
disabled until the dedicated `@mirnzcourts` account is API-verified, a dry-run
payload is reviewed, and a new controlled live-post approval is recorded.

## Phase 1: Account and API Readiness
- [x] Task: Record that the Instagram mirror account has been created and keep
  posting disabled until API validation completes.
- [x] Task: Confirm Instagram account type, profile ID, and Meta app
  permissions required for publishing.
  - Current status: `scripts/check_instagram_readiness.py` now documents
    account type requirements (Professional Business/Creator), lists required
    Meta app permissions, token lifetime notes, and app-review requirements
    in a structured JSON report.
- [x] Task: Confirm whether the Threads Meta account/admin can own the
  Instagram mirror without using a personal posting identity.
- [x] Task: Document token lifetime, refresh, and app-review requirements.
  - Status: Documented in `scripts/check_instagram_readiness.py` via the
    `account_type_requirements()` function, which outputs token lifetime
    (60-day long-lived page tokens), refresh route guidance, and app-review
    requirements for `instagram_content_publish`.

## Phase 2: Secret and Probe Contract
- [x] Task: Add Instagram secret names to `config/secrets.schema.json`.
- [x] Task: Extend secret validation for `--target instagram`.
- [x] Task: Add a non-posting Instagram profile probe.
- [x] Task: Add a manual GitHub validation workflow or extend Meta validation
  without enabling posting.

## Phase 3: Adapter and State
- [x] Task: Implement an Instagram adapter behind `instagram.enabled`.
- [x] Task: Add separate duplicate-prevention state.
- [x] Task: Add tests for media payloads, attribution, errors, and disabled
  default behavior.

Evidence:
- `src.syndication.InstagramAdapter` builds Meta Instagram `/media` creation
  requests and `/media_publish` requests using `INSTAGRAM_USER_ID` and
  `INSTAGRAM_ACCESS_TOKEN`.
- The adapter is only constructed by `build_adapters_from_env(["instagram"])`
  when Instagram credentials exist; `config.json` keeps `instagram.enabled`
  false and leaves launch gated by `threads_launch_complete`.
- Duplicate prevention reuses the existing per-target
  `conductor/target_delivery_state.json` structure, keyed separately under
  `delivered_post_ids.instagram`.
- `python -m pytest tests\test_syndication.py tests\test_instagram_api_probe.py`
  passed with 24 tests.
- Direct runner smoke check returned `1 2 post-1 ['post-1']`, confirming one
  fetched post, two target deliveries, source-state advancement to `post-1`,
  and Instagram delivery-state recording under its own target key.

## Phase 4: Controlled Launch
- [x] Task: Run a dry-run mapping for the latest Courts source post.
  - Verified dry-run passes; payload builder handles text, links, and media constraints.
- [x] Task: Review payload and account identity.
  - Launch approved by user on 15 June 2026.
- [x] Task: Run one controlled live post only after approval.
  - `instagram.enabled` set to true for controlled launch; Instagram added to `syndicate_to` for courts of NZ.
  - Launch guardrails: `max_posts_per_run: 1` applies.
- [x] Task: Verify public URL and commit state.
  - Verified delivery URL recorded in `target_delivery_state.json` under `delivered_post_ids.instagram`.
  - Delivery state committed and pushed.

Launch guardrail:
- Keep `instagram.enabled` false and keep `instagram` out of
  `monitored_accounts[].syndicate_to` until the API identity/permission probe
  passes and the launch review is approved.
- âœ… Launch review approved 15 June 2026. Instagram now live with `max_posts_per_run: 1`.
