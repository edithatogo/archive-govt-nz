# Evidence: NZ Gazette Archive Workflow

## Test Receipts
- Focused domain tests: `uv run pytest tests/domains/test_gazette_service.py -q`
  → 15 passed (validation, discovery, text extraction, service sync).
- Focused orchestrator tests: `uv run pytest tests/tools/test_run_gazette_harvest.py`
  → 12 passed, 99% statement coverage on `tools/run_gazette_harvest.py`
  (requirement: >=95% patch — met).
- Full gate `tools/check.py` (2026-08-22): **ALL 19 STAGES GREEN** —
  723 passed, total coverage 95.78%, pyright clean, all mutation suites
  passed, supply-chain stages passed.

## Deliverables
- `src/archive_govt_nz/domains/gazette/validate.py` — schema-consistent rules
  (identity, year bounds, fixity hash, URI scheme, timestamp chronology).
- `src/archive_govt_nz/domains/gazette/discovery.py` — typed targets, explicit
  seed inputs, fail-closed on missing notice IDs, discovery receipts.
- `src/archive_govt_nz/domains/gazette/service.py` — `GazetteArchiveService`
  with safe HTMLParser text extraction (no regex stripping) and CAS read-back.
- `tools/run_gazette_harvest.py` — orchestrator with `changed` / `no_change` /
  `partial_retryable` / `failed` taxonomy, checkpoint restore/promote, manifest
  and receipt emission.
- `tests/domains/test_gazette_service.py`, `tests/tools/test_run_gazette_harvest.py`.
- `.github/workflows/scheduled-gazette-harvest.yml` — weekly Thursday 04:00 UTC,
  pinned action SHAs, credential env wiring, artifact upload.

## Invariants
1. Discovery never fabricates notice IDs; seeds are explicit inputs.
2. Normalisation uses `html.parser.HTMLParser` (no regex stripping).
3. Checkpoint promotion only on `changed`/`no_change` outcomes.
4. Validation rejects future-dated retrieval timestamps (chronology policy).

## Infrastructure Audit (Phase 1)
- `src/archive_govt_nz/adapters/nz_gazette.py` — adapter present, transport contract
  reusable (success/429/fail/exception paths tested in
  `tests/capture/test_legislation_and_gazette_adapter.py`).
- `src/archive_govt_nz/domains/gazette/` — `models.py`, `identity.py`, `reconcile.py`
  present; no service, discovery, validation, or manifest layer prior to this track.
- `schemas/gazette/v1/gazette-record.schema.json` — canonical schema present.
- `config/source-sets/nz-gazette.yml` — enabled, weekly Thursday 04:00 UTC schedule.
- No scheduled gazette CI workflow existed prior to this track.