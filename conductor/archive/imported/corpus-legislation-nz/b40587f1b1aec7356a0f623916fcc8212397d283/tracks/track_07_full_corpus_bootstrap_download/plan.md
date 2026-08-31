# Plan - Full Corpus Bootstrap Download

## Tasks
- [x] Confirm runner disk budget (docs/runtime_capacity_runbook.md: 25 GB min, 50 GB preferred).
- [x] Restore current Hugging Face state before incremental runs (merge_policy=restore_merge in workflow).
- [ ] Run full seed sync via GitHub Actions (68 batches of 500 work IDs each).
- [x] Use staged batches (pre-split in generated/historical-discovery-27313765016/batches/).
- [x] Preserve sync state after each batch (merge_policy=restore_merge).
- [x] Validate, manifest, coverage-report commands available and tested.
- [ ] Review missing text, XML URLs, failed versions, and ephemeral identifiers per batch.

## Current state

- `seeds/work_ids.txt` exists (33,693 work IDs, Track 04). Root blocker resolved.
- All 68 reviewed historical batch files exist in `seeds/reviewed/` (0001-0068).
- Historical batches 0001-0003 confirmed-uploaded to `edithatogo/corpus-legislation-nz-historical`.
- Batch 0004 no-upload triggered: run `27362894765`.
- Full live corpus sync (68 batches) must run via GitHub Actions (no local API key or disk).
- Expected 4-6 weeks of batched historical uploads at current pace.
- 2026-06-21 live dispatch check: `gh auth status` reports the active
  `edithatogo` keyring token is invalid, so this shell cannot trigger or inspect
  the GitHub Actions run until GitHub CLI authentication is refreshed.
- 2026-06-21 final serial bootstrap dispatched after GitHub CLI auth was
  refreshed: run `27898963687`,
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27898963687`.
  Inputs: `seed_work_ids_path=seeds/work_ids.txt`, `batch_size=500`,
  `start_batch=1`, `end_batch=68`, `merge_policy=restore_merge`,
  `min_seconds_between_requests=0.5`, `max_parallel=1`, `serial=true`,
  `max_works=none`.
- 2026-06-21 period-sharding decision: the current serial run remains the
  full-bootstrap evidence path, but period-level agent handoff is now split to
  Track 36. Track 36 owns canonical time-period shards, annual recent/API-native
  shards, per-period checkpoint artifacts, and period-level review status.
- 2026-06-21 latest live check: run `27898963687` remains `in_progress`.
  `plan` completed successfully, `batch` was skipped because `serial=true`,
  and `serial` is still running `Sync all bootstrap batches sequentially`.
- 2026-06-29 follow-up check: run `27898963687` completed with conclusion
  `cancelled`. The `serial` job was cancelled during
  `Sync all bootstrap batches sequentially` after about six hours, and the
  validate/manifest/coverage/artifact steps were skipped. This confirms that a
  single all-batch serial run is not viable on GitHub-hosted runners.
- 2026-06-29 remediation: added `nzlc merge-bootstrap-artifacts` and a
  `merge_batches` job to `.github/workflows/full_corpus_bootstrap.yml`.
  Hosted runs should now use `serial=false`; each batch uploads a shard
  artifact, and the merge job assembles a standard
  `full-corpus-bootstrap-download` artifact with root `data/`, manifests,
  sync state, Parquet, raw content, and review report.
- 2026-06-30 quota-safe continuation: cancelled replacement full-range run
  `28409376276` and added
  `.github/workflows/scheduled_full_corpus_bootstrap_batches.yml` to resume at
  batch 0024. The dispatcher uses the NZ Legislation API daily key limit of
  10,000 requests and schedules at 80% utilisation (8,000 requests/day).
- 2026-06-30 batch 0024 continuation evidence: run `28410878072`
  completed successfully and `nzlc review-full-corpus-bootstrap` passed against
  the downloaded `full-corpus-bootstrap-download` artifact. Review counts:
  969 records in `records.jsonl`, manifest, and coverage; validation OK; 0
  records failed; 483 XML-to-HTML fallback warnings; manifest SHA-256
  `0c41ca5a4c793247e0c94ca612992c4d2a675f80917eee1796410b9f38df4cb6`.
  Sync state recorded 500 works checked, 874 versions checked, 874 records
  added, and 12 Parquet files written. This supports a two-batch daily window:
  approximate upper-bound API requests were 2,731, so two similar batches stay
  under the 8,000 request/day target while three fallback-heavy batches could
  approach the cap. Next daily window is batches 0025-0026 with
  `max_parallel=2`.
- 2026-06-30 batches 0025-0026 continuation evidence: run `28418448745`
  completed successfully with `max_parallel=2`, and
  `nzlc review-full-corpus-bootstrap` passed against the downloaded
  `full-corpus-bootstrap-download` artifact. Review counts: 1,677 records in
  `records.jsonl`, manifest, and coverage; validation OK; 0 records failed;
  966 XML-to-HTML fallback warnings; manifest SHA-256
  `98899d1e183898240f4eb83a78e9397cd757f91f79fa9ed71a4957dc9ed975dd`.
  Merged sync state recorded 1,000 works checked, 1,582 versions checked,
  1,582 records added, and 22 Parquet files written. Next daily window is
  batches 0027-0028 with `max_parallel=2`.
- 2026-07-01 scheduler utilisation update: the automatic dispatcher initially
  started at batch 0029 with schedule day 0 on 2026-07-01, after manual
  continuation covered batches 0024-0028. The conservative budget remains
  10,000 API requests/day, 80% utilisation (8,000 usable requests/day), 500
  work IDs/batch, and 8 requests/work ID budget, which yields two guaranteed
  batches/day. After batches 0029-0030 succeeded, the scheduler was retargeted
  to start at batch 0031 on 2026-07-02 with `target_batches_per_day=3` and
  `max_parallel=3`: two batches are within the conservative budget and the
  third is an opportunistic catch-up batch. Batches 0031 and 0032 were then
  run manually in the same NZ quota window, so the scheduler was retargeted
  again to start at batch 0033 on 2026-07-02 to avoid duplicate dispatches.
  If an opportunistic batch fails or exceeds quota, resume or rerun that batch
  in the next daily window before advancing.
- 2026-07-01 batch 0028 repair evidence: run `28464210390` completed
  successfully after the dated-URL fallback patch. Local review of the
  downloaded `full-corpus-bootstrap-download` artifact passed: 1,389 records in
  `records.jsonl`, manifest, and coverage; validation OK; 0 records failed;
  474 warnings, including 473 XML-to-HTML fallback warnings; manifest SHA-256
  `6622c7e7c1256cfe73096cc31f3c72576ff9ffa5855d378e64b241003779c073`.
  Sync state recorded 1,294 versions checked, 1,294 records added, 0 failed,
  and 10 Parquet files written. The stale
  `act_public_1992_27_en_1992-04-10` URL was recovered through the
  `1992-04-10A` alternate and now maps to the same content hash as the
  `act_public_1992_27_en_1992-04-10A` version.
- 2026-07-01 batches 0029-0030 continuation evidence: run `28496717521`
  completed successfully with `max_parallel=2`. Batch 0029 completed in
  1h00m44s, batch 0030 completed in 1h22m45s, and the `merge_batches` job
  completed in 53s. Local review of the downloaded merged
  `full-corpus-bootstrap-download` artifact passed: 3,455 records in
  `records.jsonl`, manifest, and coverage; validation OK; 0 records failed;
  940 warnings, including 937 XML-to-HTML fallback warnings; 0 browser
  fallback warnings; manifest SHA-256
  `62e2bb8664404ff10abc32e8830aa9dac8a38f38e49ac3e5614a0ad89f5d21ec`.
  Merged sync state recorded 3,397 versions checked, 3,360 records added,
  36 records unchanged, 1 record changed, 0 failed, and 23 Parquet files
  written. The downloaded local review report was written to ignored generated
  evidence path `generated/full-corpus-bootstrap/review_report_28496717521_merged.json`.
- 2026-07-01 manual third-batch evidence: run `28502342645` covered batch
  0031 on `main` and completed successfully. Batch 0031 completed in 49m14s,
  and the `merge_batches` job completed in 38s. Local review of the downloaded
  merged `full-corpus-bootstrap-download` artifact passed: 1,702 records in
  `records.jsonl`, manifest, and coverage; validation OK; 0 records failed;
  78 warnings, including 77 XML-to-HTML fallback warnings; 0 browser fallback
  warnings; manifest SHA-256
  `203559ef1425477f761a16e22b99c435b2ba52038fc122e4f495ed5cecc71568`.
  Merged sync state recorded 1,627 versions checked, 1,607 records added,
  20 records unchanged, 0 failed, and 12 Parquet files written.
- 2026-07-01 manual fourth-batch evidence: run `28505079812` covered batch
  0032 on `main` and completed successfully. Local review of the downloaded
  merged `full-corpus-bootstrap-download` artifact passed: 1,541 records in
  `records.jsonl`, manifest, and coverage; validation OK; 0 records failed;
  0 warnings; manifest SHA-256
  `88579cb57d688b3db3ea114734a3538229ec33824de74e1fb8f67af8255e45a1`.
  Merged sync state recorded 500 works checked, 1,446 versions checked,
  1,446 records added, 0 records unchanged, 0 failed, and 13 Parquet files
  written. The next scheduled window is batches 0033-0035, with batch 0035
  treated as the opportunistic third batch.
- 2026-07-02 daily maximum probe: manual continuation runs covered batches
  0033-0042 successfully before the next scheduled dispatcher could take over.
  Runs `28510037176`, `28511889179`, `28513240315`, `28514259299`,
  `28515266056`, `28516266938`, and `28517300595` covered batches 0033-0039
  individually on `main`. Run `28518390359` then attempted batches 0040-0044
  with `max_parallel=3`; batches 0040, 0041, and 0042 validated and uploaded
  their batch artifacts, while batches 0043 and 0044 completed sync but failed
  the `Validate, manifest, and coverage-report` step. The failed reports
  surfaced `missing_xml_url` and `ephemeral_identifier` records for
  `secondary-legislation_agency-drafted_~...` stable IDs, not an API quota
  or runner-timeout failure. The current observed fully validated daily maximum
  is therefore six batches for the new NZ quota window: boundary batch 0037
  plus batches 0038-0042. Scheduler defaults now resume at batch 0043 on
  2026-07-03 NZ time with `target_batches_per_day=6` and `max_parallel=3`.
  Batch 0043 should be retried first; if the validation failure persists,
  classify or remediate the agency-drafted secondary-legislation records before
  advancing the schedule.
- 2026-07-02 remediation: validation logs for run `28528178088` showed the
  blocking errors were `empty_text` and missing required `text`/`source_url`
  fields on agency-drafted secondary-legislation records. The pipeline now
  defers metadata-only versions with no downloadable XML/HTML body into
  `data/_state/metadata_only_deferred.jsonl`, records `records_deferred`, and
  keeps those rows out of `records.jsonl` so batch artifacts can validate while
  preserving explicit gap evidence for official website/NZLII redundancy triage.
- 2026-07-02 repair validation: PR #75 merged as `63418d9`, and manual run
  `28558440077` reran batches 0043-0047 on `main` with `max_parallel=3`.
  All five batch jobs validated and uploaded artifacts, the `merge_batches`
  job succeeded, and the merged `full-corpus-bootstrap-download` review reported
  `ok=true`, 873 validated records, 0 failed records, 0 missing text/XML risk
  indicators, and 1,981 deferred metadata-only records preserved in
  `_state/metadata_only_deferred.jsonl`. Together with prior batch 0048, Track
  07 is now validated through batch 0048. The scheduled dispatcher should resume
  at batch 0049 on the next NZ quota window.
- 2026-07-02 batch 0049 probe: at the user's request, manual run `28559818771`
  processed batch 0049 on `main` with `max_parallel=1`. The batch and
  `merge_batches` jobs succeeded. The downloaded `full-corpus-bootstrap-download`
  review reported `ok=true`, 1,177 validated records, 0 failed records, 0
  deferred records, 0 missing text/XML risk indicators, 500 works checked, 1,082
  versions checked, and 21 Parquet files written. Track 07 is now validated
  through batch 0049, so the scheduled dispatcher should resume at batch 0050.
- 2026-07-02 batches 0050-0051 probes: manual run `28561731954` processed
  batch 0050 on `main` and completed successfully, including batch validation,
  `merge_batches`, and `full-corpus-bootstrap-download` upload. Manual run
  `28563126811` first processed batch 0051 and validated 1,181 records, but
  merge review failed because
  `secondary-legislation_pco-drafted_2001_007_en_2007-09-03` returned 404 at
  its official exposed content URL. PR #78 merged the repair that defers
  deterministic not-found content downloads with reason `download_source_not_found`.
  Repair rerun `28564452205` then completed successfully. The downloaded
  `full-corpus-bootstrap-download` review reported `ok=true`, 1,181 validated
  records, 1 deferred metadata retrieval gap, 0 failed records, 0 missing
  text/XML risk indicators, 500 works checked, 1,087 versions checked, and 11
  Parquet files written. Track 07 is now validated through batch 0051, so the
  scheduled dispatcher should resume at batch 0052.
- 2026-07-02 batch 0052 probe: manual run `28566570973` processed batch 0052
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,170 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,075
  versions checked, and 10 Parquet files written. Track 07 is now validated
  through batch 0052, so the scheduled dispatcher should resume at batch 0053.
- 2026-07-02 batch 0053 probe: manual run `28568946847` processed batch 0053
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,213 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,118
  versions checked, and 10 Parquet files written. Track 07 is now validated
  through batch 0053, so the scheduled dispatcher should resume at batch 0054.
- 2026-07-02 batch 0054 probe: manual run `28571640868` processed batch 0054
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,180 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,085
  versions checked, and 9 Parquet files written. Track 07 is now validated
  through batch 0054, so the scheduled dispatcher should resume at batch 0055.
- 2026-07-02 batch 0055 probe: manual run `28574778367` processed batch 0055
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,164 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,069
  versions checked, and 10 Parquet files written. Track 07 is now validated
  through batch 0055, so the scheduled dispatcher should resume at batch 0056.
- 2026-07-02 batch 0056 probe: manual run `28577774075` processed batch 0056
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,200 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,105
  versions checked, and 9 Parquet files written. Track 07 is now validated
  through batch 0056, so the scheduled dispatcher should resume at batch 0057.
- 2026-07-02 batch 0057 probe: manual run `28581048704` processed batch 0057
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,191 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,096
  versions checked, and 9 Parquet files written. Track 07 is now validated
  through batch 0057, so the scheduled dispatcher should resume at batch 0058.
- 2026-07-02 batch 0058 probe: manual run `28584537830` processed batch 0058
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,100 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 1,005
  versions checked, and 9 Parquet files written. Track 07 is now validated
  through batch 0058, so the scheduled dispatcher should resume at batch 0059.
- 2026-07-02 batch 0059 probe: manual run `28587801975` processed batch 0059
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,054 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 959
  versions checked, and 10 Parquet files written. Track 07 is now validated
  through batch 0059.
- 2026-07-02 batch 0060 probe: manual run `28588847327` processed batch 0060
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,074 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 979
  versions checked, and 9 Parquet files written. Track 07 is now validated
  through batch 0060, so the scheduled dispatcher should resume at batch 0061.
- 2026-07-03 batch 0061 probe: manual run `28593549021` processed batch 0061
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,034 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 939
  versions checked, and 9 Parquet files written. Track 07 is now validated
  through batch 0061, so the scheduled dispatcher should resume at batch 0062.
- 2026-07-03 batch 0062 probe: manual run `28598279801` processed batch 0062
  on `main` with `max_parallel=1`. The batch and `merge_batches` jobs
  succeeded. The downloaded `full-corpus-bootstrap-download` review reported
  `ok=true`, 1,061 validated records, 0 failed records, 0 deferred records,
  0 warnings, 0 missing text/XML risk indicators, 500 works checked, 966
  versions checked, and 10 Parquet files written. Track 07 is now validated
  through batch 0062, so the scheduled dispatcher should resume at batch 0063.
- 2026-07-03 batches 0063-0067 probe: manual run `28606962250` processed
  batches 0063-0067 on `main` with `max_parallel=3`. The batch jobs and
  `merge_batches` job succeeded. The downloaded `full-corpus-bootstrap-download`
  review reported `ok=true`, 4,257 validated records, 0 failed records, 0
  deferred records, 0 warnings, 0 missing text/XML risk indicators, 2,500 works
  checked, 4,162 versions checked, 4,162 records added, and 48 Parquet files
  written across the five downloaded batch artifacts. Track 07 is now
  validated through batch 0067, so the scheduled dispatcher should resume at
  batch 0068.

## Batch 0001 no-upload evidence

- Reviewed batch path: `seeds/reviewed/historical-work-ids-0001.txt`.
- GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27316467370`.
- Result: success with `upload_confirmed=false`; no Hugging Face write.
- Validation/manifest/coverage completed for 4,737 restored/merged records.
- Initial sync state recorded 436 failed versions, mostly early local/imperial
  Act XML 404 responses.
- XML-to-HTML fallback remediated the failures in rerun
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27330484544`.
- Confirmed batch 0001 upload passed in
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27331999831`.
- Confirmed batch 0001 sync state: 623 versions checked, 623 records added, 0
  records failed, 436 XML-to-HTML fallback warnings.
- Historical Hugging Face revision after upload:
  `dcc92964ef832c7e0bd2f904f88de523998304f2`.

## Batch 0002 evidence

- Reviewed batch path: `seeds/reviewed/historical-work-ids-0002.txt`.
- No-upload GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27344560156`.
- Confirmed batch 0002 upload passed in
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27347686841`.
- Confirmed batch 0002 sync state: 606 versions checked, 606 records added, 0
  records failed, 482 XML-to-HTML fallback warnings.
- Validation/manifest/coverage completed for 5,779 restored/merged records.
- Historical Hugging Face revision after upload:
  `bb425cb308410fac43095a30f88c9d92848a0eb8`.

## Batch 0003 evidence

- Reviewed batch path: `seeds/reviewed/historical-work-ids-0003.txt`.
- No-upload GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27351234418`.
- Confirmed batch 0003 upload passed in
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27354924156`.
- Confirmed batch 0003 sync state: 612 versions checked, 605 records added, 7
  records unchanged, 0 records failed, 487 XML-to-HTML fallback warnings.
- Validation/manifest/coverage completed for 6,384 restored/merged records.
- Historical Hugging Face revision after upload:
  `0cc4021cae106c0b9ae3722488faed21df3e578c`.


## Implementation automation added 2026-06-12

- Added `.github/workflows/full_corpus_bootstrap.yml` with manual batch splitting, disk-budget enforcement, HF restore, staged `nzlc sync`, validation, manifest, coverage-report, and artifact evidence.
- See `docs/full_corpus_operations.md` for the operator inputs and review
  sequence for this workflow.
- Parallel mode supports reviewed batch evidence; `serial=true` preserves one cumulative `data/` directory on a sufficiently large runner.
- Track remains `in_progress` until a full seed sync run produces and records final evidence.

## Full corpus bootstrap pilot run evidence (2026-06-12)

Run: `27396415830` (triggered via `gh workflow run`)
- Inputs: `batch_size=500`, `start_batch=1`, `end_batch=1`, `min_seconds_between_requests=1.0`, `serial=false`, `max_parallel=1`, `max_works=none`
- Plan job: completed (12s) with batch_count=1 for 500 work IDs
- Batch 0001 job: ran from 05:24:07Z to 10:38:47Z (5h14m40s)
  - Sync bootstrap batch step: 05:24:18Z to 10:38:46Z (5h14m28s)
  - Validate, manifest, and coverage-report: completed
  - Upload batch bootstrap artifact: completed
  - Batch summary: completed
- Serial job: skipped (serial=false)

### Sync performance analysis

500 work IDs (batch_0001: early imperial acts 1539-1730) took 5h14m at 1.0s pacing.
This is ~37 seconds per work ID, far above the ~3s expected from pacing alone.

Root cause: NZ Legislation API rate limiting. The `_sleep_for_low_quota` method
triggers when `X-RateLimit-Remaining` drops below `rate_limit_low_watermark=10`,
sleeping for `reset_time / remaining` seconds per call. Once quota is depleted,
the client waits for the full quota reset window (typically 1 hour) before
continuing, causing the exponential slowdown.

### Recommendation for full 68-batch run

1. Use `serial=true` with one cumulative data directory (24h runner timeout, 50GB+ disk)
2. Set `min_seconds_between_requests=0.5` for initial batches, then reduce to 0.2
   after confirming no 429/403 rate limiting
3. Expected wall-clock time: 8-15 hours for the full 33,693 work IDs at 0.5s pacing
   with observed API latency
4. Monitor `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers; if quota
   exhaustion is frequent, contact NZ Legislation API support for a higher tier
5. Alternative: process through the historical bootstrap workflow
   (`historical_hf_upload.yml`) which has been proven at 500-work scale with
   batches 0001-0003

## Code improvements applied 2026-06-13

The following production-hardening changes were made to support reliable 68-batch processing:

### Critical: quota sleep cap (`config.py`, `nz_api.py`)

Added `rate_limit_max_sleep_seconds=60.0` to cap `_sleep_for_low_quota`. Previously,
a quota-exhausted API key with `remaining=1` and `reset=3600s` could sleep 30+ minutes
per work ID (~1800s). The cap limits the maximum individual sleep to 60s, preventing
multi-hour stalls while still respecting the API quota system.

### Logging guard: `_download_first_available_format` (`cli.py`)

Added empty-content detection: if `download_url` returns zero bytes, the code now
raises an exception, triggering the XML->HTML fallback path instead of silently
returning empty content.

### Seed file warning: `_load_seed_work_ids` (`cli.py`)

Added a log warning when the seed work-IDs file exists but contains zero usable
(non-comment, non-empty) lines, preventing silent batch processing of empty batches.

### Serial mode progress tracking (`.github/workflows/full_corpus_bootstrap.yml`)

Added batch-level progress counters (`Processing batch 17/68`) to the serial batch
loop, providing real-time monitoring for the ~8-15 hour cumulative run.

### Extended test coverage

- **Rate limit tests** (`test_nz_api.py`): 9 new tests covering capped quota sleep,
  `_retry_after_seconds` invalid header fallback, `download_url` retries on 429/403/5xx,
  quota pause in download path, missing/expired header edge cases.
- **Download fallback tests** (`test_cli_download.py`): 5 new tests for
  `_download_first_available_format` covering XML success, XML->HTML fallback, both fail,
  HTML-only, and no formats available.
- **Coverage report tests** (`test_cli_coverage.py`): 3 new tests for empty corpus,
  multi-type records with risk indicators, and history append.
- **HF sync test** (`test_hf_sync.py`): prune stale paths test added.

All 65 tests pass; ruff lint clean.

## Test environment isolation applied 2026-06-16

After merging the 2026-06-13 hardening, the full pytest run on a developer
workstation exposed 34 pre-existing failures caused by user-shell `NZLC_*`
environment variables leaking into the test process and tripping
`pydantic_settings` list-field validation. These failures were independent of
the hardening work and surfaced only when the developer's shell exported
`NZLC_SEARCH_TERMS=law,act,...` style CSV values.

### Fix: tests/conftest.py autouse session fixture

Added a session-scoped autouse fixture (`_isolate_settings_env`) that pops the
known `NZLC_*`, `NZ_LEGISLATION_*`, `HF_TOKEN`, and `HF_HUB_TOKEN` env vars
before any test runs, so `Settings()` resolves to its declared defaults.

### Result

- `uv run pytest -q -p no:cacheprovider tests` reports **122 passed** in ~8s.
- `uv run ruff check tests/conftest.py` reports **All checks passed**.
- 5 pre-existing ruff findings in `embeddings.py` (D205/D212/D400/D415) and
  `utils.py` (I001) are unrelated to this track and remain on `main`; they are
  tracked separately.

## Artifact review gate added 2026-06-21

- Added `nzlc review-full-corpus-bootstrap` to review a downloaded
  `full_corpus_bootstrap.yml` artifact before any completeness claim.
- The review gate checks for `records.jsonl`, validation, manifest, coverage,
  and sync-state artifacts; records failed; failed-version warnings; manifest
  hash presence; manifest and coverage record-count agreement with
  `records.jsonl`; and missing text, missing XML URL, and ephemeral identifier
  risk indicators.
- The command writes `generated/full-corpus-bootstrap/review_report.json` by
  default and exits non-zero when required evidence is missing or failed.
- 2026-06-21 review fix: non-zero risk indicators and manifest/count
  mismatches now fail the review and require triage before Track 07 completion.
- Focused validation passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py -q`
  reported 20 passed.
- Lint passed:
  `.venv\Scripts\python.exe -m ruff check --no-cache src\nz_legislation_corpus\bootstrap_review.py src\nz_legislation_corpus\cli.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py tests\conftest.py`.
- Test fixture hardening: `tests/conftest.py` now falls back from locked
  `test-tmp/` to `.tmp/test-tmp/` after a writability probe, preserving
  repo-local test temp directories on OneDrive-backed worktrees.


## Remaining operator tasks

1. Monitor dispatched run `27898963687` until the `serial` job completes.
2. Dispatch a hosted `serial=false` full bootstrap run for all 68 batches, or
   run `serial=true` only on a local/self-hosted runner with runtime above the
   hosted six-hour ceiling.
3. After the hosted batch run completes, download
   `full-corpus-bootstrap-download`: `data/records.jsonl`,
   `data/manifests/`, `data/_state/`, `data/parquet/`, and `data/raw_xml/`.
4. Run `nzlc review-full-corpus-bootstrap --artifact-root <downloaded-artifact>`
   and review `generated/full-corpus-bootstrap/review_report.json`.
5. Review `sync_state.json` for failed versions and XML-to-HTML fallback warnings.
6. Update tracks.md with final evidence (run URL, manifest SHA, record counts).
7. Mark Task 3 [x] and Task 7 [x] after review.

## Deferred to Track 36

- Generate period-specific seed files and a period manifest.
- Verify the API-native/recent boundary year before making recent shards annual.
- Add per-period checkpoint artifacts so another agent can start work as soon
  as a period completes.
- Add or extend the review gate for single-period artifacts.

