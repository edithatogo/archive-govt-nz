# Specification - Courts of New Zealand Facebook Page archive lane

## Overview

Keep Facebook as an archive-only lane for Courts of New Zealand content.
Public-page snapshots are allowed now. Any future authenticated Meta Facebook
API lane remains deferred until a later business-account decision.

## Functional Requirements

- Describe Facebook as archive-only, not mirroring.
- Archive public Facebook Page snapshots from the official pages.
- Do not assume Threads tokens authorize Facebook access.
- Keep any authenticated API or outbound publishing work deferred.
- Keep the workflow and operator guidance read-only until an archive action is
  explicitly run.

## Non-Goals

- Posting to Facebook.
- Creating or requiring a business account now.
- Changing the broader Meta access strategy beyond archive-only snapshot
  capture.

## Acceptance Criteria

- Facebook guidance documents the archive-only public snapshot path.
- The workflow and readiness docs do not require a business account for the
  current archive lane.
- Tests and reports distinguish archive-only snapshot capture from any future
  authenticated API work.
- Business-account dependent work stays explicitly deferred.
