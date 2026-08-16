# Plan - Courts of New Zealand Threads Adapter Launch

## Phase 1: Adapter Contract
- [x] Task: Define Threads payload builder for text-only and media posts.
- [x] Task: Add a Threads adapter class with injected HTTP client for tests.
- [x] Task: Keep the adapter unreachable unless `threads.enabled` is true.

## Phase 2: State and Tests
- [x] Task: Add Threads duplicate-prevention state.
- [x] Task: Add unit tests for formatting, attribution, state, and API errors.
- [x] Task: Add guardrail tests proving archive replay is not used by default.

## Phase 3: Dry Run
- [x] Task: Add a dry-run command for the latest source post.
- [x] Task: Review generated payload against Threads limits and identity rules.
- [x] Task: Confirm no LinkedIn or personal identity data enters the payload.

## Phase 4: Controlled Live Launch
- [x] Task: Enable Threads for a one-post manual workflow dispatch.
- [x] Task: Verify public Threads delivery state and commit state. Threads
  duplicate-prevention state now records one delivered Courts of New Zealand
  source post for `courtsofnz.bsky.social`.
- [x] Task: Disable or retain scheduling according to launch review.

## Launch Evidence
- [x] `config.json` now includes `threads` in the Courts of New Zealand
  `syndicate_to` list and sets `threads.enabled` to true.
- [x] `.github/workflows/syndicate.yml` validates and probes
  `THREADS_ACCESS_TOKEN` and `THREADS_USER_ID` before the syndicator runs.
- [x] Scheduled runs now skip live new-post syndication if Threads
  validation/probing fails, while allowing archive/backlog tasks to continue.
  This avoids advancing source state without a healthy Threads path. Manual
  live dispatches still fail hard.
- [x] `conductor/target_delivery_state.json` is committed as the separate
  per-target duplicate-prevention state file.
- [x] Manual `Syndicate` workflow run
  `https://github.com/edithatogo/sm-govt-nz/actions/runs/27459100624` passed
  with Threads enabled; it fetched zero new source posts and therefore did not
  publish a Threads post.
- [x] Manual `Syndicate` workflow run
  `https://github.com/edithatogo/sm-govt-nz/actions/runs/27500249516` passed
  with Threads credentials validating and probing successfully.
- [x] `conductor/target_delivery_state.json` records Threads delivery for source
  post `3mo2b6w4u522m`.
- [x] `python scripts/threads_dry_run_latest.py` emits the latest source post's
  intended Threads create/publish requests with access tokens redacted and
  historical replay disabled.
