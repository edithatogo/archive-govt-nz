# Phase 7 Review - Operational Optimizations

## Status
Phase 7 is complete.

## Completed Tasks
- Added the Pages source-health dashboard for archive source status.
- Added the no-op duplicate monitor for email archive replay.
- Added monthly archive compaction through
  `scripts/build_archive_compaction_manifest.py`,
  `conductor/archive_compaction_manifest.json`, and the
  `Archive Compaction Manifest` workflow.
- Added the Buffer API key rotation reminder workflow for the 12 July 2026
  expiry and confirmed it opened GitHub issue #4.
- Added syndication failure isolation so one missing or failing target does not
  stop other configured targets from posting.

## Review Findings
- No blocking Phase 7 issues found.
- Archive compaction is append-only. It records source/month counts, bytes,
  normalized JSONL content checksums, and raw path/size inventory digests
  without deleting or repacking evidence.
- The Buffer reminder does not read or print the Buffer key. It only tracks the
  known expiry date and writes a GitHub issue when rotation is due.
- Scheduled syndication no longer skips the whole run when Threads credentials
  are unavailable. Missing or failing targets are recorded as unsuccessful
  skipped deliveries while successful targets still record delivery state.
- Source cursor advancement remains conservative. If any active target for a
  selected post is blocked, `conductor/state.json` does not advance, so the
  blocked target can catch up after credentials or platform access are fixed.

## Validation
- `python -m pytest tests/test_archive_compaction_manifest.py tests/test_publish_archives.py -q`
- `ruff check --no-cache scripts/build_archive_compaction_manifest.py tests/test_archive_compaction_manifest.py`
- `python -m pytest tests/test_buffer_key_rotation.py -q`
- `ruff check --no-cache scripts/check_buffer_key_rotation.py tests/test_buffer_key_rotation.py`
- `python scripts/check_buffer_key_rotation.py --expires-on 2026-07-12`
- `python -m pytest tests/test_runner.py -q`
- `ruff check --no-cache src/runner.py tests/test_runner.py`
- `git diff --check` for each staged task set
- GitHub CI and Pages passed for:
  - `c415452` - monthly compaction manifest
  - `750d288` - Buffer key rotation reminder
  - `2a438c6` - target delivery failure isolation
- Manual GitHub workflow runs passed:
  - `Archive Compaction Manifest` run `27491385998`
  - `Buffer Key Rotation Reminder` run `27491477765`

## Residual Risks
- Raw archive compaction uses path/size inventory digests rather than full raw
  file content hashes so monthly runs remain cheap. Raw capture writers are
  append-only, so this is acceptable for operations but not a substitute for a
  full forensic content-hash audit.
- The Buffer expiry date is configured in workflow/script inputs, not detected
  from Buffer's API.
- Earlier phases still have open LinkedIn capture and external dataset
  publication tasks. Phase 7 completion does not launch those external
  dependencies.

## Next Phase Criteria
The next practical work should return to the remaining open tasks:

- Create the dedicated Cloudflare-routed subscription address for Courts of NZ
  judgments of public interest notifications.
- Decide whether Mailgun or scheduled mailbox polling is needed as an email
  ingress fallback after Cloudflare is live.
- Publish normalized JSONL and Parquet shards to Hugging Face Datasets once the
  dataset repository secret is configured.
- Publish a citable Zenodo release snapshot once the Zenodo deposition endpoint
  and token are configured.
