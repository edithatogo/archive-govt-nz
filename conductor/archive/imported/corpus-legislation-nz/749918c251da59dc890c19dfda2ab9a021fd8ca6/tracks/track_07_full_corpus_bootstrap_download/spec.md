# Spec - Full Corpus Bootstrap Download

## Status
done

## Goal
download the full corpus into local `data/` using the proven discovery method and conservative pacing.

## Acceptance Criteria
- All seed works are attempted.
- Failed versions are recorded and triaged.
- Validation passes or documented exceptions are accepted.
- Coverage report is reviewed before any public completeness claim.

## Evidence to Record
- Total works attempted.
- Total versions and records produced.
- Failed or skipped version list.
- Final manifest hash.
- Coverage report path.

## Evidence Recorded

- Seed inventory: `seeds/work_ids.txt` now exists with 33,693 work IDs (search-derived, documented in Track 04).
- Pre-split batches: 68 batches of 500 work IDs each in `generated/historical-discovery-27313765016/batches/`.
- Historical batches 0001-0003 confirmed-uploaded to `edithatogo/corpus-legislation-nz-historical`.
- Batch 0004 no-upload triggered on 2026-06-11: run `27362894765`.
- Full live corpus sync requires GitHub Actions (no local API key; local disk ~7.5 GB free below 25 GB minimum).
- Runner disk budget documented in `docs/runtime_capacity_runbook.md`: minimum 25 GB, prefer 50 GB.
- 2026-06-16: Test environment isolation added in `tests/conftest.py` (autouse session fixture `_isolate_settings_env`); full pytest run now reports **122 passed**, unblocking this track's automated validation gate.
- 2026-06-21: Added `nzlc review-full-corpus-bootstrap` as the deterministic
  post-artifact review gate for validation, manifest, coverage, sync-state, and
  failed-version evidence. The gate now fails artifacts with manifest/count
  mismatches or non-zero missing text, missing XML URL, or ephemeral identifier
  risk indicators.
- 2026-06-21: Final serial bootstrap dispatched after GitHub CLI auth was
  refreshed: run `27898963687`,
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27898963687`.
  The run remains `in_progress` pending completion of the `serial` job.
- 2026-07-03: Batch 0068 completed successfully in run `28635745595` with
  `ok=true`, 298 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, and manifest hash
  `0feea3b522e9c121450d2d2751b02661f6472c044a62ce8e5f2d284a689982d1`.
  The merged artifact root was
  `generated/full-corpus-bootstrap/downloaded-batches/full-corpus-batch-0068-download`.

## Remaining Tasks

- None. The full bootstrap completed through batch 0068 and the corpus is now
  fully validated for the current seed set.
