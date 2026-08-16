# Specification - Courts of New Zealand Bluesky Profile Archive

## Overview
Close the remaining Bluesky account-identity evidence gap for
`mirnzcourts.bsky.social`. This track is limited to profile metadata,
identity assets, and repository evidence. It must not post content.

## Requirements
1. Verify the mirror profile display name, handle, bio, avatar, banner, and
   source attribution match the mirror identity contract.
2. Archive current source and mirror profile snapshots under
   `profile_archive/courts-nz/<date>/`.
3. Store profile evidence as reviewable JSON and image files without secrets or
   personal-account identifiers.
4. Update conductor product guidelines if the approved handle/display-name
   pattern changes.

## Acceptance Criteria
- A dated profile archive contains source Bluesky profile metadata, mirror
  Bluesky profile metadata, avatar, and banner evidence.
- The mirror bio explicitly states the account is unofficial and links or names
  `courtsofnz.bsky.social`.
- No live posts are made as part of this track.
