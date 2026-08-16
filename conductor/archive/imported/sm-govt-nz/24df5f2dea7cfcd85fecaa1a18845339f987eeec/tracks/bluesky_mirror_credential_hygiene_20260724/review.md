# Review Report: Bluesky Mirror Credential Hygiene

## Summary

All local credential controls are complete. Operator-supervised primary-password
rotation, GitHub Environment app-password replacement, and superseded
app-password revocation remain unverified external actions.

## Verification Checks

- [x] **Plan Compliance**: Partial - all automatable tasks are complete.
- [x] **Style Compliance**: Pass.
- [x] **New Tests**: Yes.
- [x] **Test Coverage**: Yes for local app-password enforcement and nonsecret
  reporting.
- [x] **Test Results**: Passed - 57 targeted tests and Ruff passed.

## Hosted Evidence

Run `30238209314` passed on 2026-07-27:

- the ACC mirror selected environment
  `bluesky-mirror-accident-compensation-corporation`;
- app-password mode and the expected handle were enforced;
- credential authentication and DID resolution passed; and
- dry-run publication completed without posting.

## Remaining External Gate

GitHub's nonsecret Environment metadata reports `BLUESKY_APP_PASSWORD` was last
updated at `2026-07-22T11:18:54Z`. This predates the claimed 2026-07-27
replacement and cannot verify rotation or revocation. Completion requires:

- operator-controlled primary-password rotation;
- replacement of the isolated Environment app password;
- revocation of the superseded app password; and
- a non-posting preflight using the replacement credential.
