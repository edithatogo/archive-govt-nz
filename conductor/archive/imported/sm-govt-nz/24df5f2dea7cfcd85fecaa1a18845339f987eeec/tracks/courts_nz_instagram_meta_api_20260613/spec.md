# Specification - Courts of New Zealand Instagram archive lane

## Overview

Keep Instagram as an archive-only lane for Courts of New Zealand content.
Public-profile snapshots are allowed now. Any future authenticated Meta
Instagram API lane remains deferred until a later business-account decision.

## Functional Requirements

- Describe Instagram as archive-only, not mirroring.
- Archive public-profile snapshots from the official Instagram pages.
- Do not assume Threads tokens authorize Instagram access.
- Keep any authenticated API or outbound publishing work deferred.
- Keep the workflow and operator guidance read-only until an archive action is
  explicitly run.

## Non-Goals

- Posting to Instagram.
- Creating or requiring a business account now.
- Changing the broader Meta access strategy beyond archive-only snapshot
  capture.

## Acceptance Criteria

- Instagram guidance documents the archive-only public snapshot path.
- The workflow and readiness docs do not require a business account for the
  current archive lane.
- Tests and reports distinguish archive-only snapshot capture from any future
  authenticated API work.
- Business-account dependent work stays explicitly deferred.
