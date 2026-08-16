# Plan - Courts of New Zealand Bluesky Mirror Account

## Phase 1: Account Onboarding
- [x] Task: Create the dedicated Bluesky mirror account using
  `edithatogo@gmail.com` for administration where practical.
- [x] Task: Configure display name, handle, bio, avatar, banner, and source link
  using the mirror identity contract.
- [x] Task: Archive the source and mirror profile snapshots in the repository.

## Phase 2: API and Secrets
- [x] Task: Identify the Bluesky posting library/API path and document token
  requirements.
- [x] Task: Add secret schema entries for the mirror account credentials.
- [x] Task: Add a read/write credential validation command that cannot post
  content.

## Phase 3: Posting Adapter
- [x] Task: Implement a Bluesky mirror target adapter behind an explicit config
  flag.
- [x] Task: Add duplicate-prevention state that is separate from archive state.
- [x] Task: Add tests for attribution, character limits, and no-backlog posting.
- [x] Task: Add historical corpus sync dry-run mode that maps archived records
  to mirror posts without publishing by default.
- [x] Task: Add an explicit bounded backlog posting mode for historical
  backfill.

## Phase 4: Controlled Launch
- [x] Task: Run dry-run mapping for the latest Courts of New Zealand source
  post.
- [x] Task: Review the generated payload before any live post.
- [x] Task: Run one controlled live post only after review approval.
- [x] Task: Verify the live URL and commit updated state.

## Phase 5: Historical Corpus Sync
- [x] Task: Add archive mirror coverage reporting for both the current Bluesky
  archive and the recovered historical X archive.
- [x] Task: Add a bounded X archive replay batch to the Bluesky mirror pipeline.
- [x] Task: Split remaining Bluesky work into granular conductor tracks for
  profile evidence, archive replay completion, and launch operations.
- [x] Task: Generate a complete historical sync plan from the normalized Courts
  archive.
- [x] Task: Review ordering, attribution, source links, and platform limits.
- [x] Task: Publish in bounded batches only after explicit approval.
- [x] Task: Record every posted historical mirror URL in the corpus manifest.
