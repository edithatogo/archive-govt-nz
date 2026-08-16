# Track 6 Specification: Preservation, Replay and Recovery Assimilation

## Purpose
Converge archival preservation mechanics, byte-level WARC packaging, compaction, offline replay, and restore verification onto the unified target core.

## Context & Objectives
1. Implement ISO 28500 WARC and WACZ generation for all captured social-media posts, feeds, and web snapshots.
2. Ingest donor historical raw archives (`historical_archive_raw`, `historical_archive_normalized`) into streaming SHA-256 CAS.
3. Build automated snapshot compaction, deduplication, and offline deterministic replay verification.
4. Establish disaster recovery rehearsal automation.

## Deliverables
- `src/archive_govt_nz/preservation/warc.py`
- `src/archive_govt_nz/preservation/compaction.py`
- `src/archive_govt_nz/preservation/replay.py`
- `src/archive_govt_nz/preservation/recovery.py`
- Replay and restore verification tests
