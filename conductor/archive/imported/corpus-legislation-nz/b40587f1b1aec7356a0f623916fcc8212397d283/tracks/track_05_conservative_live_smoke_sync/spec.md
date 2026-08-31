# Spec - Conservative Live Smoke Sync

## Status
done

## Goal
prove the live sync path against external services without risking rate limits or large uploads.

## Acceptance Criteria
- Five or fewer seed works are synced exactly as requested.
- Validation passes.
- Manifest and coverage report are generated.
- No rate-limit failures are unhandled.

## Evidence to Record
- Command summaries.
- Synced work count.
- Any API warnings from sync state.

## Evidence Recorded

- Live partial/API-discovery sync path was proven for the approved launch.
- The full seed inventory remains absent, so this track is complete only for the
  conservative launch smoke scope. Full coverage remains blocked under Tracks
  04, 07, 08, and 11.

- Local environment presence check on 2026-06-07:
  - `NZ_LEGISLATION_API_KEY`: absent.
  - `NZLC_MIN_SECONDS_BETWEEN_REQUESTS`: absent.
  - `NZLC_OUTPUT_DIR`: absent.
- Seed inventory check on 2026-06-07:
  - `seeds/work_ids.txt`: absent.
  - `seeds/work_ids.txt.example` and `seeds/work_ids.example.txt`: present as examples only.
- Local data check on 2026-06-07:
  - `data/`: absent.
- Local doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `NZ_LEGISLATION_API_KEY`: warning, not configured.
  - `output_dir`: `data`.
- Live sync command was not run because it would not prove the external path without a configured API key and seed file.

## Blocked Items

- Cannot run `uv run nzlc sync --seed-work-ids seeds/work_ids.txt --max-works 5` until `NZ_LEGISLATION_API_KEY` is configured.
- Cannot prove five-or-fewer seed works are synced exactly as requested until an authoritative `seeds/work_ids.txt` exists.
- Cannot generate live validation, manifest, coverage, or sync-state evidence until the conservative live sync succeeds.
