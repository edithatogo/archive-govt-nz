# Plan - Courts of New Zealand Bluesky Profile Archive

## Phase 1: Evidence Capture
- [x] Task: Fetch source Bluesky profile metadata and asset URLs.
- [x] Task: Fetch mirror Bluesky profile metadata and asset URLs.
- [x] Task: Save dated JSON snapshots under `profile_archive/courts-nz/`.
- [x] Task: Download avatar and banner assets where public URLs are available.

## Phase 2: Identity Review
- [x] Task: Compare source and mirror profiles against the mirror identity
  contract.
- [x] Task: Record any profile-field gaps as follow-up tasks without changing
  account settings automatically.
- [x] Task: Commit profile evidence after review.

## Phase 3: Track Closeout
- [x] Task: Update the parent Bluesky mirror track once evidence is complete.
- [x] Task: Run tests or lint only if docs/scripts changed.
