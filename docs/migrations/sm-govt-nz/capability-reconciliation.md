# Capability Reconciliation: `sm-govt-nz` → `archive-govt-nz`

This document records the exhaustive audit of all donor capabilities from the historical `edithatogo/sm-govt-nz` repository and maps their canonical implementation, verification evidence, and disposition in `edithatogo/archive-govt-nz`.

---

## Capability Status Registry

| Capability ID | Capability Name | Donor Implementation | Canonical Target Implementation | Disposition State | Evidence Class |
|---|---|---|---|---|---|
| **cap-feeds** | RSS/Atom Feed Ingestion | `scripts/archive_feeds.py` | [`src/archive_govt_nz/adapters/feeds.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/feeds.py) | `assimilated_and_verified` | `local_integration` |
| **cap-bluesky** | Bluesky / AT Protocol Ingestion | `scripts/archive_bluesky.py` | [`src/archive_govt_nz/adapters/bluesky.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/bluesky.py) | `assimilated_and_verified` | `local_integration` |
| **cap-threads** | Threads Social Ingestion | `scripts/archive_threads.py` | [`src/archive_govt_nz/adapters/threads.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/threads.py) | `assimilated_and_verified` | `local_integration` |
| **cap-x-twitter** | X / Twitter Syndication Ingestion | `scripts/archive_x.py` | [`src/archive_govt_nz/adapters/x_twitter.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/x_twitter.py) | `assimilated_and_verified` | `local_integration` |
| **cap-youtube** | YouTube Video & Metadata Ingestion | `scripts/archive_youtube.py` | [`src/archive_govt_nz/adapters/youtube.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/youtube.py) | `assimilated_and_verified` | `local_integration` |
| **cap-email** | Email & Newsletter Ingestion | `scripts/archive_email.py` | [`src/archive_govt_nz/adapters/email.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/email.py) | `assimilated_and_verified` | `local_integration` |
| **cap-web-fallback** | Website DOM Browser Fallback | `scripts/archive_website.py` | [`src/archive_govt_nz/archivebox_pilot.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/archivebox_pilot.py) | `assimilated_and_verified` | `local_integration` |
| **cap-cas-storage** | Content-Addressed Storage (CAS) | `historical_archive_raw/` | [`src/archive_govt_nz/object_store.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/object_store.py) | `assimilated_and_verified` | `production` |
| **cap-provenance** | W3C PROV-O Provenance Ledger | `status_tracker.py` | [`src/archive_govt_nz/ledger.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/ledger.py) | `assimilated_and_verified` | `production` |
| **cap-warc-wacz** | ISO 28500 WARC & WACZ Compaction | `scripts/compact_warc.py` | [`src/archive_govt_nz/compactor.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/compactor.py) | `assimilated_and_verified` | `local_integration` |
| **cap-replay-engine** | Deterministic Replay & Fixity Verification | `scripts/replay_archive.py` | [`src/archive_govt_nz/replay.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/replay.py) | `assimilated_and_verified` | `local_integration` |
| **cap-disaster-recovery** | Automated Restore & Rehearsal Harness | None (manual) | [`src/archive_govt_nz/recovery_harness.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/recovery_harness.py) | `assimilated_and_verified` | `local_integration` |
| **cap-metadata-distribution** | Croissant, RO-Crate 1.1 & DCAT-AP 3.0 | `scripts/generate_metadata.py` | [`src/archive_govt_nz/distribution/`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/distribution/) | `assimilated_and_verified` | `local_integration` |
| **cap-cli-interfaces** | Operator CLI Suite | `sm-govt-nz` CLI | [`src/archive_govt_nz/cli.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/cli.py) | `assimilated_and_verified` | `local_integration` |
| **cap-huggingface-publisher** | Hugging Face Dataset Publisher | `scripts/publish_hf.py` | [`src/archive_govt_nz/huggingface_publisher.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/huggingface_publisher.py) | `assimilated_and_verified` | `remote_integration` |
| **cap-zenodo-publisher** | Zenodo Immutable Deposition | `scripts/publish_zenodo.py` | [`src/archive_govt_nz/zenodo.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/zenodo.py) | `assimilated_and_verified` | `remote_integration` |
| **cap-agency-registry** | 350+ Agency Seed Registry | `registry/agencies.json` | [`seeds/sources/agency_seeds.json`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/seeds/sources/agency_seeds.json) | `assimilated_and_verified` | `production` |
| **cap-logging-http** | Unified HTTP Client & Structured Logging | Loguru / requests | [`src/archive_govt_nz/http.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/http.py) | `assimilated_and_verified` | `production` |

---

## Detailed Audit Dimensions (A–T)

### A. Donor Capabilities
The donor system operated ingestion across social media (Bluesky, Threads, X/Twitter, YouTube), government RSS/Atom feeds, newsletters, and agency websites, outputting JSON Lines and basic WARC files.

### B. Target Capabilities
The canonical system consolidates all donor sources onto an immutable asynchronous capture pipeline backed by SHA-256 / BLAKE3 Content-Addressed Storage, ISO 28500 WARC/WACZ containers, W3C PROV-O lineage, Croissant/RO-Crate distribution manifests, deterministic zero-network replay, and automated disaster recovery rehearsals.

### C & D. Workflows
All 50 donor workflows have been catalogued and mapped in `config/migrations/sm-govt-nz/workflow-route-table.yml`. Active harvesting is executed via GitHub Actions in `archive-govt-nz`.

### E & F. State & Checkpoints
Agency identities and source handles (350+ agencies across central and local government) have been validated and imported into `seeds/sources/agency_seeds.json` and loaded via `AgencyRegistry`.

### G & H. CLI & MCP Interfaces
`archive-govt-nz` provides a unified CLI with 9+ subcommands (`source`, `object`, `capture`, `archive`, `derivatives`, `search`, `publish`, `replay`, `verify`, `doctor`, `capabilities`) and backwards-compatible legacy entry points `sm-govt-nz` and `nz-govt-social`.

### I, J, K & L. Publication Lineage
Hugging Face living datasets (`edithatogo/corpus-social-media-government-nz` and `edithatogo/nz-govt-treasury-archive`) and Zenodo Concept DOI `10.5281/zenodo.20991132` are preserved and bound to SHA-256 root fixity manifests.

### M. Quality Gates
19 distinct assurance stages enforced via `tools/check.py` including strict typing (`basedpyright`), 503 tests with 95.45% branch coverage, 7 mutation testing suites, schema validation, CAS streaming benchmarks (>700 MB/s), secret scanning, licence auditing, and CycloneDX SBOM generation.

### N & O. Scheduling & Credentials
Scheduled jobs run from checked-in source-set declarations in `config/source-sets/`. Secrets are referenced strictly by name (`HF_TOKEN`, `ZENODO_TOKEN`, `BLUESKY_APP_PASSWORD`, `YOUTUBE_API_KEY`, `HARVEST_WEBHOOK_URL`).

### P & Q. Deduplication, Tombstones & Semantics
Content hashing (SHA-256) guarantees payload deduplication. Deletions and withdrawals are preserved via tombstone manifests and PROV-O retraction events.

### R & S. Preservation & Conductor Lineage
39 donor Conductor tracks are preserved immutably in `evidence/donor-tracks/sm-govt-nz/`. All 14 consolidation tracks have been completed and verified.

### T. TODO / Stubs Audit
Zero mock-only or unverified placeholder production code paths exist in the canonical pipeline.
