# Project Tracks

## [ ] Track: dataset_identifier_interlinking_20260721

[Specification and plan](./tracks/dataset_identifier_interlinking_20260721/)

This file tracks the major work items for `corpus-legislation-nz`.

---

## Status Key

- `todo`: not started.
- `blocked`: waiting on credentials, external access, or a decision.
- `ready`: prerequisites are available and implementation can proceed.
- `in_progress`: actively being worked.
- `done`: acceptance criteria are met and evidence is recorded.

## Reconciliation Note - 2026-06-10

The approved partial/API-discovery launch is complete. GitHub repository
publication, required secrets/variables, live Hugging Face publication, Zenodo
production DOI publication, release/tag creation, and post-launch rename to
`corpus-legislation-nz` have been verified.

Remaining blockers are now scoped to full-corpus completeness, long-running
historical coverage, scheduled maintenance evidence, and roadmap tracks. Older
track text that refers to missing GitHub remotes, missing public Hugging Face
shells, or absent launch secrets should be read as superseded by this
reconciliation unless the individual track still preserves a full-completeness
blocker.

## Track 01 - Repository Commit And Release Baseline

Status: `done`

Goal: get the current local implementation into a clean Git baseline before any live data operation is treated as repeatable.

Actions:

- Resolve the parent `OneDrive - Flinders` Git root lock issue or move `corpus-law-nz` into an isolated Git repository.
- Commit the currently staged rate-limit hardening, bootstrap guardrails, tests, and documentation.
- Generate a clean `uv.lock` from the final repository root.
- Switch CI dependency installation to `uv sync --all-extras --frozen` after `uv.lock` exists.
- Run `pytest -q -p no:cacheprovider tests`.
- Run `ruff check src/nz_legislation_corpus tests`.

Acceptance criteria:

- Git history contains a commit for the rate-limit work.
- `uv.lock` is committed.
- Tests and lint pass from the clean checkout.

Evidence to record:

- Commit SHA.
- Test command output summary.
- Lint command output summary.

## Track 02 - Credential And Secret Inventory

Status: `done`

Goal: confirm all credentials and GitHub variables required for live corpus operations are present, scoped correctly, and stored in the right place.

Actions:

- Confirm `NZ_LEGISLATION_API_KEY` exists and can call the NZ Legislation API.
- Confirm `HF_TOKEN` exists and has write access only to the intended Hugging Face dataset repository where possible.
- Confirm `HF_REPO_ID` is final.
- Confirm `ZENODO_TOKEN` exists for sandbox first.
- Decide whether production Zenodo uses a separate token and required reviewer environment.
- Store GitHub secrets: `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `ZENODO_TOKEN`.
- Store GitHub variables: `HF_REPO_ID`, `NZLC_SEARCH_TERMS`, `NZLC_SEARCH_FIELD`, `NZLC_SEARCH_SORT_BY`, `NZLC_LEGISLATION_TYPES`, `ARCHIVE_CREATORS_JSON`, and archive metadata.
- Run `uv run nzlc doctor` locally or through GitHub Actions.

Acceptance criteria:

- `nzlc doctor` passes without exposing secret values.
- GitHub Actions has the required secrets and variables.
- Zenodo production publication remains approval-gated.

Evidence recorded:

- GitHub repository secrets exist by name: `NZ_LEGISLATION_API_KEY`,
  `HF_TOKEN`, and `ZENODO_TOKEN`.
- GitHub repository variables include `HF_REPO_ID=edithatogo/corpus-legislation-nz`
  and `HF_HISTORICAL_REPO_ID=edithatogo/corpus-legislation-nz-historical`,
  plus archive and NZLC search variables.
- Branch protection on `main` requires strict `tests`, one approving review,
  admin enforcement, linear history, no force pushes, and no deletions.

## Track 03 - Hugging Face Dataset Shell

Status: `done`

Goal: create and verify the Hugging Face dataset repository before uploading corpus data.

Actions:

- Create or confirm the Hugging Face dataset repository named by `HF_REPO_ID`.
- Run `scripts/create_huggingface_dataset_repo.sh "$HF_REPO_ID"` or equivalent API setup.
- Confirm the remote layout is root-based, not nested under `data/`.
- Confirm `.gitattributes`, dataset card metadata, and lightweight root placeholders are correct.
- Remove any legacy `data/...` placeholders if present.

Acceptance criteria:

- Hugging Face repo exists and is writable by the configured token.
- Root-level layout is ready for `parquet/`, `raw_xml/`, `manifests/`, and `_state/`.
- Dataset card describes live corpus status without claiming full coverage before discovery proof.

Evidence to record:

- Hugging Face repo URL.
- Root layout listing.
- Dataset card revision or commit hash.

Current evidence:

- Live Hugging Face dataset:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Current verified revision:
  `6b082e2f85802cb374898d689d264017a047799b`.
- Dataset is public and has root-level publication artifacts.
- Legacy DOI-bound Hugging Face dataset
  `edithatogo/nz-legislation-corpus` remains as a compatibility shell pointing
  to the renamed dataset.

## Track 04 - Source Discovery Completeness

Status: `done`

Goal: establish the discovery method needed before the project can claim a complete corpus.

Actions:

- Contact or check the NZ Legislation source for an official work ID export or complete inventory.
- If no official export is available, build `seeds/work_ids.txt` from a documented authoritative inventory.
- Keep comments and provenance in the seed file or adjacent documentation.
- Reconcile seed coverage against search-based discovery.
- Define expected counts by legislation type, status, and year where available.
- Document any known exclusions, ephemeral IDs, or incorporated-by-reference caveats.

Acceptance criteria:

- `seeds/work_ids.txt` or an equivalent documented inventory exists.
- `docs/source_discovery_strategy.md` states the actual discovery source used.
- Public docs distinguish pipeline completeness from proven corpus completeness.

Current evidence:

- `seeds/work_ids.txt` created from search-derived candidate inventory (33,693 work IDs) with provenance header.
- Seed source: search-based API discovery with terms `act,bill,regulation,order,notice` and types `act,bill,secondary_legislation,amendment_paper` (no status filter). Discovery run: `27313765016`.
- Seed SHA-256: `4E9BD99F2D9EF3AB57C9BBD24DBA9DEAC3E3F98A0E30C4572001E189BDAC0C74`.
- Reconciliation against reviewed historical batch 0001 (500 IDs): 33,193 added, 0 removed â€” search-derived inventory is a superset.
- Expected counts by type: act (16,829), secondary_legislation (12,226), amendment_paper (2,764), bill (1,874).
- Caveat: search-derived inventory is not authoritative; public docs (README, DATASET_CARD, source_discovery_strategy) state coverage is not proven complete.

## Track 05 - Conservative Live Smoke Sync

Status: `done`

Goal: prove the live sync path against external services without risking rate limits or large uploads.

Actions:

- Set `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=1.0`.
- Run `uv run nzlc sync --seed-work-ids seeds/work_ids.txt --max-works 5`.
- Run `uv run nzlc validate`.
- Run `uv run nzlc manifest`.
- Run `uv run nzlc coverage-report`.
- Inspect `data/_state/sync_state.json`, `data/manifests/latest_manifest.json`, and `data/manifests/latest_changes.json`.

Acceptance criteria:

- Five or fewer seed works are synced exactly as requested.
- Validation passes.
- Manifest and coverage report are generated.
- No rate-limit failures are unhandled.

Evidence to record:

- Command summaries.
- Synced work count.
- Any API warnings from sync state.

Current evidence:

- Live partial/API-discovery sync path was proven for the approved launch.
- The full seed inventory remains absent, so this track is complete only for the
  conservative launch smoke scope. Full coverage remains blocked under Tracks
  04, 07, 08, and 11.

## Track 06 - First Hugging Face Smoke Upload

Status: `done`

Goal: prove upload, restore, and no-change behavior on Hugging Face with the small smoke corpus.

Actions:

- Run `uv run nzlc hf-upload` against the smoke data.
- Download the Hugging Face dataset back into a clean local `data/` directory.
- Confirm root-level remote files map to local `data/parquet/`, `data/raw_xml/`, `data/manifests/`, and `data/_state/`.
- Rerun upload with unchanged content and confirm it skips or produces no content churn.
- Inspect the Hugging Face dataset viewer and sample Parquet reads.

Acceptance criteria:

- Smoke corpus is visible in Hugging Face.
- Re-download produces the expected local layout.
- No-change upload behavior is proven.

Evidence to record:

- Hugging Face commit or revision.
- Manifest hash before and after no-change upload.
- Sample Parquet read result.

Current evidence:

- The live Hugging Face upload, restore/no-change behavior, and sample dataset
  verification passed for the approved partial/API-discovery launch.
- Live dataset target:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Current verified revision:
  `6b082e2f85802cb374898d689d264017a047799b`.

## Track 07 - Full Corpus Bootstrap Download

Status: `done`

Goal: download the full corpus into local `data/` using the proven discovery method and conservative pacing.

Actions:

- Confirm enough local disk space for raw files, Parquet, manifests, and temporary archive work.
- Restore current Hugging Face corpus state into `data/` if any previous upload exists.
- Run full seed sync with `NZLC_MIN_SECONDS_BETWEEN_REQUESTS` set conservatively.
- Use staged batches if the seed inventory is large or API limits are uncertain.
- Preserve sync state after each batch.
- Run `uv run nzlc validate`, `uv run nzlc manifest`, and `uv run nzlc coverage-report`.
- Review missing text, missing XML URLs, failed versions, and ephemeral identifiers.

Acceptance criteria:

- All seed works are attempted.
- Failed versions are recorded and triaged.
- Validation passes or documented exceptions are accepted.
- Coverage report is reviewed before any public completeness claim.

Evidence to record:

- Total works attempted.
- Total versions and records produced.
- Failed or skipped version list.
- Final manifest hash.
- Coverage report path.

Current state:

- `seeds/work_ids.txt` exists (33,693 work IDs, Track 04). Root blocker resolved.
- 68 pre-split batches available in `generated/historical-discovery-27313765016/batches/`.
- Historical batches 0001-0003 confirmed-uploaded to `edithatogo/corpus-legislation-nz-historical`.
- Batch 0004 no-upload triggered: run `27362894765`.
- Batches 0005-0067 (63 batches) required the no-upload -> review -> confirmed-upload cycle.
- Full bootstrap workflow is now present in `.github/workflows/full_corpus_bootstrap.yml`.
- Full corpus operations runbook is now documented in `docs/full_corpus_operations.md`.
- Pilot run `27396415830` completed batch 0001 (500 work IDs) with full validate/manifest/coverage cycle in 5h14m at 1.0s pacing.
- Sync is rate-limit constrained: ~37s per work ID due to NZ Legislation API quota exhaustion sleeps.
- **2026-06-13 fix**: `rate_limit_max_sleep_seconds=60.0` added to cap `_sleep_for_low_quota`, preventing multi-hour stalls when quota is exhausted.
- Full sync must run via GitHub Actions (no local API key; local disk ~7.5 GB free).
- Runner disk budget: 25 GB min, 50 GB preferred (docs/runtime_capacity_runbook.md).
- **2026-06-13 hardening**: Empty-content detection in XML->HTML fallback, seed file emptiness warning, serial-mode batch progress counters, and extended test coverage (65 tests, ruff clean).
- **2026-06-16 test environment isolation**: `tests/conftest.py` autouse session fixture `_isolate_settings_env` clears user-shell `NZLC_*` / `NZ_LEGISLATION_*` / `HF_TOKEN` env vars before pytest. Pre-existing 34 failures (caused by developer env leaking CSV values into `pydantic_settings` list fields) are now resolved. Full suite: **122 passed** in ~8s. ruff clean on `tests/conftest.py`. Pre-existing lint findings in `embeddings.py` / `utils.py` are unrelated and tracked separately.
- **2026-06-21 artifact review gate**: `nzlc review-full-corpus-bootstrap`
  now reviews downloaded full-bootstrap artifacts for required files,
  validation, manifest hash, coverage counts, sync-state failures, and
  failed-version warnings before any completeness claim.
- **2026-06-21 live dispatch blocker**: `gh auth status` reports the active
  `edithatogo` keyring token is invalid, so this shell cannot trigger or
  inspect the final GitHub Actions bootstrap run until GitHub CLI
  authentication is refreshed.
- **2026-06-21 final serial bootstrap dispatched**: run `27898963687`,
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27898963687`.
  Inputs were all 68 seed batches, `merge_policy=restore_merge`,
  `min_seconds_between_requests=0.5`, `max_parallel=1`, `serial=true`, and
  `max_works=none`. Initial live checks passed through required secrets,
  doctor, and Hugging Face restore; the serial sync step is in progress.
- **2026-06-29 hosted serial failure confirmed**: run `27898963687` completed
  with conclusion `cancelled`. The serial job was cancelled during
  `Sync all bootstrap batches sequentially` after about six hours, so
  validation, manifest, coverage, and artifact upload were skipped. Track 07
  cannot rely on a single all-batch hosted serial runner.
- **2026-06-29 sharded merge remediation**: `nzlc merge-bootstrap-artifacts`
  and the `full_corpus_bootstrap.yml` `merge_batches` job now support hosted
  `serial=false` runs: batch artifacts are merged into a standard
  `full-corpus-bootstrap-download` artifact with root `data/`, manifests,
  sync state, raw content, Parquet, and review report.
- **2026-06-21 period handoff note**: this all-batch serial run remains valid
  for full-bootstrap evidence, but it is not the final agent-handoff shape.
  Track 36 now owns period-sharded seed manifests, annual recent shards,
  per-period checkpoint artifacts, and period-level review/handoff status.
- **2026-07-01 scheduler and continuation evidence**: PR #67 merged the
  scheduled dispatcher onto `main`. It initially used a conservative two-batch
  daily cadence under the 8,000 request/day target. Manual run `28496717521`
  covered batches 0029-0030 with `max_parallel=2` and completed successfully.
  After that success, the scheduler was retargeted to start at batch 0031 on
  2026-07-02 with `target_batches_per_day=3` and `max_parallel=3`: two batches
  are within the conservative request budget, and the third is an opportunistic
  catch-up batch to resume or rerun in the next daily window if unsuccessful.
  Local review of the merged
  `full-corpus-bootstrap-download` artifact passed: 3,455 records in
  `records.jsonl`, manifest, and coverage; validation OK; 0 records failed;
  940 warnings, including 937 XML-to-HTML fallback warnings; 0 browser
  fallback warnings; manifest SHA-256
  `62e2bb8664404ff10abc32e8830aa9dac8a38f38e49ac3e5614a0ad89f5d21ec`.
  Merged sync state recorded 3,397 versions checked, 3,360 records added,
  36 records unchanged, 1 record changed, 0 failed, and 23 Parquet files
  written.
- **2026-07-01 manual third/fourth batch evidence**: batch 0031 run
  `28502342645` completed successfully on `main`; local review passed with
  1,702 records in `records.jsonl`, manifest, and coverage, validation OK,
  0 records failed, 78 warnings including 77 XML-to-HTML fallback warnings,
  and manifest SHA-256
  `203559ef1425477f761a16e22b99c435b2ba52038fc122e4f495ed5cecc71568`.
  Batch 0032 run `28505079812` also completed successfully on `main`; local
  review passed with 1,541 records in `records.jsonl`, manifest, and coverage,
  validation OK, 0 records failed, 0 warnings, and manifest SHA-256
  `88579cb57d688b3db3ea114734a3538229ec33824de74e1fb8f67af8255e45a1`.
  The scheduler was retargeted to start at batch 0033 on 2026-07-02 to avoid
  duplicating the manually completed batches. Track 07 remains in progress;
  next scheduled daily window is batches 0033-0035, with batch 0035 treated as
  the opportunistic third batch.
- **2026-07-02 daily maximum probe**: manual continuation advanced batches
  0033-0042. Runs `28510037176`, `28511889179`, `28513240315`,
  `28514259299`, `28515266056`, `28516266938`, and `28517300595` completed
  batches 0033-0039 individually. Run `28518390359` attempted batches
  0040-0044 with `max_parallel=3`; batches 0040-0042 validated and uploaded
  batch artifacts, while batches 0043-0044 failed after sync during
  `Validate, manifest, and coverage-report` with `missing_xml_url` and
  `ephemeral_identifier` records for agency-drafted secondary legislation.
  This was not an observed API quota failure. The current operational maximum
  for fully validated daily progress is recorded as six batches in the new NZ
  quota window, and the scheduler now resumes at batch 0043 on 2026-07-03
  NZ time with `target_batches_per_day=6` and `max_parallel=3`.
- **2026-07-02 metadata-only remediation**: run `28528178088` confirmed the
  blocking validation errors were empty text and missing `text`/`source_url`
  fields for API-visible agency-drafted secondary-legislation records. Sync now
  defers these metadata-only versions into `_state/metadata_only_deferred.jsonl`
  with `records_deferred`, keeping invalid empty rows out of the validated
  corpus while preserving evidence for redundancy triage.
- **2026-07-02 repair run**: PR #75 merged as `63418d9`; run `28558440077`
  reran batches 0043-0047 and succeeded. The merged review was `ok=true` with
  873 validated records, 0 failed records, 0 missing text/XML risk indicators,
  and 1,981 deferred metadata-only records. Track 07 is validated through batch
  0048, and the scheduler is retargeted to start at batch 0049.
- **2026-07-02 batch 0049 probe**: run `28559818771` succeeded for batch 0049.
  The merged review was `ok=true` with 1,177 validated records, 0 failed
  records, 0 deferred records, and 0 missing text/XML risk indicators. Track 07
  is validated through batch 0049, and the scheduler is retargeted to start at
  batch 0050.
- **2026-07-02 batches 0050-0051 probes**: run `28561731954` succeeded for
  batch 0050. Run `28563126811` first validated batch 0051 records but failed
  merge review on one deterministic 404 retrieval gap for
  `secondary-legislation_pco-drafted_2001_007_en_2007-09-03`. PR #78 merged the
  `download_source_not_found` deferral repair, and repair rerun `28564452205`
  succeeded. The merged review was `ok=true` with 1,181 validated records,
  1 deferred metadata retrieval gap, 0 failed records, and 0 missing text/XML
  risk indicators. Track 07 is validated through batch 0051, and the scheduler
  is retargeted to start at batch 0052.
- **2026-07-02 batch 0052 probe**: run `28566570973` succeeded for batch 0052.
  The merged review was `ok=true` with 1,170 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,075 versions checked,
  1,075 records added, and 10 Parquet files written. Track 07 is validated
  through batch 0052, and the scheduler is retargeted to start at batch 0053.
- **2026-07-02 batch 0053 probe**: run `28568946847` succeeded for batch 0053.
  The merged review was `ok=true` with 1,213 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,118 versions checked,
  1,118 records added, and 10 Parquet files written. Track 07 is validated
  through batch 0053, and the scheduler is retargeted to start at batch 0054.
- **2026-07-02 batch 0054 probe**: run `28571640868` succeeded for batch 0054.
  The merged review was `ok=true` with 1,180 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,085 versions checked,
  1,085 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0054, and the scheduler is retargeted to start at batch 0055.
- **2026-07-02 batch 0055 probe**: run `28574778367` succeeded for batch 0055.
  The merged review was `ok=true` with 1,164 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,069 versions checked,
  1,069 records added, and 10 Parquet files written. Track 07 is validated
  through batch 0055, and the scheduler is retargeted to start at batch 0056.
- **2026-07-02 batch 0056 probe**: run `28577774075` succeeded for batch 0056.
  The merged review was `ok=true` with 1,200 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,105 versions checked,
  1,105 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0056, and the scheduler is retargeted to start at batch 0057.
- **2026-07-02 batch 0057 probe**: run `28581048704` succeeded for batch 0057.
  The merged review was `ok=true` with 1,191 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,096 versions checked,
  1,096 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0057, and the scheduler is retargeted to start at batch 0058.
- **2026-07-02 batch 0058 probe**: run `28584537830` succeeded for batch 0058.
  The merged review was `ok=true` with 1,100 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 1,005 versions checked,
  1,005 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0058, and the scheduler is retargeted to start at batch 0059.
- **2026-07-02 batch 0059 probe**: run `28587801975` succeeded for batch 0059.
  The merged review was `ok=true` with 1,054 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 959 versions checked,
  959 records added, and 10 Parquet files written. Track 07 is validated
  through batch 0059.
- **2026-07-02 batch 0060 probe**: run `28588847327` succeeded for batch 0060.
  The merged review was `ok=true` with 1,074 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 979 versions checked,
  979 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0060, and the scheduler is retargeted to start at batch 0061.
- **2026-07-03 batch 0061 probe**: run `28593549021` succeeded for batch 0061.
  The merged review was `ok=true` with 1,034 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 939 versions checked,
  939 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0061, and the scheduler is retargeted to start at batch 0062.
- **2026-07-03 batch 0062 probe**: run `28598279801` succeeded for batch 0062.
  The merged review was `ok=true` with 1,061 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 500 works checked, 966 versions checked,
  966 records added, and 10 Parquet files written. Track 07 is validated
  through batch 0062, and the scheduler is retargeted to start at batch 0063.
- **2026-07-03 batches 0063-0067 probe**: run `28606962250` completed
  successfully on `main` with `max_parallel=3`. The merged review was
  `ok=true` with 4,257 validated records, 0 failed records, 0 deferred
  records, 0 warnings, and 0 missing text/XML risk indicators. Sync state
  recorded 2,500 works checked, 4,162 versions checked, 4,162 records added,
  and 48 Parquet files written across the five downloaded batch artifacts.
  Track 07 is validated through batch 0067, and the scheduler is retargeted
  to start at batch 0068.
- **2026-07-03 batch 0068 probe**: run `28635745595` succeeded for batch 0068.
  The merged review was `ok=true` with 298 validated records, 0 failed
  records, 0 deferred records, 0 warnings, and 0 missing text/XML risk
  indicators. Sync state recorded 193 works checked, 203 versions checked,
  203 records added, and 9 Parquet files written. Track 07 is validated
  through batch 0068. No further batches remain in the current full bootstrap.

## Track 08 - Full Hugging Face Corpus Upload

Status: `ready`

Goal: publish the full validated corpus to Hugging Face as the live operational dataset.

Actions:

- Confirm `HF_XET_HIGH_PERFORMANCE=1` for the upload environment.
- Run `uv run nzlc hf-upload`.
- Use resumable upload behavior if the upload is interrupted.
- Verify Hugging Face contains `parquet/`, `raw_xml/`, `records.jsonl`, `manifests/`, and `_state/` as expected.
- Re-download the dataset into a clean location and compare manifest hashes.
- Confirm the dataset card states the discovery and coverage status accurately.

Acceptance criteria:

- Full corpus upload completes.
- Re-downloaded manifest matches the uploaded manifest.
- Dataset card and README do not overclaim completeness.

Evidence to record:

- Hugging Face revision or commit hash.
- Uploaded size.
- Manifest hash.
- Re-download verification result.

Current blocker:

- A live partial/API-discovery Hugging Face dataset exists, but the full
  validated corpus has not been produced.
- Track 07 has not produced the full bootstrap corpus yet.
- The upload helper defaults `HF_XET_HIGH_PERFORMANCE=1` during upload.
- Full-corpus upload workflow is now present in
  `.github/workflows/full_corpus_hf_upload.yml`.
- Full corpus operations runbook is now documented in
  `docs/full_corpus_operations.md`.
- **2026-06-21 publication guard hardening**:
  `full_corpus_hf_upload.yml` now downloads Track 07 bootstrap artifacts into
  the workspace root to preserve the `data/` tree, fails closed when
  `upload_confirmed=true` is requested without `bootstrap_run_id`, runs
  `nzlc review-full-corpus-bootstrap --artifact-root data` before any confirmed
  `nzlc hf-upload`, and includes the generated review report in the pre-upload
  review artifact. Focused tests, Ruff, and `actionlint` passed.
- Remaining live upload tasks still depend on Track 07 run `27898963687`
  completing and producing a reviewed full-corpus artifact.

## Track 09 - GitHub Scheduled Hugging Face Sync

Status: `ready`

Goal: make GitHub Actions the normal maintenance loop for the Hugging Face live corpus.

Actions:

- Confirm `.github/workflows/hf_sync.yml` exists on the default branch.
- Configure GitHub secrets and variables from Track 02.
- Run workflow manually with `max_works=5` and `min_seconds_between_requests=1.0`.
- Run workflow manually without `max_works` only after Track 07 and Track 08 are proven.
- Confirm scheduled daily runs restore Hugging Face state before syncing.
- Confirm workflow uploads only changed content.
- Confirm GitHub Actions summary includes sync state and latest changes.

Acceptance criteria:

- Manual smoke workflow passes.
- Full manual workflow passes.
- Daily scheduled workflow is enabled and uses the Hugging Face repo as the live data hub.

Evidence to record:

- GitHub Actions run URLs.
- Workflow inputs used.
- Latest successful scheduled run URL.

Current evidence and remaining blocker:

- `.github/workflows/hf_sync.yml` exists locally and includes schedule, manual dispatch inputs, Hugging Face restore, sync, upload, and step-summary sections.
- The GitHub repository and required secrets/variables exist.
- Manual live sync and no-change upload proof passed for the approved
  partial/API-discovery launch.
- The scheduled-run launch gate was explicitly waived by the repository owner on
  2026-06-09 after the first post-fix scheduled event did not dispatch.
- Full and recurring maintenance proof remains blocked until Tracks 04, 07, and
  08 establish a full seed and full validated corpus.
- **2026-06-21 scheduled maintenance guard hardening**:
  `hf_sync.yml` now fails closed when Hugging Face restore fails, preventing a
  scheduled maintenance run from uploading an empty or partial local state after
  restore errors. Routine runs also upload `hf-sync-maintenance-evidence`
  containing `sync_state.json`, `latest_changes.json`, `latest_manifest.json`,
  and `coverage_report.json` for post-run review. Focused tests, Ruff, and
  `actionlint` passed.

## Track 10 - Maintenance Doctor And Alerting

Status: `done`

Goal: surface token, API, and dependency failures before they affect the live corpus.

Actions:

- Enable `.github/workflows/doctor.yml`.
- Confirm doctor runs without mutating corpus data.
- Confirm GitHub Actions notifications reach the maintainer.
- Decide whether to add a lightweight webhook or issue creation on repeated failures.
- Review Dependabot configuration and security workflows.

Acceptance criteria:

- Doctor workflow passes once with live secrets.
- Failure notification path is known.
- Maintainer has a weekly check routine.

Evidence to record:

- Doctor workflow run URL.
- Notification destination.
- Any follow-up alerting issue.

Current evidence:

- `.github/workflows/doctor.yml` exists and is scheduled weekly.
- Local non-network `uv run --no-cache nzlc doctor` runs without creating
  `data/`.
- Live secret/variable configuration exists; continuing evidence should be
  recorded through future weekly doctor runs.
- Dependabot, CodeQL, and OpenSSF Scorecard configurations exist locally.
- Doctor workflow passed with live secrets: run `27125139848` (2026-06-08) and
  run `27362180628` (2026-06-11) both succeeded.
- Notification path: GitHub Actions default email notifications to repository
  watchers on scheduled workflow failure. Weekly check routine documented in
  `docs/maintenance_runbook.md`.

## Track 11 - Monthly Full Reconciliation

Status: `ready`

Goal: keep the corpus complete over time, not only during the first bootstrap.

Actions:

- Define a monthly or quarterly full reconciliation cadence.
- Compare seed inventory, search discovery, and coverage report outputs.
- Add newly discovered work IDs to `seeds/work_ids.txt` with provenance.
- Rerun full sync in staged batches when the seed file changes materially.
- Review counts by legislation type, status, and year.

Acceptance criteria:

- Reconciliation cadence is documented.
- Seed changes are reviewed.
- Coverage deltas are explained in `latest_changes.json` or a maintenance note.

Evidence to record:

- Reconciliation date.
- Added or removed work IDs.
- Coverage deltas.

Current blocker:

- `docs/reconciliation_runbook.md` now documents the monthly cadence and procedure.
- `seeds/work_ids.txt` is absent, so seed changes cannot be reviewed or applied.
- `data/manifests/coverage_report.json` is absent, so coverage deltas cannot be compared.
- Track 04 has produced the search-derived `seeds/work_ids.txt` operational
  baseline. Full reconciliation evidence still depends on Track 07 completing
  the reviewed full bootstrap, Track 08 publishing the reviewed full corpus,
  and Track 09 proving the recurring maintenance loop.
- Candidate seed reconciliation is now available through `nzlc reconcile-work-ids`
  and `.github/workflows/historical_seed_reconciliation.yml`.
- Monthly full reconciliation automation is now also present in
  `.github/workflows/monthly_full_reconciliation.yml` for the broader full-corpus
  maintenance lane.
- Full corpus operations runbook is now documented in
  `docs/full_corpus_operations.md`.
- **2026-06-21 reconciliation publication guard hardening**:
  `monthly_full_reconciliation.yml` now uses safe scheduled-run defaults for
  baseline seed, request pacing, max works, and disk budget when manual inputs
  are absent. Confirmed Hugging Face publication fails closed in this workflow;
  reconciliation can produce review artifacts and optional full-sync outputs,
  but live publication must use Track 08 after review. Focused tests, Ruff, and
  `actionlint` passed.

## Track 12 - Zenodo Sandbox Archive

Status: `done`

Goal: prove annual immutable archiving without publishing to production.

Actions:

- Set Zenodo sandbox token and sandbox API URL.
- Run `uv run nzlc archive --year <year> --output-dir dist/archive`.
- Run `uv run nzlc zenodo-upload --year <year> --archive-dir dist/archive` against sandbox.
- Verify archive manifest and checksums.
- Verify duplicate-file replacement behavior if rerun.

Acceptance criteria:

- Sandbox draft is created or updated.
- Archive, manifest, and checksum files are present.
- No production publication occurs.

Evidence to record:

- Sandbox deposition URL.
- Archive filename and checksum.
- Workflow run URL if performed in GitHub Actions.

Current evidence:

- Production Zenodo path was proven and published for the approved partial
  launch, superseding the original sandbox-only blocker.
- Published record: `https://zenodo.org/records/20592540`.
- DOI: `10.5281/zenodo.20592540`.
- Concept DOI: `10.5281/zenodo.20592539`.

## Track 13 - Protected Production Zenodo Archive

Status: `done`

Goal: publish annual DOI snapshots only after explicit approval.

Actions:

- Configure `zenodo-production` GitHub environment with required reviewers.
- Confirm production `ZENODO_TOKEN` is environment-scoped.
- Run annual workflow with `publish=false` first.
- Review production draft metadata, license, creators, related identifiers, and files.
- Publish only after reviewer approval and explicit `publish=true`.
- Record DOI in `CITATION.cff`, `DATASET_CARD.md`, and Hugging Face dataset card.

Acceptance criteria:

- Production draft path is proven.
- Publication requires approval.
- DOI is recorded after publication.

Evidence to record:

- Production deposition URL.
- DOI.
- Commit updating citation files.

Current evidence:

- Production Zenodo archive published for the approved partial launch:
  `https://zenodo.org/records/20592540`.
- DOI: `10.5281/zenodo.20592540`.
- Workflow evidence:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27132519663`.
- The Zenodo related identifier now points to
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Published archive filenames remain immutable and still include the old launch
  prefix.

## Track 14 - Legal, Citation, And Dataset Wording

Status: `done`

Goal: keep public statements accurate about corpus coverage, licensing, and incorporated-by-reference material.

Actions:

- Review `README.md`, `DATASET_CARD.md`, `CITATION.cff`, and archive metadata.
- State whether discovery is complete, partial, seed-based, or search-based.
- Separate code license from legislation reuse status.
- Add caveats for incorporated-by-reference material and non-legislative website content.
- Confirm citation guidance for Hugging Face live data and Zenodo annual snapshots.

Acceptance criteria:

- Public docs make no unsupported completeness claim.
- License and citation wording are internally consistent.
- Zenodo and Hugging Face metadata align.

Evidence to record:

- Reviewed files.
- Reviewer notes.
- Metadata commit SHA.

Current evidence:

- Reviewed `README.md`, `DATASET_CARD.md`, `CITATION.cff`, and Hugging Face dataset-card generation in `scripts/init_huggingface_dataset.py`.
- Public wording now states coverage is not proven complete, separates code licensing from source-content reuse status, and distinguishes live Hugging Face citation from fixed Zenodo citation.
- Official NZ Legislation copyright/disclosure pages checked on 2026-06-07 support Crown copyright / Creative Commons attribution wording, with separate caution retained for third-party or non-legislative material.
- Live Hugging Face and Zenodo metadata were verified for the approved
  partial/API-discovery launch and post-launch rename.
- Full-coverage wording remains prohibited until Track 04 is closed.

## Track 15 - Downstream Researcher Usability

Status: `done`

Goal: make the published corpus easy to inspect and query after the live hub is stable.

Actions:

- Add a small public sample split if useful for users who do not want the full corpus.
- Add DuckDB or Polars examples that query Parquet directly from Hugging Face.
- Add a minimal data dictionary from schema fields.
- Optionally add a Hugging Face Space for browsing/search after core maintenance is stable.

Acceptance criteria:

- A new user can query the Parquet dataset without downloading the full raw corpus.
- Examples are tested or manually verified.
- Optional browser UI is clearly secondary to the dataset pipeline.

Evidence to record:

- Example command output.
- Sample dataset path or revision.
- Documentation links.

Current evidence:

- Added `docs/researcher_quickstart.md` with DuckDB `hf://` examples, local PyArrow examples, and sample split policy.
- Added `docs/data_dictionary.md` from `schemas/legislation_record.schema.json`.
- `README.md` and `DATASET_CARD.md` now link to downstream researcher documentation.
- Examples verified on 2026-06-11:
  - DuckDB `hf://` queries return 9 records from live dataset.
  - PyArrow example fixed to avoid pandas dependency; verified with local smoke fixture.
  - Local smoke fixture + validate commands produce viable Parquet output.
- Sample split deferred until full corpus publication (Track 08).
- Hugging Face Space deferred until pipeline and live hub are stable.

## Track 16 - GitHub Repository Hardening

Status: `done`

Goal: make the GitHub repository safe to operate as the automation controller for the live Hugging Face corpus.

Actions:

- Create or confirm the final GitHub repository. Blocked: no Git remote is configured.
- Push the code-only repository without `data/`, `dist/`, cache directories, or generated corpus files. Blocked until the final GitHub repository exists.
- Enable branch protection on the default branch. Blocked until the final GitHub repository exists.
- Require the tests workflow before merge once CI is stable. Blocked until branch protection/rulesets can be applied on GitHub.
- Enable secret scanning and push protection where available. Blocked until GitHub repository settings are available.
- Enable Dependabot alerts and dependency update PRs. Dependency update PR configuration is present in `.github/dependabot.yml`; live alert enablement is scripted but blocked until GitHub repository settings are available.
- Confirm `CODEOWNERS`, issue templates, pull request template, security policy, and contribution docs are present if the repo is public. Done locally.
- Confirm workflows have minimum permissions and do not expose secrets in logs. Done locally.

Acceptance criteria:

- Default branch is protected.
- Tests are required for code changes.
- Secret scanning and dependency alerts are enabled or explicitly documented as unavailable.
- Repository remains code-only.

Evidence to record:

- GitHub repository URL.
- Branch protection summary.
- Enabled security settings.
- First passing CI run URL.

Current evidence:

- GitHub repository URL: `https://github.com/edithatogo/corpus-legislation-nz`.
- Branch protection summary: `main` requires strict `tests`, one approving review, admin enforcement, linear history, no force pushes, and no deletions.
- Enabled security settings: Dependabot security updates, secret scanning, and push protection.
- First passing CI run: baseline `Tests` run `27087158077` and `CodeQL` run `27087158073` passed on 2026-06-07.
- `.gitignore` excludes generated corpus/archive/cache paths including `data/`, `dist/`, `.hf_cache/`, and `.track15-smoke/`; no tracked files exist under generated corpus/archive paths.
- `SECURITY.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, pull request template, issue templates, Dependabot config, CodeQL, Scorecard, tests, doctor, Hugging Face sync, and annual Zenodo workflows are present.
- Workflow permissions are minimum-scoped for local review: `contents: read` by default, with `security-events: write` only where `codeql.yml` and `scorecard.yml` upload SARIF.

## Track 17 - Runtime Capacity, Batching, And Resume

Status: `done`

Goal: make the full corpus bootstrap and recurring sync practical under local disk, GitHub Actions runtime, API rate limits, and upload interruption constraints.

Actions:

- Estimate disk required for raw files, normalized records, Parquet, manifests, and annual archive staging. Done in `docs/runtime_capacity_runbook.md`.
- Decide whether first full bootstrap runs locally, on GitHub Actions, or on another controlled runner. Done: first full bootstrap should run on a controlled local or self-hosted runner.
- Define batch size and pacing defaults for first full sync. Done in `docs/runtime_capacity_runbook.md`.
- Confirm sync state is preserved between batches. Done with `tests/test_sync_resume.py`.
- Confirm interrupted Hugging Face uploads can resume without corrupting the remote dataset. `hf upload-large-folder` is resumable by design; no-change manifest check prevents redundant uploads; sync resume tested.
- Add an operator note for cleaning local generated data safely after upload and verification. Done in `docs/runtime_capacity_runbook.md`.
- Record the fallback plan if the full bootstrap exceeds GitHub Actions timeout. Done in `docs/runtime_capacity_runbook.md`.

Acceptance criteria:

- Bootstrap runner and disk budget are documented.
- Batch/resume procedure is written and tested with a non-trivial batch.
- Generated local data cleanup is documented and does not affect Git-tracked files.

Evidence to record:

- Disk estimate.
- Chosen runner.
- Batch size and pacing values.
- Resume test result.

Current evidence:

- Disk estimate documented in `docs/runtime_capacity_runbook.md`: reserve at least 25 GB free for the expected 6 GB class corpus, preferably 50 GB when archive staging or embeddings share the runner.
- Chosen runner documented: controlled local or self-hosted first bootstrap, then GitHub Actions for daily/latest maintenance after first verified upload.
- Batch defaults documented: 5-work smoke at 1.0 seconds pacing, 50-work pilot at 1.0 seconds, 250-work seed chunks at 0.5 seconds, and 500-1000 work chunks at 0.2 seconds only after throttle-free earlier batches.
- Sync resume behavior tested in `tests/test_sync_resume.py` (2 tests pass).
- Hugging Face upload resume uses `hf upload-large-folder` (resumable) with
  no-change manifest check, documented in `docs/runtime_capacity_runbook.md`.
- Historical bootstrap publication proved the manual upload path at 500-work
  scale. Full-corpus capacity remains to be measured once the authoritative seed
  is available.
- Period-sharded bootstrap and agent handoff is now split into Track 36. Track
  17 remains the runtime/batching foundation; Track 36 owns period policy,
  annual recent shards, checkpoint artifacts, and handoff status.

## Track 18 - Data Quality And Schema Governance

Status: `blocked`

Goal: prevent silent schema drift or degraded corpus quality after the first public upload.

Actions:

- Define minimum validation checks required before upload. Done.
- Define which validation warnings block upload and which are informational. Done.
- Add or confirm fixture coverage for representative XML, HTML, missing-text, missing-format, and ephemeral-ID cases. Done.
- Version the record schema explicitly before public release. Done: `record_schema_version = "1.0"`.
- Document how schema changes are migrated or announced. Done in `docs/schema_governance.md`.
- Track data-quality metrics from `coverage_report.json` over time. Done via `data/manifests/coverage_history.jsonl`.

Acceptance criteria:

- Upload cannot proceed after blocking validation failures.
- Schema version is visible in records or manifests.
- Coverage metrics can be compared between runs.
- Public docs explain backward compatibility expectations.

Evidence to record:

- Schema version.
- Validation report path.
- Fixture list.
- Coverage baseline.

Current evidence:

- Schema version: `record_schema_version = "1.0"`.
- Validation report path: `data/manifests/validation_report.json`.
- Fixture list: `tests/fixtures/sample_legislation.xml`, `tests/fixtures/sample_legislation.html`, plus validation tests for missing text, missing XML URL, missing source format/metadata-only content, and ephemeral identifiers.
- Coverage metrics are written to `data/manifests/coverage_report.json` and appended to `data/manifests/coverage_history.jsonl`.
- Period checkpoint review reports now emit `period_quality` when a period
  context file is present, carrying the period ID, source work-ID count,
  produced record count, validation status, manifest hash, failed-version
  count, and the same missing text/XML URL and ephemeral identifier indicators
  used for full-corpus coverage.
- Live coverage baseline remains blocked until Track 07/08 produce and publish the real corpus.

## Track 19 - Public Launch Decision

Status: `done`

Goal: make a deliberate launch decision after the corpus, automation, metadata, and maintenance loop are all proven.

Actions:

- Confirm Tracks 01 through 14 are done or explicitly waived. Blocked: Tracks 02-14 still have unresolved blockers.
- Confirm Hugging Face contains the full intended live corpus or clearly labels the dataset as partial. Blocked until Track 03/08 publish or confirm the live dataset.
- Confirm GitHub scheduled sync is enabled and has passed after the first upload. Blocked until Track 09 runs on a configured GitHub repository.
- Confirm Zenodo sandbox archive has passed. Blocked until Track 12 passes.
- Confirm public README, dataset card, and citation files match the actual coverage state. Done for current prelaunch state.
- Create a release note summarizing coverage, caveats, update cadence, and archival plan. Done as draft template.

Acceptance criteria:

- Public users can find the live dataset, source repository, coverage statement, and citation instructions.
- No public page claims full coverage unless Track 04 is proven.
- Maintainer has a clear monthly and annual operating checklist.

Evidence to record:

- Launch date.
- Hugging Face revision.
- GitHub release or tag.
- Final launch checklist.

Current evidence:

- Launch date: 2026-06-09; current decision is launch approved for the
  intentional partial/API-discovery dataset.
- Hugging Face revision:
  `6b082e2f85802cb374898d689d264017a047799b` after the post-launch rename and
  card update. Launch upload revision:
  `8d48d807c5c8da73f8ad164734245d9ea73046f3`.
- GitHub release or tag: `v0.1.0-partial.20260609`,
  `https://github.com/edithatogo/corpus-legislation-nz/releases/tag/v0.1.0-partial.20260609`.
- Final launch checklist: `docs/public_launch_decision.md`.
- Draft release note: `docs/public_launch_release_note.md`.
- Launch tracking issues #10 through #15 are closed.

## Track 20 - GitHub Release Tag For Partial Launch

Status: `done`

Goal: create a GitHub release and tag for the approved intentional partial/API-discovery launch.

Actions:

- Confirm `docs/public_launch_decision.md` records launch approval and the scheduled-run waiver.
- Choose a release tag, for example `v0.1.0-partial.20260609`.
- Create a GitHub release on `main` for the partial/API-discovery dataset launch.
- Update `docs/public_launch_decision.md` so `GitHub release or tag` records the real tag.
- Confirm release notes do not claim full New Zealand legislation coverage.

Acceptance criteria:

- A GitHub release/tag exists for the approved partial launch.
- Launch docs record the release/tag.
- Public wording remains clear that the dataset is partial/API-discovery based.

Evidence to record:

- GitHub release URL:
  `https://github.com/edithatogo/corpus-legislation-nz/releases/tag/v0.1.0-partial.20260609`.
- Tag name and commit SHA: `v0.1.0-partial.20260609` at
  `3196fb415276e1d1e8edd3c394ddeac30d4485a9`.
- Commit updating launch docs: this implementation branch records the release
  URL in `docs/public_launch_decision.md`.

## Track 21 - Separate Historical Hugging Face Corpus

Status: `done`

Goal: prepare historical corpus publication as a separate Hugging Face dataset, following the Hansard-style separation pattern and avoiding overwrite of the live six-record dataset.

Actions:

- Use the separate Hugging Face dataset target `edithatogo/corpus-legislation-nz-historical`.
- Document that `edithatogo/corpus-legislation-nz` remains the live partial/API-discovery dataset.
- Confirm or create the historical Hugging Face dataset shell with root-level layout.
- Configure a separate repository variable such as `HF_HISTORICAL_REPO_ID`.
- Ensure historical pilots and uploads cannot write to `HF_REPO_ID` unless explicitly intended.

Acceptance criteria:

- Historical publication target is documented and separate from the live dataset.
- Historical dataset shell exists or has a precise creation runbook.
- Repository variables/secrets distinguish live and historical upload targets.

Evidence to record:

- Historical Hugging Face dataset URL.
- Root layout or creation command output.
- GitHub variable names, not secret values.

Completion evidence:

- Historical target documented as `edithatogo/corpus-legislation-nz-historical`.
- Live target `edithatogo/corpus-legislation-nz` remains the partial/API-discovery corpus and must not be overwritten.
- GitHub variable contract documented as `HF_HISTORICAL_REPO_ID=edithatogo/corpus-legislation-nz-historical`.

## Track 22 - Historical Bootstrap Review Plan

Status: `done`

Goal: turn the historical pilot into a reviewed bootstrap plan before any historical publication workflow is enabled.

Actions:

- Retrieve the latest `historical-sync-pilot` artifact produced by a
  `historical_sync_pilot.yml` workflow run.
- Review `generated/historical-work-ids.provenance.json`.
- Review `data-historical-pilot/manifests/latest_manifest.json`.
- Review `data-historical-pilot/manifests/coverage_report.json`.
- Review `data-historical-pilot/_state/sync_state.json`, including failed-version state.
- Define batch sizes, pacing, resume checkpoints, and stop conditions for the historical bootstrap.
- Record the chosen publication target from Track 21.

Acceptance criteria:

- Pilot artifact evidence is reviewed and summarized.
- Failed versions and coverage caveats are documented.
- Batch plan and publication target are approved before upload code is added.

Evidence to record:

- Pilot workflow run URL and artifact name:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27138352849`,
  artifact `historical-sync-pilot`.
- Work ID count, record count, manifest hash, and coverage summary: reviewed in
  `docs/historical_bootstrap_review.md`; 10 work IDs, 52 validated records,
  manifest SHA-256
  `3a6e6abdccaa6a8124fece672a708a8f6e61389cd32b575ccc13367a5d23b0ae`.
- Failed-version summary: `records_failed: 0`, warnings empty, 52 version hash
  entries available for resume.
- Batch plan and historical Hugging Face target: documented in
  `docs/historical_bootstrap_review.md`; target
  `edithatogo/corpus-legislation-nz-historical`.

## Track 23 - Manual Historical Upload Workflow

Status: `done`

Goal: add a disabled/manual historical upload workflow only after the historical target and bootstrap plan are explicit.

Actions:

- Wait for Track 21 to define the separate historical Hugging Face target.
- Wait for Track 22 to approve pilot evidence, batch sizes, and publication policy.
- Add a manual-only workflow separate from `hf_sync.yml`.
- Require an explicit `HF_HISTORICAL_REPO_ID` repository variable or workflow input.
- Fail closed if `HF_HISTORICAL_REPO_ID` is absent or equals `HF_REPO_ID`.
- Keep historical upload disabled for schedules unless a later track deliberately enables maintenance automation.
- Default to dry-run/no-upload behavior until the historical target and batch plan are approved.
- Add guardrails preventing writes to the live `HF_REPO_ID` by default.

Acceptance criteria:

- Historical upload workflow is manual-only and separate from live sync.
- Workflow fails closed unless the historical target is explicitly configured.
- Workflow rejects `HF_HISTORICAL_REPO_ID=HF_REPO_ID`.
- Workflow has no scheduled trigger.
- Dry-run/no-upload behavior is documented for first proof runs.
- Documentation states that historical outputs must not overwrite the live dataset.

Evidence to record:

- Pull request URL adding the workflow.
- Dry-run or no-upload workflow run URL.
- First reviewed historical upload run URL, only after Track 21 and Track 22 pass.

Remaining external evidence:

- First reviewed historical upload run URL remains intentionally pending until
  historical target and batch-plan review are approved.

Current evidence:

- `docs/HUGGINGFACE_SETUP.md` records the manual historical upload contract:
  distinct `HF_HISTORICAL_REPO_ID`, fail-closed target checks, no schedule, and
  dry-run/no-upload first proof.
- `docs/historical_publication_policy.md` records the publication guardrails
  that protect the live `HF_REPO_ID` dataset from historical writes by default.
- `.github/workflows/historical_hf_upload.yml` adds a separate manual-only
  workflow with `workflow_dispatch`, fail-closed `HF_HISTORICAL_REPO_ID`
  checks, dry-run artifacts, and an upload step gated by
  `upload_confirmed=true`.
- `.github/workflows/historical_batch_review.yml` adds a GitHub-hosted
  reviewed batch fan-out path for parallel no-upload validation while keeping
  confirmed historical uploads on the serial workflow.
- `scripts/historical_workflow_helpers.py` centralizes the historical target
  guard, reviewed-seed provenance, and publication-policy metadata used by the
  shell initializer, serial upload workflow, and batch review workflow.
- Dry-run/no-upload proof passed:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27194196559`.
  The upload step was skipped because `upload_confirmed=false`, and dry-run
  artifacts were uploaded.
- `conductor/tracks/track_23_manual_historical_upload_workflow/spec.md`
  records the workflow contract.
- `conductor/tracks/track_23_manual_historical_upload_workflow/plan.md`
  records the implementation and local verification state.
- Historical completeness planning now uses `nzlc reconcile-work-ids`,
  `.github/workflows/historical_seed_reconciliation.yml`, and
  `docs/historical_completeness_plan.md` before any full-seed promotion.

## Track 24 - Corpus Family Naming And Publication Alignment

Status: `done`

Goal: adopt `corpus-nz-legislation` as the preferred systematic label and align GitHub, Hugging Face, Zenodo, OSF, and future metadata environments with sibling `corpus-nz-hansard`.

Actions:

- Record naming preference in Conductor setup and corpus-family docs.
- Audit GitHub, Hugging Face, Zenodo, OSF, and future metadata environments.
- Cross-reference `C:\Users\60217257\OneDrive - Flinders\repos\corpus-nz-hansard`.
- Preserve existing public URLs until a migration plan protects citations and redirects.

Acceptance criteria:

- Requirements, design, Mermaid diagrams, and environment tasks exist.
- Track directory contains spec and plan.
- Public-surface alignment includes GitHub, Hugging Face, Zenodo, OSF, and future metadata.

Link: `conductor/tracks/track_24_corpus_family_naming_and_publication_alignment/`

Evidence:

- Naming/publication decision:
  `docs/naming_publication_alignment.md`.
- Requirements/design docs:
  `docs/corpus-family-requirements-moscow.md` and
  `docs/corpus-family-design.md`.
- Public-surface evidence:
  `docs/public_surface_evidence_ledger.md`.
- README and dataset card now state the preferred `corpus-nz-legislation`
  family label, current `corpus-legislation-nz` publication line, and sibling
  `corpus-nz-hansard`.
- Migration or reservation of `corpus-nz-legislation` remains deferred to Track
  28.

## Track 25 - Cross Corpus Interoperability And Metadata

Status: `done`

Goal: adopt applicable Hansard interoperability and SOTA metadata roadmap patterns for legislation researcher artifacts and metadata endpoints.

Actions:

- Review Hansard search/RAG, RDF, Akoma Ntoso, and metadata endpoint tracks.
- Define optional legislation DuckDB/search/RAG and metadata artifacts.
- Keep derived artifacts validated, versioned, and optional.

Acceptance criteria:

- Roadmap covers DuckDB/search/RAG, Croissant, RO-Crate, Frictionless, DCAT/PROV-O, and Akoma Ntoso considerations.
- Track directory contains spec and plan.
- No base dependency expansion happens without a future implementation track.

Link: `conductor/tracks/track_25_cross_corpus_interoperability_and_metadata/`

Evidence:

- Hansard interoperability mapping:
  `docs/cross_corpus_interoperability_hansard.md`.
- Corpus-family design and researcher quickstart now reference the optional
  interoperability artifact contract.
- Hansard reference checkout:
  `C:\Users\60217257\OneDrive - Flinders\repos\corpus-nz-hansard`.
- Derived artifacts remain optional, generated, versioned, validated, and
  dependency-neutral until future implementation tracks scope them.

## track 26 public surface audit evidence

Status: `done`

Goal: Create an evidence ledger for GitHub, Hugging Face, Zenodo, OSF, and future metadata surfaces.

Link: `conductor/tracks/track_26_public_surface_audit_evidence/`

Evidence:

- Ledger: `docs/public_surface_evidence_ledger.md`.
- GitHub public repo, release/tag, branch protection, variables, secret names,
  and recent workflow runs recorded.
- Hugging Face live, historical, and legacy/redirect surfaces recorded.
- Zenodo record, DOI, related identifier, file list, and immutable filename
  caveat recorded.
- OSF and future metadata surfaces recorded as inactive/pending policy.


## track 27 zenodo rights metadata and zenodraft workflow

Status: `done`

Goal: Harmonise Zenodo rights metadata and migrate/evaluate draft operations through zenodraft.

Link: `conductor/tracks/track_27_zenodo_rights_metadata_and_zenodraft_workflow/`

Evidence:

- Rights and workflow decision:
  `docs/zenodo_rights_metadata_zenodraft.md`.
- Zenodo metadata example:
  `docs/zenodo/zenodo-2026-metadata.example.json`.
- Notice file:
  `NOTICE.md`.
- `zenodraft` was evaluated locally with Node `v24.15.0`, npm `11.12.1`, and
  `npx --yes zenodraft --help`.
- Metadata validation passed with
  `npx --yes zenodraft metadata validate docs/zenodo/zenodo-2026-metadata.example.json`.
- The annual Zenodo workflow remains draft-first by default, with future
  `zenodraft` token mapping documented and production publish still protected.


## track 28 github repository name migration assessment

Status: `done`

Goal: Assess safe migration or reservation of the preferred corpus-nz-legislation GitHub name.

Link: `conductor/tracks/track_28_github_repository_name_migration_assessment/`

Evidence:

- Assessment document:
  `docs/github_repository_name_migration_assessment.md`.
- Current live GitHub repository remains
  `https://github.com/edithatogo/corpus-legislation-nz`.
- Preferred target `edithatogo/corpus-nz-legislation` was not found or not
  accessible through `gh repo view` at the Track 28 check point.
- Decision: do not rename the live repository in this track; reserve the
  preferred name as a pointer repository first, then treat any full rename as a
  release operation with post-rename verification.


## track 29 shared nz corpus core schema

Status: `done`

Goal: Define shared core fields and compatibility expectations across legislation and Hansard.

Link: `conductor/tracks/track_29_shared_nz_corpus_core_schema/`

Evidence:

- Shared core schema documentation:
  `docs/shared_nz_corpus_core_schema.md`.
- Machine-readable schema:
  `schemas/shared_nz_corpus_core.schema.json`.
- Contract checker:
  `scripts/check_shared_core_schema.py`.
- Tests:
  `tests/test_shared_core_schema.py`.
- The shared schema accepts `corpus-nz-legislation` and `corpus-nz-hansard`
  while keeping corpus-specific fields in their own schemas.


## track 30 sota metadata packages

Status: `done`

Goal: Generate validated Croissant, RO-Crate, Frictionless, DCAT, and PROV-O metadata packages.

Link: `conductor/tracks/track_30_sota_metadata_packages/`

Evidence:

- Metadata package contract:
  `docs/sota_metadata_packages.md`.
- Generator and validator:
  `src/nz_legislation_corpus/metadata_packages.py`.
- CLI commands:
  `uv run nzlc metadata-packages --output-dir generated/metadata-packages`
  and
  `uv run nzlc validate-metadata-packages --metadata-dir generated/metadata-packages`.
- Tests:
  `tests/test_metadata_packages.py`.
- Generated outputs remain ignored release artifacts under `generated/` until
  an explicit release/upload/archive workflow publishes them.


## track 31 bleeding edge versioning release automation

Status: `done`

Goal: Implement SemVer/dataset/schema version governance, Release Please-style changelog automation, and consistency checks.

Link: `conductor/tracks/track_31_bleeding_edge_versioning_release_automation/`

Evidence:

- Versioning/release automation policy:
  `docs/versioning_release_automation.md`.
- Consistency checker:
  `scripts/check_version_consistency.py`.
- Tests:
  `tests/test_version_consistency.py`.
- CI enforcement:
  `.github/workflows/tests.yml` runs the version/release consistency check with
  read-only repository permissions.
- Release Please decision: deferred until publication gates and protected
  environments are proven; future automation must not publish Hugging Face or
  Zenodo records.
- Dependency-update policy keeps Renovate PRs from publishing datasets or
  Zenodo records.


## track 32 sota cicd code quality rust tooling

Status: `done`

Goal: Adopt SOTA CI/code-quality automation using Rust-backed tools where possible: uv, ruff, typos, zizmor, taplo, plus actionlint.

Link: `conductor/tracks/track_32_sota_cicd_code_quality_rust_tooling/`

Evidence:

- CI workflow:
  `.github/workflows/code_quality.yml`.
- Tooling policy:
  `docs/ci_code_quality_security_tooling.md`.
- Blocking checks now cover `uv`, `ruff check`, `ruff format --check`,
  strict `ty`, `typos`, `taplo`, and `actionlint`.
- `actionlint` found and drove the fix for
  `.github/workflows/historical_hf_upload.yml`, consolidating 12 manual inputs
  down to GitHub's 10-input `workflow_dispatch` limit.
- CodeQL, OpenSSF Scorecard, Renovate, and pre-commit adoption decisions are
  documented.
- Ruff expanded from 6 to 49 rule sets, all passing cleanly.
- pydantic v2 with `pydantic-settings.BaseSettings` adopted for all
  configuration.
- Template injection risks fixed across all 8 CI workflows; `zizmor` now
  reports zero findings.
- All 16 workflows have explicit least-privilege `permissions:` blocks.
- `uv_build` build backend adopted for Python packaging.


## track 33 artifact provenance attestations

Status: `done`

Goal: Add release evidence ledgers, GitHub artifact attestations or SLSA-style provenance, and signed/checksummed artifact policy.

Link: `conductor/tracks/track_33_artifact_provenance_attestations/`

Evidence:

- Provenance and attestation policy:
  `docs/artifact_provenance_attestations.md`.
- Release evidence JSON Schema:
  `schemas/release_evidence.schema.json`.
- Archive release evidence generator:
  `src/nz_legislation_corpus/artifact_provenance.py`.
- `nzlc archive` now emits
  `corpus-legislation-nz-YYYY.release-evidence.json` and includes it in
  `SHA256SUMS`.
- Annual Zenodo archive workflow uploads archive evidence artifacts and calls
  GitHub artifact attestation before Zenodo draft upload.
- Consistency checker and tests:
  `scripts/check_artifact_provenance.py` and
  `tests/test_artifact_provenance.py`.


## track 34 sota test infrastructure

Status: `done`

Goal: SOTA test infrastructure with hypothesis property-based tests, integration/smoke test directories, coverage baselines, and pytest markers.

Link: `conductor/tracks/track_34_sota_test_infrastructure/`

Evidence:

- 120 tests total (89 existing unit tests + 31 new hypothesis/integration/smoke tests).
- 8 hypothesis property-based tests for pure functions.
- Integration test directory: `tests/integration/` (3 cross-component tests).
- Smoke test directory: `tests/smoke/` (2 full CLI pipeline tests).
- Coverage configured with `fail_under = 60` in `pyproject.toml`.
- Pytest markers (unit, integration, smoke, hypothesis) registered and applied across all test files.

## track 35 multi-git and multi-archive mirroring setup

Status: `blocked`

Goal: Establish multi-git and multi-archive mirroring setup to prevent single-point-of-failure repository/dataset takedowns.

Link: `conductor/tracks/track_35_multi_git_and_multi_archive_mirroring_setup/`

Evidence:
- Git mirror workflow configured: `.github/workflows/mirror_sync.yml`.
- Mirror workflow locally linted with `actionlint` and hardened to skip when mirror secrets are absent.
- Zenodo and Hugging Face pipelines hardened.
- OSF optional mirror convenience policy mapped in `docs/osf-optional-mirror-policy.md` (inactive pending live setup).
- OSF policy validator added: `scripts/check_osf_optional_policy.py`.
- OSF unit tests added: `tests/test_osf_optional.py`.
- Local Phase 2 validation command: `python scripts/check_osf_optional_policy.py`.
- Local validation passed: OSF policy validators, `tests/test_osf_optional.py`, direct Ruff check, and `actionlint .github/workflows/mirror_sync.yml`.
- Mirror setup runbook added: `docs/mirror-sync-setup.md`.
- Live GitHub secret-name check on 2026-06-21 found `OSF_TOKEN` present but no
  `GIT_MIRROR_URLS`, `GIT_MIRROR_URL`, or `GIT_MIRROR_SSH_PRIVATE_KEY`.
- Live GitHub workflow-name check on 2026-06-21 did not show `Mirror Sync` on
  the default branch yet.
- Remaining Track 35 items are gated external work: push/publish
  `.github/workflows/mirror_sync.yml` to GitHub, configure mirror secrets, and
  verify manual/push mirror runs.
- 2026-07-02 live proof: `Mirror Sync` is now active on the default branch.
  Manual run `28581284768` completed successfully and took the expected guarded
  skip path because `GIT_MIRROR_URLS/GIT_MIRROR_URL` is not configured.
  `gh secret list` still shows no `GIT_MIRROR_URLS`, `GIT_MIRROR_URL`, or
  `GIT_MIRROR_SSH_PRIVATE_KEY`, so real mirror-push verification is externally
  blocked on mirror remote and SSH-key secret setup.

## track 36 period sharded bootstrap agent handoff

Status: `in_progress`

Goal: Define time-period corpus shards, recent annual shards, checkpoint
artifacts, and agent handoff rules so completed periods can be reviewed or
triaged by other agents while later periods continue to sync.

Link: `conductor/tracks/track_36_period_sharded_bootstrap_agent_handoff/`

Initial policy:

- Use coarse historical shards for older records:
  `pre_1908`, `1908_1949`, `1950_1979`, `1980_1999`.
- Use annual shards from the verified API-native/recent boundary through the
  current year.
- Keep `unknown_year_review` as an explicit shard for records whose year cannot
  be derived.
- Do not hard-code the API-native boundary from memory; verify it against repo
  evidence, official API metadata, or generated coverage evidence. If no
  authoritative boundary is available, use 2008 as a planning fallback only and
  record the uncertainty.

Evidence to create:

- Period manifest and per-period seed SHA-256 values.
- Per-period workflow checkpoint artifacts.
- Period-level review reports with validation, manifest, coverage, sync state,
  failed versions, missing text/XML URL counts, and ephemeral-ID counts.
- Conductor handoff status for each period before assigning another agent.

Implementation evidence:

- Period seed/manifest generator:
  `src/nz_legislation_corpus/period_shards.py`.
- CLI command:
  `nzlc split-work-id-periods`.
- Period checkpoint workflow:
  `.github/workflows/full_corpus_period_bootstrap.yml`.
- Period context is included in `nzlc review-full-corpus-bootstrap` reports
  when `generated/full-corpus-periods/period_context.json` is present.
- Focused tests and lint passed for period sharding, review context, CLI smoke,
  Ruff, and `actionlint`.
- 2026-07-02 local manifest generation passed with the unverified 2008 planning
  fallback boundary: all 33,693 reviewed work IDs were assigned across 24
  periods, with seed SHA-256
  `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.

Remaining:

- Verify the API-native/recent annual-shard boundary from evidence.
- Run period checkpoint workflows and create period-specific follow-up tracks
  only for completed artifacts that need independent agent review.

---

- [x] **Track: Official website fallback retrieval**
*Link: [./tracks/track_38_official_website_fallback_retrieval/](./tracks/track_38_official_website_fallback_retrieval/)*

Goal: Add a conservative, provenance-rich official-website retrieval fallback
for failed API/XML/HTML edge cases while avoiding stealth scraping or
access-control bypass.

---

- [x] **Track: NZLII redundancy reconciliation**
*Link: [./tracks/track_39_nzlii_redundancy_reconciliation/](./tracks/track_39_nzlii_redundancy_reconciliation/)*

Goal: Use NZLII as an independent secondary source for coverage checks,
candidate matching, and guarded text-rescue triage without treating it as the
canonical source.

---

- [x] **Track: Source redundancy resolver and provenance**
*Link: [./tracks/track_40_source_redundancy_resolver_provenance/](./tracks/track_40_source_redundancy_resolver_provenance/)*

Goal: Define the shared fallback resolver and provenance model across API,
feeds, official website fallback retrieval, and NZLII redundancy.

---

- [ ] **Track: Gazette source registry, rights, and shared schema**
*Link: [./tracks/track_41_gazette_source_registry_rights_shared_schema/](./tracks/track_41_gazette_source_registry_rights_shared_schema/)*

Goal: Define the NZ Gazette source registry, rights boundary, retrieval limits,
and shared raw/canonical schema for independent source archives and derived
canonical records.

---

- [ ] **Track: Official Gazette source archive**
*Link: [./tracks/track_42_official_gazette_source_archive/](./tracks/track_42_official_gazette_source_archive/)*

Goal: Archive official NZ Gazette issue PDFs and notice pages as their own
source evidence layer with raw artifacts, HTTP metadata, hashes, extraction
outputs, and provenance.

---

- [ ] **Track: DigitalNZ Gazette source archive**
*Link: [./tracks/track_43_digitalnz_gazette_source_archive/](./tracks/track_43_digitalnz_gazette_source_archive/)*

Goal: Archive DigitalNZ New Zealand Gazette records through the local `dnz`
CLI/resource repo as a separate source evidence layer for comparison and
corroboration.

---

- [ ] **Track: Victoria/LexisNexis historical Gazette archive**
*Link: [./tracks/track_44_victoria_lexisnexis_historical_gazette_archive/](./tracks/track_44_victoria_lexisnexis_historical_gazette_archive/)*

Goal: Archive Victoria/LexisNexis historical NZ Gazette index and content as a
separate rights-caveated source layer after access and rights checks.

---

- [ ] **Track: NZLII Gazette redundancy archive**
*Link: [./tracks/track_45_nzlii_gazette_redundancy_archive/](./tracks/track_45_nzlii_gazette_redundancy_archive/)*

Goal: Evaluate and archive NZLII Gazette material as a separate secondary
redundancy source if access, rights, and coverage checks permit it.

---

- [ ] **Track: Cross-source comparison and canonical Gazette builder**
*Link: [./tracks/track_46_cross_source_comparison_canonical_gazette_builder/](./tracks/track_46_cross_source_comparison_canonical_gazette_builder/)*

Goal: Build a derived, reproducible, conflict-aware canonical NZ Gazette layer
by comparing independent source archives without replacing raw source evidence.

---

- [ ] **Track: Gazette archive workflow, review, and publication staging**
*Link: [./tracks/track_47_gazette_archive_workflow_review_publication_staging/](./tracks/track_47_gazette_archive_workflow_review_publication_staging/)*

Goal: Stage workflows and review gates for source-specific Gazette archives and
the derived canonical Gazette archive, keeping publication artifact-first and
approval-gated.

---

- [ ] **Track: Gazette freshness and change detection**
*Link: [./tracks/track_48_gazette_freshness_change_detection/](./tracks/track_48_gazette_freshness_change_detection/)*

Goal: Detect new and changed NZ Gazette material across official and DigitalNZ
sources, persist freshness state, and enqueue targeted source refreshes and
canonical rebuilds.
