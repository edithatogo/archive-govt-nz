# Migration Baseline: `edithatogo/sm-govt-nz` → `edithatogo/archive-govt-nz`

## 1. Repository Lineage and Metadata

| Attribute | Donor Repository (`sm-govt-nz`) | Target Repository (`archive-govt-nz`) |
| :--- | :--- | :--- |
| **GitHub URI** | [`https://github.com/edithatogo/sm-govt-nz`](https://github.com/edithatogo/sm-govt-nz) | [`https://github.com/edithatogo/archive-govt-nz`](https://github.com/edithatogo/archive-govt-nz) |
| **Default Branch** | `master` | `main` |
| **Inspected Commit SHA** | `24df5f2dea7cfcd85fecaa1a18845339f987eeec` | `b1c09da305822f3e8f85f1c4e7a85eb803565ec2` |
| **Package Name** | `sm-govt-nz` (v0.1.0) | `archive-govt-nz` (v0.1.0) |
| **CLI Identities** | `sm-govt-nz`, `nz-govt-social` | `archive-govt-nz` |
| **Python Target** | `>=3.14` | `>=3.14` |
| **Quality Framework** | Ruff + Pytest (fail_under: 60%) | 18 automated gates, basedpyright strict, >95% branch coverage |
| **CAS / Preservation** | File-path based (`historical_archive_raw`, `historical_archive_normalized`) | Content-addressed storage (SHA-256 CAS, ISO 28500 WARC, BagIt, RO-Crate) |
| **Hugging Face Publication** | `edithatogo/corpus-social-media-government-nz` | `edithatogo/archive-govt-nz-global`, `edithatogo/archive-govt-nz-treasury`, `edithatogo/archive-govt-nz-health` |
| **Zenodo Publication** | Concept Record `20991132` (DOI `10.5281/zenodo.20991132`) | Concept Record `16872591` (DOI `10.5281/zenodo.16872591`) |
| **OSF Publication** | Target configured via `OSF_UPLOAD_URL` | Integration planned via RIOPA storage connector |

## 2. Secrets and Environment Variables (Names Only)

### Donor (`sm-govt-nz`)
- `HF_TOKEN`
- `ZENODO_TOKEN`
- `ZENODO_PUBLISH`
- `ZENODO_CONCEPT_RECORD_ID`
- `OSF_TOKEN`
- `OSF_UPLOAD_URL`
- `BLUESKY_HANDLE`
- `BLUESKY_APP_PASSWORD`
- `META_APP_ID`
- `META_APP_SECRET`
- `X_BEARER_TOKEN`
- `BUFFER_ACCESS_TOKEN`
- `CLOUDFLARE_API_TOKEN`

### Target (`archive-govt-nz`)
- `HF_TOKEN`
- `ZENODO_TOKEN`
- `HARVEST_WEBHOOK_URL`

## 3. Donor Scheduled Workflows Inventory (66 Workflows)

1. **Publication & Release Cadence**:
   - `publish_archives.yml` (Monthly snapshot on 1st at 16:41 UTC)
   - `publish_zenodo_deposition.yml`
   - `publish_retrospective_monthly_archive.yml`
2. **Social Media & Feed Ingestion**:
   - `archive_bluesky_scheduled.yml`, `archive_bluesky_sources.yml`
   - `archive_threads_scheduled.yml`, `archive_threads_manual_seeds.yml`
   - `archive_x_feed_scheduled.yml`, `x_launch.yml`
   - `archive_youtube_scheduled.yml`
   - `archive_rss_scheduled.yml`, `archive_json_feed_scheduled.yml`
   - `archive_email.yml`, `archive_newsletter_payloads.yml`
   - `archive_website_scheduled.yml`, `archive_website_browser_fallback.yml`
3. **Triangulation & Redundancy**:
   - `triangulate_wayback.yml`
   - `triangulate_common_crawl.yml`
4. **Mirroring & Backlog Health**:
   - `bluesky_mirror_ongoing.yml`, `bluesky_mirror_historical_backfill.yml`, `bluesky_mirror_health.yml`
   - `archive_health_monitor.yml`, `archive_compaction.yml`, `archive_completion_loop.yml`

## 4. Rollback and Freeze Baseline

Before any donor adapter migration occurs:
- The donor repository `edithatogo/sm-govt-nz` is tagged with `v0.1.0-pre-consolidation-baseline` at commit `24df5f2dea7cfcd85fecaa1a18845339f987eeec`.
- Read-only fixtures and historical raw captures are preserved in `evidence/migrations/sm-govt-nz/`.
- Both systems will operate concurrently in dual-run mode until Track 12.
