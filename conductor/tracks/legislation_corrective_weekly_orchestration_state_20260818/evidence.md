# Evidence: Weekly Orchestration, Resumable Archival Service, and State Management

## Executed Commands & Test Receipts

- `uv run pytest --cov=archive_govt_nz.domains.legislation.corpus --cov=archive_govt_nz.domains.legislation.checkpoints tests/domains/test_legislation_archive_service.py tests/domains/test_legislation_corpus_service.py tests/domains/test_legislation.py`: 17 passed in 25.86s, 97.81% coverage.
- `uv run python tools/validate_contracts.py`: All 15 YAML contracts validated.

## Invariants Verified

- **10-Step Synchronization**: Discovery → traversal → conditional acquisition → CAS storage → v2 normalisation → validation → manifest generation → coverage calculation → staged checkpoint → atomic promotion.
- **Idempotent Reruns**: Repeated sync without changes returns `status="no_change"` and performs 0 duplicate CAS writes.
- **Resumability**: Interrupted syncs resume from checkpoint `processed_work_ids`, skipping already preserved works.
- **Failure Guard**: Checkpoints are NOT promoted on `fail_fast` failures or 0 preserved records; staging files are discarded.
- **Corrupt Checkpoint Detection**: Unparseable JSON raises `LegislationCheckpointCorruptError` without overwriting data.
- **Zero Fabricated Timestamps**: Unused/initial checkpoint state has `last_updated: None`.
