# Phase 5 Review - Judgments Email Subscription Ingress

## Status
Phase 5 is complete.

## Completed Tasks
- Selected Cloudflare Email Routing Worker as the default email ingress bridge
  because it has a free routing path and enough free Worker request capacity
  for low-volume notification capture.
- Retained Mailgun inbound parse as a deferred fallback only if Cloudflare
  parsing/routing is insufficient and a trial or paid plan is acceptable.
- Retained scheduled mailbox polling through Gmail or IMAP as the final
  fallback if webhook-style inbound delivery is unavailable.
- Created a dedicated subscription address for Courts of NZ judgments of public
  interest notifications. The active automated address is
  `em4mkapmjakoh5o@upload.pipedream.net` (Pipedream Email trigger), deployed,
  verified, and subscribed to all four Courts of NZ judgment lists on
  2026-06-17. The planned permanent Cloudflare-routed address
  `courts-nz-judgments@archive.edithatogo.com` remains
  `pending_external_setup` because `edithatogo.com` is not registered; domain
  registration is cost-bearing and requires explicit approval per the
  Cloudflare cost guardrail.
- Stored raw email payloads under `historical_archive_raw/email/<yyyy-mm>/`.
- Normalized email subject/body/link records into the shared archive schema
  under `historical_archive_normalized/email/<yyyy-mm>.jsonl`.
- Triggered GitHub Actions with `repository_dispatch` after email receipt.
- Added a deployable Cloudflare Email Routing Worker template and tests for
  dispatching received messages into GitHub.
- Added a manual GitHub Actions deployment workflow for the Cloudflare Email
  Routing Worker.

## Review Findings
- The acceptance criterion is satisfied: email subscription messages can enter
  the repository through a documented bridge (Pipedream, Cloudflare Worker, or
  manual `Archive Email` dispatch) and are archived as raw and normalized
  records. Four verification records exist in
  `historical_archive_raw/email/2026-06/` and
  `historical_archive_normalized/email/2026-06.jsonl`.
- The active automated subscription address
  (`em4mkapmjakoh5o@upload.pipedream.net`) is dedicated to Courts of NZ
  judgments capture, deployed in Pipedream, and verified with two test dispatch
  runs (`27624019635`, `27624118414`).
- Subscription confirmation was verified pending on 2026-06-21. The GitHub
  Actions `Archive Email` workflow runs were reviewed between 2026-06-17 and
  2026-06-21; no new `repository_dispatch` runs occurred after the subscription
  request. The last run was `27624118414` on 2026-06-16 (a deployed test).
  Courts of NZ may require a visible browser session to complete list
  confirmation, or confirmation emails may not have been sent yet.
- The Cloudflare dedicated address remains deferred. `edithatogo.com` returned
  `NXDOMAIN` on 2026-06-15. The Cloudflare account has no payment method, no
  active subscriptions, and Workers on the `Free $0` plan. Domain registration
  must not proceed without explicit approval.
- The `Multi-Source Blocker Status` check reports email ingress as `complete`
  because a capture route is available (Pipedream automated route plus manual
  `Archive Email` dispatch). The dedicated Cloudflare route is `deferred`.
- Email ingress remains archive-only. No email record advances outbound
  syndication state or creates posts on any mirror account.

## Validation
- `python -m pytest tests/test_email_ingress_config.py -q`
- `python -m pytest tests/test_archive_email_payload.py -q`
- `python -m pytest tests/test_cloudflare_email_worker.py -q`
- `python -m pytest tests/test_configure_cloudflare_email_routing.py -q`
- `python scripts/check_multisource_blockers.py`
- `ruff check --no-cache src tests scripts`
- JSON validation for `config/courts_nz_email_ingress.json`

## Residual Risks
- Courts of NZ subscription confirmation is pending. If confirmation emails do
  not arrive, the subscription should be repeated in a visible browser session
  to complete any site-side validation or confirmation step.
- The Pipedream route depends on Pipedream free-tier credit limits. Keep
  billing disabled, review usage after the first month, and switch to manual
  dispatch if the account approaches the free-tier limit.
- The Cloudflare permanent address requires domain registration, which is
  cost-bearing and blocked by the zero-spend guardrail until explicitly
  approved.

## Next Phase Criteria
All Phase 5 tasks are complete. The remaining open items in this track are:
- Phase 3 and Phase 4 LinkedIn capture tasks, which are paused per user
  decision on 15 June 2026 until Instagram, Facebook, and the multi-source
  archive pipeline are stable.
- The Deferred Tracks section, which requires separate conductor tracks per
  future outbound platform account and is out of scope for this track.
