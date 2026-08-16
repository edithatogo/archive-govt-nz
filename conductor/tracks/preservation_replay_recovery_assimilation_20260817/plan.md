# Track 6 Plan: Preservation, Replay and Recovery Assimilation

## Phases

### Phase 1: WARC / WACZ Engine Implementation
- [ ] Build ISO 28500 streaming WARC serializer with GZIP compression in `src/archive_govt_nz/preservation/warc.py`.
- [ ] Implement BagIt and RO-Crate metadata generators.

### Phase 2: Historical Archive Ingestion & Compaction
- [ ] Implement migration tool to ingest donor `historical_archive_raw` into CAS.
- [ ] Implement compaction and deduplication engine with SHA-256 fixity proofs.

### Phase 3: Replay & Disaster Recovery Automation
- [ ] Build offline deterministic replay runner.
- [ ] Implement and verify `tools/restore_from_publication.py` restore rehearsal.
