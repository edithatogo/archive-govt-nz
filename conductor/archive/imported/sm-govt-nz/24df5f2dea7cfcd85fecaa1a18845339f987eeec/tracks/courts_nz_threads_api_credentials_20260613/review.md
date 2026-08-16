# Review - Courts of New Zealand Threads API Credentials

**Track ID:** `courts_nz_threads_api_credentials_20260613`
**Review Date:** 2026-06-25
**Reviewer:** Conductor Track Reviewer Agent

## Summary
All 9 tasks across 3 phases are fully implemented and verified. Threads API credential contracts, secret schema, and non-posting validation are complete. Live posting remains gated by adapter launch review. No fixes required.

## Plan Compliance
All 9 tasks across 3 phases are marked `[x]`:

| Phase | Task | Status | Evidence |
|-------|------|--------|----------|
| Phase 1: Contract Research | Confirm Threads API fields, scopes, profile IDs, token lifetime | âœ… | Meta documentation referenced |
| Phase 1: Contract Research | Decide Buffer fallback status | âœ… | Buffer removed from launch path |
| Phase 1: Contract Research | Document free-tier/quota implications | âœ… | Documented |
| Phase 2: Secret Schema | Add Threads secret names to `config/secrets.schema.json` | âœ… | `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID` |
| Phase 2: Secret Schema | Extend `scripts/validate_secrets.py` for `--target threads` | âœ… | Threads validation implemented |
| Phase 2: Secret Schema | Unit tests for missing, partial, valid Threads secret sets | âœ… | `test_validate_secrets.py` |
| Phase 3: Non-Posting Probe | Implement Threads credential probe (read-only) | âœ… | `scripts/threads_api_probe.py` |
| Phase 3: Non-Posting Probe | GitHub Actions wiring for probe | âœ… | `.github/workflows/validate_threads.yml` |
| Phase 3: Non-Posting Probe | Document credential rotation/revocation | âœ… | Setup docs updated |

## Completion Evidence
- âœ… Meta app `Courts NZ Mirror` has `mirnzcourts` accepted as Threads tester
- âœ… GitHub Actions secrets `THREADS_ACCESS_TOKEN` and `THREADS_USER_ID` configured for `edithatogo/sm-govt-nz`
- âœ… Manual `Validate Threads` workflow run `27458588485` passed
- âœ… Live Threads syndication remains disabled in `config.json` (gated by adapter launch review)

## Spec Compliance
- âœ… Prefer official Threads API route for `https://www.threads.com/@mirnzcourts`
- âœ… Documented Meta app, Threads user/profile ID, access token scope, token refresh/expiry
- âœ… GitHub secret names and validation logic without storing tokens in Git
- âœ… Validation does not create, publish, or delete Threads posts
- âœ… Threads disabled in `config.json` until adapter launch review passes

## Acceptance Criteria
- âœ… `config/secrets.schema.json` includes Threads secret contract
- âœ… `scripts/validate_secrets.py --mode syndicate --target threads` verifies environment shape
- âœ… Probe command (`scripts/threads_api_probe.py`) verifies credentials without publishing
- âœ… Docs explain credential rotation/revocation

## Code Quality
- Ruff: âœ… All checks passed (`ruff check --no-cache src tests scripts`)
- pytest: âœ… Secret validation tests pass

## Archive Decision
**ARCHIVED** â€” All deliverables complete and verified. Threads credentials ready for adapter launch.