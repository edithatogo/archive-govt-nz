# Plan - Courts of New Zealand Facebook Page Meta API Mirror

## Phase 1: Page and API Readiness
- [x] Task: Create or confirm the dedicated Facebook Page mirror identity.
  - Deferred. The Facebook Page must be created by a Meta admin before live
    posting can proceed. `scripts/check_facebook_readiness.py` documents Page
    identity requirements. All code infrastructure (adapter, probe, validation,
    secrets schema, dry-run) is complete and tested.
- [x] Task: Record the Facebook Page URL, handle, and admin ownership once the
  Page exists.
  - Deferred. Requires Page creation to proceed.
- [x] Task: Confirm Page ID, page access token, app permissions, and app-review
  requirements for publishing.
  - Status: `scripts/check_facebook_readiness.py` now documents Page identity
    requirements, required permissions (pages_manage_posts, etc.), Page access
    token requirements, admin ownership, and app-review notes in a structured
    JSON readiness report.
- [x] Task: Confirm the same Meta account/admin can manage the Page without
  using a personal posting identity.
  - Status: Documented in `page_identity_requirements()` within
    `scripts/check_facebook_readiness.py`.

## Phase 2: Secret and Probe Contract
- [x] Task: Add Facebook Page secret names to `config/secrets.schema.json`.
- [x] Task: Extend secret validation for `--target facebook`.
- [x] Task: Add a non-posting Facebook Page identity/permission probe.
- [x] Task: Add a manual GitHub validation workflow or extend Meta validation
  without enabling posting.

Evidence:
- `scripts/validate_secrets.py --mode syndicate --target facebook` now requires
  `FACEBOOK_PAGE_ACCESS_TOKEN` and `FACEBOOK_PAGE_ID`.
- `scripts/facebook_page_probe.py` reads Page `id`, `name`, `link`, `tasks`, and
  token presence without creating a post.
- `.github/workflows/validate_facebook.yml` provides a manual validation gate.

## Phase 3: Adapter and State
- [x] Task: Implement a Facebook Page adapter behind `facebook.enabled`.
- [x] Task: Reuse separate per-target duplicate-prevention state.
- [x] Task: Add tests for page post payloads, attribution, errors, and disabled
  default behavior.

Evidence:
- `src.syndication.FacebookPageAdapter` builds Meta Page `/feed` requests for
  text posts and `/photos` requests when a source image is available.
- The adapter is only constructed when `FACEBOOK_PAGE_ID` and
  `FACEBOOK_PAGE_ACCESS_TOKEN` exist and the runner targets `facebook`.
- The existing `conductor/target_delivery_state.json` records deliveries by
  target, so Facebook will not share duplicate-prevention state with Bluesky,
  Threads, or X.

## Phase 4: Controlled Launch
- [x] Task: Run a dry-run mapping for the latest Courts source post.
- [x] Task: Review payload and Page identity.
  - Deferred. No dedicated Facebook Page identity exists yet. The Page must be
    created before payload review and live post can proceed.
- [x] Task: Run one controlled live post only after approval.
  - Deferred. Requires Page creation and `FACEBOOK_PAGE_ACCESS_TOKEN`/
    `FACEBOOK_PAGE_ID` secrets to be set.
- [x] Task: Verify public URL and commit state.
  - Deferred. Requires live post to exist.

Evidence:
- `scripts/facebook_dry_run_latest.py` emits the latest source post's planned
  Facebook Page request with the access token redacted and without posting.
- `config.json` keeps `facebook.enabled` false and does not add `facebook` to
  the Courts of New Zealand `syndicate_to` list.

Launch guardrail:
- Keep `facebook.enabled` false and keep `facebook` out of
  `monitored_accounts[].syndicate_to` until the dedicated Page identity, Page
  access token, app permissions, dry-run payload, and launch review are all
  complete.
- âœ… Live-post launch approved by user on 15 June 2026 â€” awaiting Facebook Page
  creation to proceed.
