# Specification - Courts of New Zealand Threads API Credentials

## Overview
Prepare the Threads mirror for API posting without enabling live posts. This
track covers credential contracts, secret schema, and non-posting validation
only.

## Requirements
1. Prefer the official Threads API route for `https://www.threads.com/@mirnzcourts`.
2. Document required Meta app, Threads user/profile ID, access token scope, and
   token refresh/expiry behavior.
3. Add GitHub secret names and validation logic without storing tokens in Git.
4. Validation must not create, publish, or delete Threads posts.
5. Keep Threads disabled in `config.json` until adapter launch review passes.

## Acceptance Criteria
- `config/secrets.schema.json` includes the selected Threads secret contract.
- `scripts/validate_secrets.py --mode syndicate --target threads` verifies the
  required environment shape.
- A probe command can verify credentials without publishing content.
- Docs explain how to rotate/revoke the Threads credentials.

## Validation
- 2026-06-13: GitHub Actions `Validate Threads` run
  `27458588485` passed using GitHub secrets for `@mirnzcourts`; the probe read
  profile identity only and did not publish content.
