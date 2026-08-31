# Plan - Monthly Full Reconciliation

## Tasks
- [x] Define a monthly or quarterly full reconciliation cadence.
- [ ] Compare seed inventory, search discovery, and coverage report outputs.
- [ ] Add newly discovered work IDs to `seeds/work_ids.txt` with provenance.
- [ ] Rerun full sync in staged batches when the seed file changes materially.
- [ ] Review counts by legislation type, status, and year.

## Current blocker

- `docs/reconciliation_runbook.md` defines the monthly cadence and full reconciliation procedure.
- `seeds/work_ids.txt` now exists as the reviewed search-derived seed
  inventory from Track 04, so seed comparison can run against that operational
  baseline.
- `data/manifests/coverage_report.json` does not exist locally for a reviewed
  full corpus, so final coverage counts and deltas cannot be reviewed yet.
- Track 07 must complete a full bootstrap, and Track 08 must publish the
  reviewed full corpus, before monthly reconciliation can produce final
  live-maintenance evidence.
- `nzlc reconcile-work-ids` and `.github/workflows/historical_seed_reconciliation.yml`
  are available for candidate seed comparison before promotion.


## Implementation automation added 2026-06-12

- Added `.github/workflows/monthly_full_reconciliation.yml` for monthly and manual reconciliation.
- The workflow restores the live dataset, validates baseline coverage, discovers
  or ingests a candidate seed, reconciles it with `seeds/work_ids.txt`, and can
  optionally run a full sync to produce review artifacts after reconciliation.
- See `docs/full_corpus_operations.md` for the operator sequence and review
  artifacts for this workflow.
- Track is `ready` for the first manual reconciliation but remains unable to produce final coverage-delta evidence until Track 07/08 complete.

## Reconciliation publication guard hardened 2026-06-21

- `monthly_full_reconciliation.yml` now supplies safe defaults for scheduled
  runs where `workflow_dispatch` inputs are absent: baseline seed
  `seeds/work_ids.txt`, `max_works=none`, request pacing `1.0`, and minimum
  disk `25` GB.
- Confirmed publication now fails closed in this workflow. Monthly
  reconciliation can produce review artifacts and optionally run a full sync,
  but live Hugging Face publication must use Track 08
  `full_corpus_hf_upload.yml` after reviewing reconciliation outputs.
- Focused validation passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_monthly_full_reconciliation_workflow.py -q`
  reported 2 passed.
- Lint and workflow validation passed:
  `.venv\Scripts\python.exe -m ruff check --no-cache tests\test_monthly_full_reconciliation_workflow.py`
  and `actionlint .github\workflows\monthly_full_reconciliation.yml`.
- Broader adjacent workflow validation passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_monthly_full_reconciliation_workflow.py tests\test_hf_sync_workflow.py tests\test_full_corpus_hf_upload_workflow.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py -q`
  reported 27 passed, with Ruff and `actionlint` also passing across the
  monthly reconciliation, scheduled sync, and full upload workflow surfaces.

## Period-shard dependency added 2026-06-21

- Track 36 period manifests should become an input to monthly reconciliation
  once implemented.
- Reconciliation should compare coverage deltas by legislation type, status,
  year, and Track 36 period shard, with annual recent shards reviewed
  separately from coarse historical shards.
