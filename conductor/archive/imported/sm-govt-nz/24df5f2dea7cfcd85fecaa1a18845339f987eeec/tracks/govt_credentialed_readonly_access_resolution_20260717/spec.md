# Specification: Credentialed Read-Only Access Resolution

## Overview

Resolve the remaining Facebook and LinkedIn archival access gaps, complete Bluesky credential validation, and ensure all credentialed paths remain archive-only. The canonical administrative identity is `edithatogo@gmail.com`.

## Functional Requirements

- Validate the Bluesky identifier and dedicated app password through the existing read-only archive workflow.
- Never use normal account passwords in GitHub Actions or archive adapters.
- Facebook capture may proceed only with an authorised Page ID and Page Access Token.
- LinkedIn capture may proceed only with an approved read-only API token or an authorised export.
- Do not create substitute Pages, claim organisation identities, request write scopes, post, mirror, follow, message, like, or react.
- Record reCAPTCHA, missing Page administration, missing LinkedIn Page association, unavailable products, missing tokens, and missing exports as machine-readable external-access states.
- Keep all captures separated from syndication state and preserve monthly publication guards.

## Non-Functional Requirements

- Credentials must be stored only as masked local user variables or GitHub secrets; normal passwords must be removed and rotated after exposure.
- Workflows must fail closed when required read-only credentials or identifiers are absent.
- Browser setup may be used interactively, but must not extract cookies, local storage, password stores, or private API calls.
- All changes must remain Python 3.14 compatible and use zero-cost options only.

## Acceptance Criteria

- Bluesky workflow succeeds with a dedicated app password and no direct-message access.
- Facebook either archives through a verified Page-level read token or has evidence-backed `terminal_external_access` status.
- LinkedIn either archives through an approved read-only token/authorised export or has evidence-backed `terminal_external_access` status.
- CI/tests assert no posting or mirroring path is enabled by these credentials.
- Reports identify the exact external prerequisite for every unresolved source cohort.

## Out of Scope

- Creating or claiming government Pages or LinkedIn organisation Pages.
- CAPTCHA solving or access-control bypass.
- Paid APIs, paid automation, proxy services, or credential harvesting.
- Personal-profile mirroring or any outbound platform activity.
