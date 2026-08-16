# Plan - Courts of New Zealand Threads API Credentials

## Phase 1: Contract Research
- [x] Task: Confirm official Threads API fields, scopes, profile IDs, and token
  lifetime requirements from Meta documentation.
- [x] Task: Decide whether Buffer remains a fallback or is removed from the
  launch path.
- [x] Task: Document free-tier or quota implications.

## Phase 2: Secret Schema
- [x] Task: Add Threads secret names to `config/secrets.schema.json`.
- [x] Task: Extend `scripts/validate_secrets.py` for `--target threads`.
- [x] Task: Add unit tests for missing, partial, and valid Threads secret sets.

## Phase 3: Non-Posting Probe
- [x] Task: Implement a Threads credential probe that reads account/profile
  identity only.
- [x] Task: Add GitHub Actions wiring for the probe behind a disabled or manual
  gate.
- [x] Task: Document setup and rotation in `SETUP_GUIDE.md`.

## Completion Evidence
- [x] Meta app `Courts NZ Mirror` has `mirnzcourts` accepted as a Threads
  tester.
- [x] GitHub Actions secrets `THREADS_ACCESS_TOKEN` and `THREADS_USER_ID` are
  configured for `edithatogo/sm-govt-nz`.
- [x] Manual `Validate Threads` workflow run
  `https://github.com/edithatogo/sm-govt-nz/actions/runs/27458588485` passed.
- [x] Live Threads syndication remains disabled in `config.json`; launch is
  still gated by Bluesky backlog completion and adapter launch review.
