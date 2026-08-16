# Capability & Disposition Matrix

This matrix provides the comparative capability analysis between `sm-govt-nz` (donor) and `archive-govt-nz` (target).

## Disposition Legend

- `target_native_preferred`: Target implementation is superior in architecture, testing, or standards compliance.
- `donor_native_preferred`: Donor implementation has mature capabilities or domain coverage that will be transplanted into the target.
- `target_only`: Exclusive to `archive-govt-nz`.
- `donor_only`: Exclusive to `sm-govt-nz`; candidate for phased migration.
- `overlapping_needs_parity_test`: Implemented in both; requires differential fixture testing before cutover.
- `complementary`: Components merge naturally into a unified system.
- `defer`: Capability evaluated but deferred until demonstrated consumer demand.

---

## Detailed Capability Matrix

| Domain | Capability | Disposition | Donor (`sm-govt-nz`) | Target (`archive-govt-nz`) | Target Track | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Archive Core** | Content Addressed Storage (CAS) | `target_native_preferred` | Path-based flat files | Streaming SHA-256 CAS (`object_store.py`) | Track 6 | Target CAS achieves >400 MB/s streaming fixity and deduplication. |
| **Archive Core** | Evidence Ledger | `target_native_preferred` | `monthly_release_ledger.json` | JSON-LD Event Ledger (`ledger.py`) | Track 4 | Target provides auditable append-only cryptographic event chains. |
| **Archive Core** | Provenance Model | `target_native_preferred` | Ad-hoc run metadata | W3C PROV-O (`provenance.py`) | Track 4 | Formal ontology with agent, activity, and entity traceability. |
| **Archive Core** | Rights & Authority Engine | `target_native_preferred` | Static markdown checklists | Automated Policy Engine (`global_policy.py`) | Track 4 | Automatic license enforcement, quarantine, and redistribution gates. |
| **Archive Core** | NZ Govt Source Registry | `donor_native_preferred` | Curated `registry/` (350+ agencies) | Minimal CKAN scope | Track 4 | Donor registry is rich and comprehensive; transplant as core source registry. |
| **Capture** | Bluesky / AT Protocol | `overlapping_needs_parity_test` | `bluesky.py` & mirror programme | Planned `capture/social/bluesky.py` | Track 5 | Donor handles AT Protocol and media; port onto target CAS and provenance. |
| **Capture** | Threads (Meta Graph) | `overlapping_needs_parity_test` | `threads_pipeline.py` | Planned `capture/social/threads.py` | Track 5 | Assimilate Meta Graph API + Playwright browser fallback. |
| **Capture** | X / Twitter Ingestion | `overlapping_needs_parity_test` | Feed + operator capture | Planned `capture/social/x_twitter.py` | Track 5 | Assimilate feed parser and browser capture with ethical rate limits. |
| **Capture** | YouTube & Video | `donor_only` | Channel RSS & metadata script | Planned `capture/video/youtube.py` | Track 5 | Migrate YouTube RSS ingestion and transcript extraction into video adapter. |
| **Capture** | RSS / Atom & JSON Feeds | `overlapping_needs_parity_test` | `feed_ingestion.py` | Planned `capture/feeds/feed_harvester.py`| Track 5 | Integrate feed polling with target hash-based delta detection. |
| **Capture** | Email Newsletters | `donor_only` | Cloudflare Email Worker | Planned `capture/newsletters/email.py` | Track 5 | Ingest newsletter payloads into WARC and CAS storage. |
| **Capture** | Global CKAN Harvester | `target_only` | None | `global_discovery.py` & `tools/harvest_ckan.py`| Track 4 | Full CKAN Action API harvester with drift reconciliation. |
| **Capture** | Browser / Playwright | `complementary` | Headless scripts | `archivebox_pilot.py` container engine | Track 5 | Combine into unified headless capture service. |
| **Preservation**| WARC / WACZ Standards | `target_native_preferred` | None (flat JSON/HTML) | ISO 28500 WARC & BagIt (`warc.py`, `preservation.py`)| Track 6 | Standards-compliant archival containers with RO-Crate metadata. |
| **Preservation**| Wayback Triangulation | `target_native_preferred` | `triangulate_wayback.py` | Hypothesis-fuzzed CDX client (`wayback_triangulation.py`)| Track 6 | High-assurance retry-budgeted CDX triangulation. |
| **Derivatives** | Columnar Parquet | `target_only` | None | PyArrow / DuckDB (`analytical_derivatives.py`)| Track 7 | Ultra-fast analytical querying and dataset projections. |
| **Derivatives** | DCAT-AP Knowledge Graph| `target_only` | None | DCAT-AP 3.0 & BM25 Vector Search (`semantic_search.py`)| Track 7 | Standardized semantic ontology and hybrid search index. |
| **Publication** | Hugging Face Sync | `overlapping_needs_parity_test` | `corpus-social-media-government-nz`| `archive-govt-nz-global` publisher | Track 7 | Preserve existing dataset slug while using target verified sync engine. |
| **Publication** | Zenodo Releases | `overlapping_needs_parity_test` | Concept `20991132` | Concept `16872591` & Deposit Engine | Track 7 | Retain existing concept DOIs and publish dual-signed immutable deposits. |
| **Interfaces**  | CLI & Aliases | `complementary` | `sm-govt-nz`, `nz-govt-social` | `archive-govt-nz` CLI | Track 8 | Provide backwards-compatible CLI entry points. |
| **Interfaces**  | Webhook Alerting | `target_only` | None | Slack & Discord dispatcher (`notifications.py`)| Track 8 | Production status notifications. |
| **Interfaces**  | MCP Server | `defer` | None | None | Track 8 | No external consumer demand identified. Deferred. |

---

## Machine-Readable Reference
See [`capability-matrix.json`](./capability-matrix.json) for the JSON schema-validated version of this matrix.
