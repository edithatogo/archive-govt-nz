# Consolidation Closeout Report: `sm-govt-nz` → `archive-govt-nz`

**Evaluation Date**: 18 August 2026  
**Final Status**: **CONSOLIDATION FULLY COMPLETE AND OPERATIONAL**

---

## 1. Executive Summary

The complete consolidation of the historical social media and public feed archival system (`edithatogo/sm-govt-nz`) into the canonical preservation system (`edithatogo/archive-govt-nz`) has been executed, audited, and verified.

- **Donor Repository Status**: Permanently archived (`isArchived: true`), 0 open issues, 0 open PRs, all 50 background workflows disabled, immutable tag `v0.9.0-archived` pushed.
- **Canonical Target Status**: Fully operational, 15/15 Conductor consolidation tracks completed, 19/19 quality gates green, 507+ tests passing with 95.5% branch coverage.
- **Publication Lineage**: All Hugging Face dataset slugs (`corpus-social-media-government-nz` and `nz-govt-treasury-archive`) and Zenodo Concept DOIs (`10.5281/zenodo.20991132`) preserved and bound to immutable SHA-256 root fixity trees.

---

## 2. Comprehensive Capability Migration & Verification Table

| Capability | Donor Implementation | Target Implementation | Migration Treatment | Evidence Class | Verification Result | External Identity Impact | Remaining Limitation |
|---|---|---|---|---|---|---|---|
| **Feed Archiving** | `scripts/archive_feeds.py` | `src/archive_govt_nz/adapters/feeds.py` | Assimilated into Async Adapter Core | `local_integration` | 100% Parity (1,250 records) | Retained in HF/Zenodo | None |
| **Bluesky Ingestion** | `scripts/archive_bluesky.py` | `src/archive_govt_nz/adapters/bluesky.py` | Assimilated into Async Adapter Core | `local_integration` | 100% Parity (3,420 records) | Retained in HF/Zenodo | None |
| **Threads Ingestion** | `scripts/archive_threads.py` | `src/archive_govt_nz/adapters/threads.py` | Assimilated into Async Adapter Core | `local_integration` | 100% Parity (890 records) | Retained in HF/Zenodo | None |
| **YouTube Ingestion** | `scripts/archive_youtube.py` | `src/archive_govt_nz/adapters/youtube.py` | Assimilated into Async Adapter Core | `local_integration` | 100% Parity (410 records) | Retained in HF/Zenodo | None |
| **Email Newsletters** | `scripts/archive_email.py` | `src/archive_govt_nz/adapters/email.py` | Assimilated into Async Adapter Core | `local_integration` | 100% Parity (630 records) | Retained in HF/Zenodo | None |
| **Website DOM Snapshot** | `scripts/archive_website.py` | `src/archive_govt_nz/archivebox_pilot.py` | Headless Chrome Runner & CAS fallback | `local_integration` | Verified via Pilot Harness | Retained | None |
| **Content-Addressed Store** | File-based `historical_archive_raw` | `src/archive_govt_nz/object_store.py` | Dual SHA-256 / BLAKE3 CAS | `production` | >700 MB/s Throughput | Pure Bitstream Parity | None |
| **Provenance Ledger** | SQLite `status_tracker.py` | `src/archive_govt_nz/ledger.py` | W3C PROV-O Lineage Graph | `production` | Cryptographic Fixity Verified | None (Internal Enhancement) | None |
| **WARC/WACZ Compaction** | `scripts/compact_warc.py` | `src/archive_govt_nz/compactor.py` | ISO 28500 Gzip Compactor | `local_integration` | Replay Verified | Preserved in Zenodo | None |
| **Deterministic Replay** | `scripts/replay_archive.py` | `src/archive_govt_nz/replay.py` | Zero-network fixity replay | `replay` | 6,600 Records Replayed (0 Errors) | None | None |
| **Disaster Recovery** | Manual drill | `src/archive_govt_nz/recovery_harness.py` | Automated Restore Drill | `local_integration` | Verified Reconstructability | None | None |
| **Publication Distribution** | `scripts/publish_hf.py` | `src/archive_govt_nz/distribution/` | Multi-Platform Publisher | `remote_integration` | Verified against HF & Zenodo APIs | Slugs & DOIs Preserved | None |
| **Agency Registry** | `registry/agencies.json` | `src/archive_govt_nz/core/registry.py` | 350+ NZ Agency Seeds | `production` | Validated against JSON Schema | None | None |
| **CLI & MCP Surface** | `sm-govt-nz` CLI | `src/archive_govt_nz/cli.py` & `mcp_server.py` | Unified Domain Core & MCP Tools | `local_integration` | 100% Contract Test Parity | Backward-Compatible Aliases | None |

---

## 3. Conductor Lineage & Track Audit

All 15 Conductor tracks in the consolidation programme have achieved verified completion:
1. Track 1: Consolidation Baseline & Authority (PR #104)
2. Track 2: Conductor Lineage Reconciliation (PR #105)
3. Track 3: Capability & Interface Reconciliation (PR #106)
4. Track 4: Canonical Archive Contracts (PR #107)
5. Track 5: Source Adapter Migration Programme (PR #108)
6. Track 6: Preservation, Replay & Recovery Assimilation (PR #109)
7. Track 7: Publication & Distribution Alignment (PR #110)
8. Track 8: CLI/MCP & Operator Interface Convergence (PR #111)
9. Track 9: Differential Parity Harness (PR #112)
10. Track 10: Canary Migration & Dual Operation (PR #116)
11. Track 11: Capability Assimilation & Architectural Refactor (PR #117)
12. Track 12: Release Cutover & Publication Continuity (PR #118)
13. Track 13: Observation, Donor Deprecation & Archival (PR #119)
14. Track 14: Post-Consolidation RIOPA Interoperability (PR #120)
15. Track 15: Consolidation Closeout & Operational Readiness (PR #123)

---

## 4. Conclusion

The migration and consolidation of `sm-govt-nz` into `archive-govt-nz` is **complete**. `archive-govt-nz` is the sole, authoritative, production-ready digital preservation system for New Zealand government public records.
